from argparse import ArgumentParser
from pathlib import Path

from openfoodfacts import API as off_api
from sqlalchemy import create_engine

from models.base import Base
from .api import FIELDS


# The country code used to restrict OpenFoodFacts results to that specific
# country.
OPENFOODFACTS_COUNTRY = "fr"

# The user agent used by the OpenFoodFacts REST API client.
OPENFOODFACTS_USER_AGENT = "OFFPRDC/0.1"


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


def format_data(data):
    """
    Generator used to format the collected data per the spreadsheet model.

    If a field is absent, the string "Unknown" is returned instead.
    """

    for field in FIELDS:
        if field in data:
            yield str(data[field])
        else:
            yield "Unknown"


def main():
    """
    Entry point of the OpenFoodFacts Data Collector command-line tool.
    """

    engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)

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
        # To take into account potential newlines when read from a text file.
        if code == "":
            data = []
        else:
            data = api_client.product.get(
                code,
                fields=FIELDS,
            )

            # If the product was not found.
            if data is None:
                data = []

        print(",".join(format_data(data)))
