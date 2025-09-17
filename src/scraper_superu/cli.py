from argparse import ArgumentParser
from logging import getLogger, Formatter, Logger, StreamHandler
from logging import DEBUG, INFO

from .products_spider import SuperUProductsSpider
from scrapy.crawler import CrawlerProcess

# The User-Agent HTTP header used by Scrapy for the crawling requests.
BOT_NAME = "proteines_resilientes"
# The default storeID sets the location to SuperU Drive La Riche
# (Tours).
DEFAULT_STORE_CP = "37005"


def __get_arg_parser() -> ArgumentParser:
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(description="SuperU web scraper")

    arg_parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable the debug mode",
    )

    arg_parser.add_argument(
        "--store_cp",
        default=DEFAULT_STORE_CP,
        help="The store ID to send as cookie",
    )

    arg_parser.add_argument(
        "query",
        help="Query to be used in SuperU's search engine",
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
     Entry point of the scraper for SuperU. 
     """ 
  
     args = __get_arg_parser().parse_args() 
  
     log_level = DEBUG if args.debug else INFO 
     __set_up_root_logger(level=log_level) 
  
     logger = getLogger(__name__) 
     logger.info("Program started") 
  
     crawler = CrawlerProcess( 
         settings={ 
             "AUTOTHROTTLE_ENABLED": True, 
             "BOT_NAME": BOT_NAME, 
             "FEED_EXPORT_ENCODING": "utf-8", 
             "ITEM_PIPELINES": { 
                 "scraper_superu.pipeline_rdbms.ProductPipeline": 300, 
             }, 
             "LOG_LEVEL": log_level, 
             "ROBOTSTXT_OBEY": False, 
             "TELNETCONSOLE_ENABLED": False, 
         } 
     ) 
     crawler.crawl( 
         SuperUProductsSpider, **{"query": args.query, "store_cp": args.store_cp} 
     ) 
     crawler.start() 
  
     logger.info("Program ended") 