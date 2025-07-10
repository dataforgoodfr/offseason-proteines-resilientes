from argparse import ArgumentParser
from logging import getLogger, Formatter, Logger, StreamHandler
from logging import DEBUG, INFO
from pathlib import Path

from openfoodfacts import API as off_api
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from .api import FIELDS
from models.base import Base
from models.product import NutriScore, NovaScore, Product
from models.reference import Reference, Type as RefType


# The country code used to restrict OpenFoodFacts results to that specific
# country.
OPENFOODFACTS_COUNTRY = "fr"

# The user agent used by the OpenFoodFacts REST API client.
OPENFOODFACTS_USER_AGENT = "OFFPRDC/0.1"

# The default SQLite database filename.
DEFAULT_SQLITE_FILENAME = "data.sqlite"


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(
        description="OpenFoodFacts Proteines Resilientes Data Collector"
    )

    ref_group = arg_parser.add_mutually_exclusive_group()

    ref_group.add_argument("references", nargs="*", help="Product references")
    ref_group.add_argument(
        "--ref-file",
        "-f",
        type=Path,
        help="Text file containing the product references, one by line",
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
    engine = create_engine("sqlite+pysqlite:///" + DEFAULT_SQLITE_FILENAME)
    Base.metadata.create_all(engine)

    references = None

    # Whether product references ("EAN") are passed by positional arguments or
    # via a text file.
    if args.ref_file is not None:
        logger.info(f"Reading references from '{args.ref_file}'")

        with open(args.ref_file, "r") as reader:
            references = reader.read().splitlines()
    else:
        logger.info("Reading references from CLI arguments")
        references = args.references

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

        logger.debug(f"Processing reference '{reference}'")

        with Session(engine) as session:
            ref_count = (
                session.query(func.count())
                .select_from(Reference)
                .filter(Reference.value == reference)
                .filter(Reference.type == RefType.EAN)
                .scalar()
            )

        if ref_count != 0:
            logger.debug(f"Reference ID {reference} already in database")
            continue

        data = api_client.product.get(
            reference,
            fields=FIELDS,
        )

        # If the product was not found.
        if data is None or data.get("product_name") is None:
            logger.debug(f"Reference not found: '{reference}'")
            continue

        logger.debug(f"Data received: {data}")

        # TODO: Refactor the Product instantiation.
        new_product = Product(
            name=data["product_name"],
            references=[Reference(type=RefType.EAN, value=reference)],
            nutriscore=NutriScore(data["nutrition_grade_fr"])
            if data.get("nutrition_grade_fr")
            and data["nutrition_grade_fr"] != "unknown"
            and data["nutrition_grade_fr"] != "not-applicable"
            else None,
            novascore=NovaScore(data["nova_group"]) if data.get("nova_group") else None,
            fat_100g=float(data["fat_100g"]) if data.get("fat_100g") else None,
            saturated_fat_100g=float(data["saturated-fat_100g"])
            if data.get("saturated-fat_100g")
            else None,
            carbohydrates_100g=float(data["carbohydrates_100g"])
            if data.get("carbohydrates_100g")
            else None,
            sugars_100g=float(data["sugars_100g"]) if data.get("sugars_100g") else None,
            fiber_100g=float(data["fiber_100g"]) if data.get("fiber_100g") else None,
            proteins_100g=float(data["proteins_100g"])
            if data.get("proteins_100g")
            else None,
            salt_100g=float(data["salt_100g"]) if data.get("salt_100g") else None,
        )

        with Session(engine) as session:
            session.add(new_product)
            session.commit()

    logger.info("Program ended")
