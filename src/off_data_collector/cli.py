from argparse import ArgumentParser
from pathlib import Path

from openfoodfacts import API as off_api
from sqlalchemy import create_engine
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


def get_arg_parser():
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(
        prog="OpenFoodFacts Proteines Resilientes Data Collector"
    )
    arg_parser.add_argument("codes", nargs="*", default=[])
    arg_parser.add_argument("--codefile", "-f", nargs="?", type=Path)

    return arg_parser


def main():
    """
    Entry point of the OpenFoodFacts Data Collector command-line tool.
    """

    # Create a new ORM engine.
    engine = create_engine("sqlite+pysqlite:///" + DEFAULT_SQLITE_FILENAME)
    Base.metadata.create_all(engine)

    # Parse arguments.
    args = get_arg_parser().parse_args()

    codes = None

    # Whether product references ("EAN") are passed by positional arguments or
    # via a text file.
    if args.codefile is not None:
        with open(args.codefile, "r") as reader:
            codes = reader.read().splitlines()
    else:
        codes = args.codes

    # Set up OpenFoodFacts REST API client.
    api_client = off_api(
        user_agent=OPENFOODFACTS_USER_AGENT, country=OPENFOODFACTS_COUNTRY
    )

    for code in codes:
        # To take into account potential newlines or comments when read from a
        # text file.
        if code == "" or code.startswith("#"):
            continue
        else:
            data = api_client.product.get(
                code,
                fields=FIELDS,
            )

            # If the product was not found.
            if data is None:
                # TODO: add log
                continue

            new_product = Product(
                name=data["product_name"],
                references=[Reference(type=RefType.EAN, value=code)],
                nutriscore=NutriScore(data["nutrition_grade_fr"]),
                novascore=NovaScore(data["nova_group"]),
                fat_100g=float(data["fat_100g"]),
                saturated_fat_100g=float(data["saturated-fat_100g"]),
                carbohydrates_100g=float(data["carbohydrates_100g"]),
                sugars_100g=float(data["sugars_100g"]),
                fiber_100g=float(data["fiber_100g"]),
                proteins_100g=float(data["proteins_100g"]),
                salt_100g=float(data["salt_100g"]),
            )

            with Session(engine) as session:
                session.add(new_product)
                session.commit()
