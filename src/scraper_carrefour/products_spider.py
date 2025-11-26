import json
import re
from logging import DEBUG

from scrapy import Request, Spider

from models.product import QuantityUnit

from .items import ProductItem


class CarrefourProductsSpider(Spider):
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

    def parse(self, response):
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

    def parse_product(self, response):
        item = ProductItem()

        microdata_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        product_data = [
            json.loads(data) for data in microdata_content if "Product" in data
        ].pop()

        item["name"] = product_data["name"]
        item["brand"] = product_data["brand"]["name"]
        item["ean"] = product_data["gtin13"]
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

        quantity, quantity_unit = self.extract_quantity(
            product_data["description"]
        ) or (None, None)

        if quantity is None:
            self.log(f"Product {item['ean']} has no quantity. Skipping...", DEBUG)
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    @staticmethod
    def extract_quantity(raw_quantity) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

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
