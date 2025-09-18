import asyncio
import scrapy
from scrapy import Request, Spider
from urllib.parse import quote_plus
from typing import Dict

from .items import ProductItem
from playwright.async_api import async_playwright

# Name of the cookie used to specify the "journey" ID.
#
# A journey ID is required to get the price on the product pages as it is tied
# to a physical store.
#
# See https://github.com/dataforgoodfr/offseason-proteines-resilientes/issues/2
# for more information.
JOURNEY_COOKIE_NAME = "storeId"


class SuperUProductsSpider(Spider):
    """
    Scrapy Spider for the products of the SuperU retail website.
    """

    name = "superu_products"
    allowed_domains = ["www.coursesu.com"]
    start_urls = ["data:,"]
    custom_settings = {}
    

    def start(self):
        query: str = getattr(self, "query", None)
        
        if query is None:
            raise AttributeError("Missing 'query' argument")
        
        yield scrapy.Request("https://httpbin.org/get", meta={"playwright": True})
        # POST request
        yield scrapy.FormRequest(
            url="https://httpbin.org/post",
            formdata={"foo": "bar"},
            meta={"playwright": True},
        )

    def parse(self, response, **kwargs):
        # 'response' contains the page as seen by the browser
        return {"url": response.url}