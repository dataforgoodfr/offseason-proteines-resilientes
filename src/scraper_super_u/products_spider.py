import json
from collections.abc import Generator
from enum import StrEnum, unique
from functools import lru_cache

from scrapy import Request, Spider
from scrapy.http import Response

from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider

# Name of the cookie used to specify the store ID.
STORE_COOKIE_NAME = "storeId"

# List of store department that are not relevant.
EXCLUSION_LIST = (
    "aides culinaires",
    "alcools",
    "boissons végétales",
    "bébé",
    "bouillon",
    "cuisinés",
    "glaces",
    "pizza",
    "préparés",
)


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    CHARCUTERIE = "Charcuterie, traiteur"
    EPICERIE = "Epicerie salée"
    FRAIS = "Marché frais"
    FRUITS_LEGUMES = "Fruits et Légumes"
    OEUFS_PRODUITS_LAITIERS = "Produits laitiers, oeufs et fromages"
    SUCRE = "Epicerie sucrée"
    SURGELES = "Surgelés"
    VIANDES = "Viandes, poissons"

    @classmethod
    def _missing_(cls, value: str) -> str | None:
        """
        Invoked when the value is not found in the enum. It is used here to
        accept values in a case-insensitive way.

        See https://docs.python.org/3/library/enum.html#enum.Enum._missing_.
        """

        value = value.upper()

        for member in cls:
            if member.value.upper() == value:
                return member

        return None


class SuperUProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Super U retail website.
    """

    name = "super_u_products"
    allowed_domains = ["www.coursesu.com"]

    custom_settings = {}

    current_page = 0
    query: str
    url: str

    def __get_next_page(self) -> str:
        """
        Returns the next URL to visit while incrementing the current page index.
        """

        self.current_page += 1
        self.url = f"https://www.coursesu.com/recherche?q={self.query}&page={self.current_page}"

        return self.url

    async def start(self):
        query = getattr(self, "query", None)
        store_id = getattr(self, "store_id", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")
        if store_id is None:
            raise AttributeError("Missing 'store_id' argument")

        self.query = query

        yield Request(
            url=self.__get_next_page(),
            cookies={STORE_COOKIE_NAME: store_id},
            meta={"impersonate": "chrome119"},
            callback=self.parse,
        )

    def parse(self, response: Response):
        product_links = response.css("a.product-tile-link")
        yield from response.follow_all(
            product_links,
            meta={"impersonate": "chrome119"},
            callback=self.parse_product,
        )

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        if not self.is_relevant(response):
            self.log("Product is irrelevant. Skipping...")
            return

        item["name"] = self.get_name(response)
        item["brand"] = self.get_brand(response)
        item["category"] = self.get_category()
        item["ean"] = self.get_ean13(response)
        item["url"] = response.url

        (discounted, price, discounted_price) = self.extract_discount_and_prices(
            response
        ) or (None, None, None)
        if price is not None:
            item["price"] = price
            item["discounted"] = discounted
            if discounted:
                item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {item['ean']} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        self.log(f"Product cache info: {self.__get_product_info.cache_info()}")

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = response.xpath(
            "//li[@class='breadcrumb-element']/a/span/text()"
        ).getall()

        if len(breadcrumbs) == 0:
            self.log("No breadcrumbs detected")
            return False

        self.log(f"Breadcrumbs on the page: {breadcrumbs}")

        try:
            main_department = breadcrumbs[0]
            main_department = Department(main_department)
        except ValueError:
            self.log(
                f"Main store department {main_department} is irrelevant. Skipping..."
            )
            return False

        any_exclusion = [
            s for excl in EXCLUSION_LIST for s in breadcrumbs if excl in s.lower()
        ]

        if any_exclusion:
            self.log(f"Hit excluded store departments: {any_exclusion}. Skipping...")
            return False

        return True

    @lru_cache(maxsize=8, typed=True)
    def __get_product_info(self, response: Response):
        """
        Extracts the product information from the response.

        The product information is cached.
        """

        microdata_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        product_data = [
            json.loads(data) for data in microdata_content if "Product" in data
        ]

        return product_data.pop()

    def get_name(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["name"]

    def get_brand(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["brand"]["name"]

    def get_ean13(self, response: Response) -> str | None:
        product_info = self.__get_product_info(response)

        return product_info["sku"]

    @staticmethod
    def extract_discount_and_prices(
        response: Response,
    ) -> tuple[bool, float, float | None] | None:
        """
        Extracts whether or not the product is discounted and its both prices
        (normal and discounted) from the response.

        Returns None if no price can be found.
        """

        current_product = response.css(".product-columns")

        current_price = current_product.xpath(
            ".//span[has-class('sale-price')]/@data-item-price"
        ).get()
        if current_price is None:
            return

        is_discounted = (
            current_product.xpath(".//span[has-class('discount')]").get() is not None
        )

        if is_discounted:
            base_price = current_product.xpath(
                ".//span[@class='pdp-standard-price-value']/text()"
            ).get()
            base_price = float(base_price.replace("€", "").replace(",", ".").strip())
            current_price = float(current_price)
            if current_price == base_price:
                is_discounted = False
        else:
            base_price = float(current_price)

        return (
            is_discounted,
            base_price,
            current_price if is_discounted else None,
        )

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        poids_net = response.xpath(
            '//p[@class="pdp-description-text"]/text()'
        ).re_first(r"Poids net: (.+)")

        if poids_net is None:
            return

        raw_quantity = poids_net.split()[0]
        quantity = float(raw_quantity.replace(",", "."))

        raw_quantity_unit = poids_net.split()[1]

        match raw_quantity_unit.lower():
            case "kg":
                quantity_unit = QuantityUnit.KILOGRAM
            case "g":
                quantity = quantity / 1000
                quantity_unit = QuantityUnit.KILOGRAM

        return (quantity, quantity_unit)
