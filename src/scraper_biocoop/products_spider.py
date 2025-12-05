import re
from collections.abc import Generator
from logging import DEBUG

from scrapy import Request, Spider
from scrapy.http import Response

from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider


class BiocoopProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Biocoop retail website.
    """

    name = "biocoop_products"
    allowed_domains = ["www.biocoop.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        url = f"https://www.biocoop.fr/magasin-biocoop_biocite/catalogsearch/result/?q={query}&p=1"

        yield Request(url=url, callback=self.parse)

    def parse(self, response: Response):
        product_links = response.xpath(
            "//div[@class='product-item-info']/a/@href"
        ).getall()
        yield from response.follow_all(product_links, callback=self.parse_product)

        next_page_url = response.css("a.next-page ::attr(data-href)").get()

        if next_page_url is not None:
            self.log(f"Next button detected: {next_page_url}")

            yield response.follow(next_page_url, callback=self.parse)

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        ean = self.get_ean13(response)

        if ean is None:
            self.log("No EAN-13 found. Skipping...", DEBUG)
            return

        item["ean"] = ean
        item["name"] = self.get_name(response)
        item["brand"] = self.get_brand(response)
        item["category"] = self.get_category()
        item["url"] = response.url

        discounted, base_price, discounted_price = self.extract_discount_and_prices(
            response
        )
        item["price"] = base_price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {ean} has no quantity. Skipping...", DEBUG)
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    def get_name(self, response: Response) -> str:
        name = response.xpath("//span[@itemprop='name']/text()").get()

        return name

    def get_brand(self, response: Response) -> str:
        brand = response.xpath("//span[@class='brand value']/text()").get()

        return brand

    def get_ean13(self, response: Response) -> str | None:
        ean: str = (
            response.xpath("//meta[@itemprop='image']/@content")
            .re_first(r"(https://.*\.jpeg)")
            .split("/")
            .pop()
            .split("-")[1]
        )

        if not ean:
            return

        return ean

    @staticmethod
    def extract_discount_and_prices(response) -> tuple[bool, float, float | None]:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """

        # Current price, could be the discounted one.
        current_price = float(
            response.xpath("//meta[@property='product:price:amount']/@content").get()
        )

        # The presence of an "old price" means that there is a discount.
        # The discounted price is before the crossed out price.
        is_discounted = response.xpath("//span[@class='old-price']").get() is not None

        if is_discounted:
            old_price = response.xpath(
                "//span[@class='old-price']/span/span/span/text()"
            ).get()

            if old_price is not None:
                base_price = float(
                    re.match("([.,0-9]+)", old_price).group(1).replace(",", ".")
                )
            else:
                base_price = current_price
            return (is_discounted, base_price, current_price)
        else:
            return (is_discounted, current_price, None)

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        is_vrac = (
            response.xpath("//div[@class='vrac-options-wrapper']").get() is not None
        )

        if is_vrac:
            quantity = 100 / 1000
            quantity_unit = QuantityUnit.KILOGRAM

            return (quantity, quantity_unit)
        else:
            quantity_attribute = response.xpath(
                "//div[@class='part-product']/span/text()"
            ).get()

            if quantity_attribute is not None:
                m = re.match(
                    "([.0-9]+) ?(cl|ml|L|kg|g)", quantity_attribute, re.IGNORECASE
                )

                if m is not None:
                    raw_quantity = m.group(1)  # 200, 1,5
                    raw_quantity_unit = m.group(2)  # g, kg, L, l, cl

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

                    return (quantity, quantity_unit)
