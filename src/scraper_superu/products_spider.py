import asyncio
import scrapy
from scrapy import Request, Spider
from urllib.parse import quote_plus
from typing import Dict, List
from bs4 import BeautifulSoup
import json

from .items import ProductItem
from .connector_nodriver import ConnectorNodriver


# Name of the cookie used to specify the "journey" ID.
#
# A journey ID is required to get the price on the product pages as it is tied
# to a physical store.
#
# See https://github.com/dataforgoodfr/offseason-proteines-resilientes/issues/2
# for more information.



class SuperUProductsSpider:
    """
    Scrapy Spider for the products of the SuperU retail website.
    """

    name = "superu_products"
    allowed_domains = ["www.coursesu.com"]
    start_urls = ["data:,"]
    custom_settings = {}
    connector: ConnectorNodriver = ConnectorNodriver()

    async def start(self, query: str, store_id: str):
        # query: str = getattr(self, "query", None)
        
        if query is None:
            raise AttributeError("Missing 'query' argument")
        
        url: str = f"https://www.coursesu.com/recherche?q={quote_plus(query).replace(' ', '+')}"
        await self.connector.get_page(url)
       

    def parse(self, response):
        # 'response' contains the page as seen by the browser
       pass