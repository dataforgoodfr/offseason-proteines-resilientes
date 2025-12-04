from argparse import ArgumentParser
from logging import DEBUG, INFO, Formatter, Logger, StreamHandler, getLogger

from scrapy.crawler import CrawlerProcess

from models.category import CategoryValues
from utils.database import DEFAULT_DATABASE_URL

from .products_spider import BiocoopProductsSpider


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="Biocoop web scraper")

    arg_parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_URL,
        help=f"Database URL to use (defaults to {DEFAULT_DATABASE_URL})",
    )

    arg_parser.add_argument(
        "--category",
        required=True,
        type=CategoryValues,
        help="The category the scraped products should be assigned to",
    )

    arg_parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable the debug mode",
    )

    arg_parser.add_argument(
        "query",
        help="Query to be used in Biocoop's search engine",
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
    Entry point of the scraper for Biocoop.
    """

    args = __get_arg_parser().parse_args()

    log_level = DEBUG if args.debug else INFO
    __set_up_root_logger(level=log_level)

    logger = getLogger(__name__)
    logger.info("Program started")

    crawler = CrawlerProcess(
        settings={
            "AUTOTHROTTLE_ENABLED": True,
            "BOT_NAME": None,
            "DATABASE_URL": args.database,
            "FEED_EXPORT_ENCODING": "utf-8",
            "ITEM_PIPELINES": {
                "scraper_biocoop.pipeline_rdbms.ProductPipeline": 300,
            },
            "LOG_LEVEL": log_level,
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "ROBOTSTXT_OBEY": False,
            "TELNETCONSOLE_ENABLED": False,
        }
    )
    crawler.crawl(
        BiocoopProductsSpider,
        **{
            "query": args.query,
            "category": args.category,
        },
    )
    crawler.start()

    logger.info("Program ended")
