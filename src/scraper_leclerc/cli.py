from argparse import ArgumentParser
from logging import DEBUG, INFO, getLogger

from scrapy.crawler import CrawlerProcess

from models.category import CategoryValues
from utils.database import DEFAULT_DATABASE_URL
from utils.logger import set_up_root_logger
from utils.spider import BOT_NAME

from .products_spider import LeclercProductsSpider


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="Leclerc web scraper")

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
        help="Query to be used in Leclerc's search engine",
    )

    return arg_parser


def main() -> None:
    """
    Entry point of the scraper for Leclerc.
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
            "FEED_EXPORT_ENCODING": "utf-8",
            "DOWNLOAD_HANDLERS": {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            },
            "ITEM_PIPELINES": {
                "scraper_leclerc.pipeline_rdbms.ProductPipeline": 300,
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
            "COOKIES_ENABLED": True,
            "COOKIES_DEBUG": True,
        }
    )
    crawler.crawl(
        LeclercProductsSpider,
        **{
            "query": args.query,
            "category": args.category,
        },
    )
    crawler.start()

    logger.info("Program ended")
