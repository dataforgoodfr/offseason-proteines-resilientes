import sys
import os
import json
from bs4 import BeautifulSoup
from typing import List, Dict
from logging import getLogger, StreamHandler
from logging import INFO
from abstract.isite_connector import ISiteConnector

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.append(root_path)


class SuperuScraper:
    def __init__(self, connector: ISiteConnector):
        self.connector = connector
        self.superu_logger = getLogger(__name__)
        self.superu_logger.setLevel(INFO)
        self.superu_logger.addHandler(StreamHandler())

    def get_pages(self, url: str, n_pages: int = 1) -> List[str]:
        if n_pages > 1:
            return [
                self.connector.get_page(f"{url}?page={page_number + 1}")
                for page_number in range(n_pages)
            ]
        else:
            return [self.connector.get_page(url)]

    

    
        