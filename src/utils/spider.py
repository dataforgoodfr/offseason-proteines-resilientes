from abc import ABC, abstractmethod
from collections.abc import Generator

from scrapy import Field, Item
from scrapy.http import Response

from models.category import CategoryValues
from models.product import QuantityUnit

# The User-Agent HTTP header used by Scrapy for the crawling requests.
BOT_NAME = "proteines_resilientes"


class ProductItem(Item):
    # The name of the product.
    name = Field()

    # The brand of the product.
    brand = Field()

    # The normalised category of the product.
    category = Field()

    # The EAN-13 reference of the product.
    ean = Field()

    # The price of the product.
    price = Field()

    # Whether or not the price is discounted.
    discounted = Field()

    # The discounted price of the product.
    discounted_price = Field()

    # Quantity of food product.
    quantity = Field()

    # Quantity unit (either a weight or a volume).
    quantity_unit = Field()

    # The URL of the product.
    url = Field()


class ProductSpider(ABC):
    """
    Base class of any product spider.
    """

    @abstractmethod
    def parse_product(self, response: Response) -> Generator[ProductItem]:
        """
        Parses a product page.
        """

        pass

    @abstractmethod
    def is_relevant(self, response: Response) -> bool:
        """
        Filters out irrelevant products.
        """

        return True

    @abstractmethod
    def get_name(self, response: Response) -> str:
        """
        Extracts the product name from the response and returns it.
        """

        pass

    @abstractmethod
    def get_brand(self, response: Response) -> str:
        """
        Extracts the product brand from the response and returns it.
        """

        pass

    def get_category(self) -> CategoryValues:
        """
        Gets and returns the product category.
        """

        category: CategoryValues = getattr(self, "category", CategoryValues.UNKNOWN)

        return category

    @abstractmethod
    def get_ean13(self, response: Response) -> str | None:
        """
        Extracts and returns the product EAN-13.
        """

        pass

    @abstractmethod
    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

        pass
