from argparse import ArgumentParser
from logging import getLogger, Formatter, Logger, StreamHandler
from logging import DEBUG, INFO
from pathlib import Path
from superu_data_collector.scraper_superu import SuperuScraper
from superu_data_collector.connector_nodriver import ConnectorNodriver
from typing import List, Dict
import time

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

def __scrape_product(product: str) -> List[Dict]:
    """Scrapes product information from Carrefour.
    Args:
        product (str): The product to search for.
    Returns:
        list: A list of dictionaries containing product information.
    """
    
    # Select the correct scraper for the chosen distributor
    scrapper = SuperuScraper(ConnectorNodriver())
    page_htmls: List[str] = scrapper.get_pages(product, n_pages=1)
    data: List[Dict] = [data for page_html in page_htmls for data in scrapper.parse_data(page_html)]
    # Deduplicate
    data: List[Dict] = [dict(t) for t in {tuple(sorted(d.items())) for d in data}]
    return data

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
    for reference in references:
        data: List[Dict] = __scrape_product(reference)
        print(data)

    logger.info("Program ended")
