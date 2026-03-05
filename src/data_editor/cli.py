from argparse import ArgumentParser, Namespace
from logging import DEBUG, INFO, getLogger
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from models.base import Base
from models.product import Product
from utils.database import DEFAULT_DATABASE_URL
from utils.logger import set_up_root_logger


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    root_parser = ArgumentParser(description="Proteines Resilientes Data Editor")

    # ------------------------------ #
    # Global options
    # ------------------------------ #

    root_parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_URL,
        help=f"Database URL to use (defaults to {DEFAULT_DATABASE_URL})",
    )

    root_parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable the debug mode",
    )

    # ------------------------------ #
    # Shared options for
    # enable/disable subcommands
    # ------------------------------ #

    ref_options_parser = ArgumentParser(add_help=False)

    ref_group = ref_options_parser.add_mutually_exclusive_group()

    ref_group.add_argument("references", nargs="*", help="Product references (EAN-13)")
    ref_group.add_argument(
        "--ref-file",
        "-f",
        type=Path,
        help="Text file containing the product references (EAN-13), one by line",
    )

    # Subparser for the subcommands.
    subparsers = root_parser.add_subparsers(
        title="Commands",
        required=True,
        dest="command",
    )

    # ------------------------------ #
    # Command 'enable'
    # ------------------------------ #

    enable_subparser = subparsers.add_parser(
        "enable",
        parents=[ref_options_parser],
        help="Enable a product",
    )
    enable_subparser.set_defaults(func=__toggle_product_status)

    # ------------------------------ #
    # Command 'disable'
    # ------------------------------ #

    disable_subparser = subparsers.add_parser(
        "disable",
        parents=[ref_options_parser],
        help="Disable a product",
    )
    disable_subparser.set_defaults(func=__toggle_product_status)

    return root_parser


def __toggle_product_status(
    args: Namespace, engine: Engine, references: tuple[str]
) -> None:
    """
    Toggles the activation status of a product.
    """

    logger = getLogger(__name__)
    logger.info(f"Processing {len(references)} references")

    updated = 0
    unchanged = 0
    not_found = 0

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
                logger.debug(f"Product {reference} not found in database")
                not_found += 1

            else:
                product: Product = products.one()

                if product.disabled and args.command == "enable":
                    product.disabled = False
                    updated += 1
                    session.commit()
                elif not product.disabled and args.command == "disable":
                    product.disabled = True
                    updated += 1
                    session.commit()
                else:
                    unchanged += 1

    logger.info(f"Updated: {updated} / Unchanged: {unchanged} / Not found: {not_found}")


def __get_references(args: Namespace) -> tuple[str]:
    logger = getLogger(__name__)

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

    return tuple(references)


def main() -> None:
    """
    Entry point of the Disable-Enable Product Database command-line tool.
    """

    args = __get_arg_parser().parse_args()

    log_level = DEBUG if args.debug else INFO
    set_up_root_logger(level=log_level)

    logger = getLogger(__name__)
    logger.info("Program started")

    logger.debug("Setting up the database")
    engine = create_engine(args.database)
    Base.metadata.create_all(engine)

    references = __get_references(args)

    args.func(args, engine, references)

    logger.info("Program ended")
