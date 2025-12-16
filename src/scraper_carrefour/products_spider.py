import json
import re
from collections.abc import Generator
from enum import StrEnum, unique
from functools import lru_cache

from scrapy import Request, Spider
from scrapy.http import Response

from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider

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

    CHARCUTERIE = "Charcuterie et Traiteur"
    EPICERIE = "Epicerie salée"
    FRUITS_LEGUMES = "Fruits et Légumes"
    OEUFS_PRODUITS_LAITIERS = "Crèmerie et Produits laitiers"
    SUCRE = "Epicerie sucrée"
    SURGELE = "Surgelés"
    VEGETAL = "Nutrition et Végétale"
    VIANDES_POISSONS = "Viandes et Poissons"

    @classmethod
    def _missing_(cls, value):
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


class CarrefourProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Carrefour retail website.
    """

    name = "carrefour_products"
    allowed_domains = ["www.carrefour.fr"]

    custom_settings = {}

    current_page = 0
    query: str
    url: str

    def __get_next_page(self) -> str:
        """
        Returns the next URL to visit while incrementing the current page index.
        """

        self.current_page += 1
        self.url = f"https://www.carrefour.fr/s?q={self.query}&page={self.current_page}"

        return self.url

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        self.query = query

        yield Request(
            url=self.__get_next_page(),
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
            callback=self.parse,
        )

    def parse(self, response: Response):
        product_links = response.xpath(
            "//li[@class='product-list-grid__item']/article/div/div/div/a[contains(@class, 'product-card-click-wrapper')]/@href"
        ).getall()
        yield from response.follow_all(
            product_links, meta={"playwright": True}, callback=self.parse_product
        )

        next_button = response.xpath(
            "//button[@aria-label='Afficher les produits suivants']"
        ).get()

        if next_button is not None:
            self.log("Next button detected")

            yield Request(
                url=self.__get_next_page(),
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse,
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

        base_price = float(
            response.css("script::text").re_first(r'"product_basePrice":([.0-9]+)')
        )
        current_price = float(
            response.css("script::text").re_first(r'"product_price":([.0-9]+)')
        )
        discounted = base_price - current_price > 0
        item["price"] = base_price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = current_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {item['ean']} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        self.log(f"Product cache info: {self.__get_product_info.cache_info()}")

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = [
            s.strip()
            for s in response.xpath(
                "//li[@class='c-breadcrumbs__breadcrumb']/a/text()"
            ).getall()
        ]

        if len(breadcrumbs) == 0:
            self.log("No breadcrumbs detected")
            return False

        self.log(f"Breadcrumbs on the page: {breadcrumbs}")

        try:
            main_department = breadcrumbs[1]
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

    def get_ean13(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["gtin13"]

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

        product_info = self.__get_product_info(response)
        raw_quantity = product_info["description"]

        m = re.match("(.+) ([.0-9]+) ?(ml|cl|L|kg|g)", raw_quantity, re.IGNORECASE)

        if m is None:
            return

        multiplier = m.group(1)  # les 2 plaquettes, la bouteille
        raw_quantity = m.group(2)  # 200, 1,5
        raw_quantity_unit = m.group(3)  # g, kg, L, l, cl

        quantity = float(raw_quantity.replace(",", "."))

        match raw_quantity_unit.lower():
            case "g":
                quantity = quantity / 1000
                quantity_unit = QuantityUnit.KILOGRAM
            case "l":
                quantity_unit = QuantityUnit.LITRE
            case "cl":
                quantity = quantity / 100
                quantity_unit = QuantityUnit.LITRE
            case "ml":
                quantity = quantity / 1000
                quantity_unit = QuantityUnit.LITRE
            case _:
                return

        is_coef = filter(str.isdigit, multiplier)

        if list(is_coef):
            nb = int("".join(filter(str.isdigit, multiplier)))
            return (quantity * nb, quantity_unit)
        else:
            return (quantity, quantity_unit)
