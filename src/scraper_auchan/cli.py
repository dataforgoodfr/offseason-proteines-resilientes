from argparse import ArgumentParser
from logging import getLogger, Formatter, Logger, StreamHandler
from logging import DEBUG, INFO


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="Auchan web scraper")

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
    Entry point of the scraper for Auchan.
    """

    args = __get_arg_parser().parse_args()

    log_level = DEBUG if args.debug else INFO
    __set_up_root_logger(level=log_level)

    logger = getLogger(__name__)
    logger.info("Program started")

    logger.info("Program ended")
