from argparse import ArgumentParser
from logging import getLogger, Formatter, Logger, StreamHandler
from logging import DEBUG, INFO
from pathlib import Path

from openfoodfacts import API as off_api
from openfoodfacts.types import JSONType
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .api import FIELDS
from models.base import Base
from models.nutrition_facts import NutritionFacts, NutriScore, NovaScore
from models.product import Product
from models.source import Source
from utils.database import DEFAULT_DATABASE_URL


# The country code used to restrict OpenFoodFacts results to that specific
# country.
OPENFOODFACTS_COUNTRY = "fr"

# The user agent used by the OpenFoodFacts REST API client.
OPENFOODFACTS_USER_AGENT = "OFFPRDC/0.1"


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(
        description="Proteines Resilientes OpenFoodFacts Data Collector"
    )

    ref_group = arg_parser.add_mutually_exclusive_group()

    ref_group.add_argument("references", nargs="*", help="Product references (EAN-13)")
    ref_group.add_argument(
        "--ref-file",
        "-f",
        type=Path,
        help="Text file containing the product references (EAN-13), one by line",
    )

    arg_parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_URL,
        help=f"Database URL to use (defaults to {DEFAULT_DATABASE_URL})",
    )

    arg_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Product data will be updated even if the product already exists in the database",
    )

    arg_parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Update all products, including those already in the database",
    )

    arg_parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable the debug mode",
    )

    return arg_parser


def __set_up_root_logger(level=INFO) -> Logger:
    """
    Sets up the root logger.
    """

    root_logger = getLogger("")
    root_logger.setLevel(level)

    console = StreamHandler()

    console_formatter = Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    console.setFormatter(console_formatter)

    root_logger.addHandler(console)

    return root_logger


def main() -> None:
    """
    Entry point of the OpenFoodFacts Data Collector command-line tool.
    """

    args = __get_arg_parser().parse_args()

    log_level = DEBUG if args.debug else INFO
    __set_up_root_logger(level=log_level)

    logger = getLogger(__name__)
    logger.info("Program started")

    logger.debug("Setting up the database")
    engine = create_engine(args.database)
    Base.metadata.create_all(engine)

    references = []

    # Whether product references ("EAN") are passed by positional arguments or
    # via a text file.
    if args.ref_file is not None:
        logger.info(f"Reading references from '{args.ref_file}'")

        with open(args.ref_file, "r") as reader:
            references += reader.read().splitlines()
    else:
        logger.info("Reading references from CLI arguments")
        references += args.references

    # If the products already in the database also need to be updated.
    if args.all:
        logger.info("Reading references from database")

        with Session(engine) as session:
            references += session.execute(select(Product.ean_13)).scalars().all()

    logger.info(f"Processing {len(references)} references")

    logger.debug("Setting up OpenFoodFacts REST API client")
    api_client = off_api(
        user_agent=OPENFOODFACTS_USER_AGENT, country=OPENFOODFACTS_COUNTRY
    )

    for reference in references:
        # To take into account potential newlines or comments when read from a
        # text file.
        if reference == "" or reference.startswith("#"):
            continue

        logger.debug(f"Processing reference ID '{reference}'")

        with Session(engine) as session:
            products = session.query(Product).filter(Product.ean_13 == reference)

            # If the product does not already exist in the database.
            if products.count() == 0:
                data = __fetch_product_data(api_client, reference)

                if data is None:
                    continue

                new_product = __create_new_product(reference, data)

                session.add(new_product)
                session.commit()
            else:
                logger.debug(f"Reference ID {reference} already in database")

                # If the user has not explicitly asked to update the products that
                # are already present in the database.
                if not args.force:
                    logger.debug(f"Skipping product with reference ID '{reference}'")
                    continue

                product = products.one()

                if product.disabled:
                    logger.debug(f"Product with reference ID '{reference}' is disabled")
                    continue

                data = __fetch_product_data(api_client, reference)

                if data is None:
                    continue

                __update_product(product, reference, data)

                session.commit()

    logger.info("Program ended")


def __fetch_product_data(
    api_client: off_api, reference: str, data_fields: list[str] = FIELDS
) -> JSONType | None:
    """
    Fetches the product data from OpenFoodFacts for a given reference (EAN-13).
    """

    logger = getLogger(__name__)

    data = api_client.product.get(
        reference,
        fields=data_fields,
    )

    # If the product was not found.
    if data is None or data.get("product_name") is None:
        logger.debug(f"Reference not found: '{reference}'")
        return None

    logger.debug(f"Data received: {data}")
    return data


def __create_new_product(reference: str, data: JSONType) -> Product:
    """
    Returns a new Product object based on the data fetched from OpenFoodFacts.
    """

    return Product(
        ean_13=reference,
        name=data["product_name"],
        brand=data["brands"] if data.get("brands") else None,
        sources=[__create_new_source(reference, data)],
    )


def __update_product(product: Product, reference: str, data: JSONType) -> None:
    """
    Updates a product stored in the database by adding the product data fetched
    from OpenFoodFacts as new source.
    """

    product.sources.append(__create_new_source(reference, data))


def __create_new_source(reference: str, data: JSONType) -> Source:
    """
    Returns a new Source object based on the reference ID and the data fetched
    from OpenFoodFacts given as parameters.
    """

    return Source(
        url=f"https://world.openfoodfacts.org/product/{reference}/",
        nutrition_facts=NutritionFacts(
            nutriscore=NutriScore(data["nutrition_grade_fr"])
            if data.get("nutrition_grade_fr")
            and data["nutrition_grade_fr"] != "unknown"
            and data["nutrition_grade_fr"] != "not-applicable"
            else None,
            novascore=NovaScore(data["nova_group"]) if data.get("nova_group") else None,
            calories_100g=float(data["energy-kcal_100g"])
            if data.get("energy-kcal_100g")
            else None,
            fat_100g=float(data["fat_100g"]) if data.get("fat_100g") else None,
            saturated_fat_100g=float(data["saturated-fat_100g"])
            if data.get("saturated-fat_100g")
            else None,
            carbohydrates_100g=float(data["carbohydrates_100g"])
            if data.get("carbohydrates_100g")
            else None,
            sugars_100g=float(data["sugars_100g"]) if data.get("sugars_100g") else None,
            fiber_100g=float(data["fiber_100g"]) if data.get("fiber_100g") else None,
            protein_100g=float(data["proteins_100g"])
            if data.get("proteins_100g")
            else None,
            salt_100g=float(data["salt_100g"]) if data.get("salt_100g") else None,
        ),
    )
