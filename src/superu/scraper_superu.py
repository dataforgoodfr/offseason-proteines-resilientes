import sys
import os
import json
from src.abstract.isite_connector import ISiteConnector
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote_plus
from logging import getLogger, StreamHandler
from logging import INFO

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.append(root_path)


class SuperuScraper:
    def __init__(self, connector: ISiteConnector):
        self.connector = connector
        self.superu_logger = getLogger(__name__)
        self.superu_logger.setLevel(INFO)
        self.superu_logger.addHandler(StreamHandler())

    def get_pages(self, product: str, n_pages: int = 1) -> List[str]:
        url: str = f"https://www.coursesu.com/recherche?q={quote_plus(product).replace(' ', '+')}"
        if n_pages > 1:
            return [
                self.connector.get_page(f"{url}&page={page_number + 1}")
                for page_number in range(n_pages)
            ]
        else:
            return [self.connector.get_page(url)]

    def parse_data(self, html: str) -> List[Dict]:
        try:
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            products: List[Dict] = []

            # extraction of json data from data-tc-product-tile attribute
            tiles: List[BeautifulSoup] = soup.select("li[data-tc-product-tile]")
            for li in tiles:
                raw_data: str = li.get("data-tc-product-tile")
                if raw_data:
                    json_str: str = raw_data.replace("&quot;", '"')
                    data: Dict = json.loads(json_str)
                    products.append({
                        "ean": data.get("EAN"),
                        "name": data.get("name"),
                        "price": data.get("price"),
                        "brand": data.get("brand"),
                        "category1": data.get("product_cat1"),
                        "category2": data.get("product_cat2"),
                        "category3": data.get("product_cat3"),
                        "image": data.get("product_url_picture"),
                    })
            print(products)
            return products
        except json.JSONDecodeError:
            self.superu_logger.error("Erreur de parsing JSON:", raw_data)
        except Exception as e:
            self.superu_logger.error(f"Error parsing HTML: {e}")
            return []

    
        