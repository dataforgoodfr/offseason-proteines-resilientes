from argparse import ArgumentParser
from logging import DEBUG, INFO, getLogger

from scrapy.crawler import CrawlerProcess

from models.category import CategoryValues
from utils.database import DEFAULT_DATABASE_URL
from utils.logger import set_up_root_logger
from utils.spider import BOT_NAME

from .products_spider import SuperUProductsSpider

# The default store ID sets the location to Joué-lès-Tours.
DEFAULT_STORE_ID = "36726"


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="Super U web scraper")

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
        "--store-id",
        default=DEFAULT_STORE_ID,
        help="The store ID to send as cookie",
    )

    arg_parser.add_argument(
        "query",
        help="Query to be used in Super U's search engine",
    )

    return arg_parser


def main() -> None:
    """
    Entry point of the scraper for Super U.
    """

    args = __get_arg_parser().parse_args()

    log_level = DEBUG if args.debug else INFO
    set_up_root_logger(level=log_level)

    logger = getLogger(__name__)
    logger.info("Program started")

    crawler = CrawlerProcess(
        settings={
            "BOT_NAME": BOT_NAME,
            "DATABASE_URL": args.database,
            "DOWNLOAD_HANDLERS": {
                "http": "scrapy_impersonate.ImpersonateDownloadHandler",
                "https": "scrapy_impersonate.ImpersonateDownloadHandler",
            },
            "FEED_EXPORT_ENCODING": "utf-8",
            "ITEM_PIPELINES": {
                "scraper_super_u.pipeline_rdbms.ProductPipeline": 300,
            },
            "LOG_LEVEL": log_level,
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            "USER_AGENT": None,
            "COOKIES_ENABLED": True,
            "COOKIES_DEBUG": True,
        }
    )
    crawler.crawl(
        SuperUProductsSpider,
        **{
            "query": args.query,
            "category": args.category,
            "store_id": args.store_id,
        },
    )
    crawler.start()

    logger.info("Program ended")
