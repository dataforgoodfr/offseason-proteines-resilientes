from argparse import ArgumentParser
from logging import DEBUG, INFO, getLogger

from scrapy.crawler import CrawlerProcess

from models.category import CategoryValues
from utils.database import DEFAULT_DATABASE_URL
from utils.logger import set_up_root_logger
from utils.spider import BOT_NAME

from .products_spider import AuchanProductsSpider

# The default journey ID sets the location to Auchan Drive Saint-Cyr-Sur-Loire
# (Tours).
DEFAULT_JOURNEY_ID = "9ca9e4a5-0d62-4a94-9f92-c7c88e374a7f"


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="Auchan web scraper")

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
        "--journey-id",
        default=DEFAULT_JOURNEY_ID,
        help="The journey ID to send as cookie",
    )

    arg_parser.add_argument(
        "query",
        help="Query to be used in Auchan's search engine",
    )

    return arg_parser


def main() -> None:
    """
    Entry point of the scraper for Auchan.
    """

    args = __get_arg_parser().parse_args()

    log_level = DEBUG if args.debug else INFO
    set_up_root_logger(level=log_level)

    logger = getLogger(__name__)
    logger.info("Program started")

    crawler = CrawlerProcess(
        settings={
            "AUTOTHROTTLE_ENABLED": True,
            "BOT_NAME": BOT_NAME,
            "DATABASE_URL": args.database,
            "FEED_EXPORT_ENCODING": "utf-8",
            "ITEM_PIPELINES": {
                "scraper_auchan.pipeline_rdbms.ProductPipeline": 300,
            },
            "LOG_LEVEL": log_level,
            "ROBOTSTXT_OBEY": False,
            "TELNETCONSOLE_ENABLED": False,
        }
    )
    crawler.crawl(
        AuchanProductsSpider,
        **{
            "query": args.query,
            "category": args.category,
            "journey_id": args.journey_id,
        },
    )
    crawler.start()

    logger.info("Program ended")
