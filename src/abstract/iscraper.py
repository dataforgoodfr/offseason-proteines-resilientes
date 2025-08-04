
from typing import List, Dict
from abc import ABC, abstractmethod


class Iscraper(ABC):
    """Interface for a scraper.
    A scraper is a class that fetches the HTML content of a page and parses the data.
    """
   
    @abstractmethod
    def get_pages(self, base_url: str, n_pages: int = 3) -> List[str]:
        """Fetches the HTML content of multiples Carrefour pages using Playwright.
        Args:
            url (str): The base URL of the page to fetch.
        Returns:
            List[str]: A list of HTML content strings for each page.
        """
        raise NotImplementedError

    
    @abstractmethod
    def parse_data(self, content: str) -> List[Dict]:
        """Parse the product information from the html of the Carrefour webpage.
        Args:
            html (str): The HTML content of the Carrefour page.
        Returns:
            List[Dict]: A list of dictionaries containing product information.
        """
        raise NotImplementedError
