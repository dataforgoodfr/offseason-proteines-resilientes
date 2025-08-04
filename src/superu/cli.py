from argparse import ArgumentParser
from logging import getLogger, Formatter, Logger, StreamHandler
from logging import DEBUG, INFO
from pathlib import Path

def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(
        description="SuperU Proteines Resilientes Data Collector"
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
    
    # Whether product name are passed by positional arguments or
    # via a text file.
    if args.ref_file is not None:
        logger.info(f"Reading references from '{args.ref_file}'")

        with open(args.ref_file, "r") as reader:
            references = reader.read().splitlines()
    else:
        logger.info("Reading references from CLI arguments")
        references = args.references

    logger.info(f"Processing {len(references)} references")

    logger.debug("Setting up SuperU scraper for product")
    


    logger.info("Program ended")
