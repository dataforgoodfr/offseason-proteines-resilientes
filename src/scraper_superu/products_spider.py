from urllib.parse import quote_plus
from typing import Dict, List
from bs4 import BeautifulSoup
import json

from .items import ProductItem
from .connector_nodriver import ConnectorNodriver
from logging import getLogger
logger = getLogger(__name__)

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

    async def start(self, query: str):
        # query: str = getattr(self, "query", None)
        
        if query is None:
            raise AttributeError("Missing 'query' argument")
        
        
        url: str = f"https://www.coursesu.com/recherche?q={quote_plus(query).replace(' ', '+')}"
        response = await self.connector.get_page(url)
        products = self.parse(response, url)
        self.__load_products(products)

    def parse(self, response:str, url:str):
        # 'response' contains the page as seen by the browser
        try:
            soup: BeautifulSoup = BeautifulSoup(response, "html.parser")
            products: List[Dict] = []

            # extraction of json data from data-tc-product-tile attribute
            tiles: List[BeautifulSoup] = soup.select("li[data-tc-product-tile]")
        
            for li in tiles:
                raw_data: str = li.get("data-tc-product-tile")
                if raw_data:
                    item = ProductItem()
                    json_str: str = raw_data.replace("&quot;", '"')
                    data: Dict = json.loads(json_str)
                    item["name"] = data.get("name")
                    item["brand"] = data.get("brand")
                    item["eans"] = data.get("EAN")    
                    item["price"] = data.get("price")
                    item["url"] = url
                    products.append(item)
            return products
        except json.JSONDecodeError:
            logger.error("Erreur de parsing JSON:", raw_data)
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def __load_products(self, products: List[Dict]):
        print(products)
        # product_pipeline = ProductPipeline()
        # product_pipeline.open_spider(None)
        # product_pipeline.process_item(products, None)
        # product_pipeline.close_spider(None)