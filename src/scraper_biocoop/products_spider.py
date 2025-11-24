from logging import DEBUG
import re
from enum import StrEnum, unique

from scrapy import Request, Spider

from .items import ProductItem
from models.product import QuantityUnit, Category


@unique
class Department(StrEnum):
    """
    The main store department of the product.
    """

    LAITIER = "Crémerie"
    VIANDE = "Traiteur, Boucherie, Poissonnerie"
    EPICERIE = "Epicerie Salée"
    SUCRE = "Epicerie Sucrée"
    FRUIT_LEGUME = "Fruits et Légumes"
    SURGELE = "Surgelés"
    VRAC = "Vrac"

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


class BiocoopProductsSpider(Spider):
    """
    Scrapy Spider for the products of the Biocoop retail website.
    """

    name = "biocoop_products"
    allowed_domains = ["www.biocoop.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)
        category = getattr(self, "category", None)
        aliment = getattr(self, "aliment", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")
        if category is None:
            category = Category.UNKNOWN
        if aliment is None:
            aliment = "Unknown"

        url = f"https://www.biocoop.fr/magasin-biocoop_biocite/catalogsearch/result/?q={query}&p=1"

        yield Request(url=url, callback=self.parse)

    def parse(self, response):
        product_links = response.xpath(
            "//div[@class='product-item-info']/a/@href"
        ).getall()
        yield from response.follow_all(product_links, callback=self.parse_product)

        next_page_url = response.css("a.next-page ::attr(data-href)").get()

        if next_page_url is not None:
            self.log(f"Next button detected: {next_page_url}")

            yield response.follow(next_page_url, callback=self.parse)

    def parse_product(self, response):
        item = ProductItem()

        ean = (
            response.xpath("//meta[@itemprop='image']/@content")
            .re_first(r"(https://.*\.jpeg)")
            .split("/")
            .pop()
            .split("-")[1]
        )

        if len(ean) == 0:
            self.log("No EAN found. Skipping...", DEBUG)
            return

        breadcrumbs = response.xpath(
            "//div[@class='breadcrumbs']/ul/li/a/text()"
        ).getall()

        exclusion_list = (
            "préparés",
            "bébé",
            "pizza",
            "bouillon",
            "boisson",
            "alcools",
            "glaces",
            "apéritif",
        )
        any_exclusion = [
            s for excl in exclusion_list for s in breadcrumbs if excl in s.lower()
        ]

        if Department(breadcrumbs[1]) is None:
            self.log(f"Not a valid food dept: {breadcrumbs[1]}. Skipping...", DEBUG)
            return
        elif any_exclusion:
            self.log(f"Not an accepted product: {any_exclusion}. Skipping...", DEBUG)
            return
        else:
            item["name"] = response.xpath("//span[@itemprop='name']/text()").get()
            item["brand"] = response.xpath("//span[@class='brand value']/text()").get()
            item["url"] = response.url
            item["ean"] = ean

            discounted, basePrice, discountedPrice = self.extract_discount_and_prices(
                response
            )
            item["price"] = basePrice
            item["discounted"] = discounted
            if discounted:
                item["discounted_price"] = discountedPrice

            quantity, quantity_unit = self.extract_quantity(response) or (None, None)

            if quantity is None:
                self.log(f"Product {ean} has no quantity. Skipping...", DEBUG)
                return

            item["quantity"] = quantity
            item["quantity_unit"] = quantity_unit

            yield item

    @staticmethod
    def extract_discount_and_prices(response) -> tuple[bool, float, float | None]:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """

        # Current price, could be the discounted one.
        currentPrice = float(
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
                basePrice = float(
                    re.match("([.,0-9]+)", old_price).group(1).replace(",", ".")
                )
            else:
                basePrice = currentPrice
            return (is_discounted, basePrice, currentPrice)
        else:
            return (is_discounted, currentPrice, None)

    @staticmethod
    def extract_quantity(response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

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
                    quantity_unit = raw_quantity_unit

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

                    return (quantity, quantity_unit)
