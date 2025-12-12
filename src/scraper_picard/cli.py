from argparse import ArgumentParser
from logging import DEBUG, INFO, getLogger

from scrapy.crawler import CrawlerProcess

from models.category import CategoryValues
from utils.database import DEFAULT_DATABASE_URL
from utils.logger import set_up_root_logger
from utils.spider import BOT_NAME

from .products_spider import PicardProductsSpider


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="Picard web scraper")

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
        help="Query to be used in Picard's search engine",
    )

    return arg_parser


def main() -> None:
    """
    Entry point of the scraper for Picard.
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
            "DOWNLOAD_HANDLERS": {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            },
            "FEED_EXPORT_ENCODING": "utf-8",
            "ITEM_PIPELINES": {
                "scraper_picard.pipeline_rdbms.ProductPipeline": 300,
            },
            "LOG_LEVEL": log_level,
            "PLAYWRIGHT_BROWSER_TYPE": "chromium",
            "PLAYWRIGHT_LAUNCH_OPTIONS": {
                "headless": False,
            },
            "ROBOTSTXT_OBEY": False,
            "TELNETCONSOLE_ENABLED": False,
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        }
    )
    crawler.crawl(
        PicardProductsSpider,
        **{
            "query": args.query,
            "category": args.category,
        },
    )
    crawler.start()

    logger.info("Program ended")
