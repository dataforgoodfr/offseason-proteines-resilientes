import re
from collections.abc import Generator
from enum import StrEnum, unique

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

    EPICERIE = "Epicerie Salée"
    FRUITS_LEGUMES = "Fruits et Légumes"
    OEUFS_PRODUITS_LAITIERS = "Crémerie"
    SUCRE = "Epicerie Sucrée"
    SURGELE = "Surgelés"
    VIANDES = "Traiteur, Boucherie, Poissonnerie"
    SPORT = "Bien-être, Santé"
    VRAC = "Vrac"

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

        yield Request(
            url=url,
            callback=self.parse,
            meta={
                "handle_httpstatus_list": [302],
            },
            dont_filter=True,
        )

    def parse(self, response: Response):
        if response.status == 302:
            product_links = [response.url]
        else:
            product_links = response.xpath(
                "//div[@class='product-item-info']/a/@href"
            ).getall()
        yield from response.follow_all(product_links, callback=self.parse_product)

        next_page_url = response.css("a.next-page ::attr(data-href)").get()

        if next_page_url is not None:
            self.logger.debug(f"Next button detected: {next_page_url}")

            yield response.follow(next_page_url, callback=self.parse)

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        if not self.is_relevant(response):
            self.logger.info("Product is irrelevant. Skipping...")
            return

        ean = self.get_ean13(response)

        if ean is None:
            self.logger.info("No EAN-13 found. Skipping...")
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
            self.logger.info(f"Product {ean} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = response.css("script::text").re_first(
            r"'product_category1': '(.+)'"
        )
        breadcrumbs = bytes(breadcrumbs, "utf-8").decode("unicode_escape").split("/")

        if len(breadcrumbs) == 0:
            self.logger.info("No breadcrumbs detected")
            return False

        self.logger.info(f"Breadcrumbs on the page: {breadcrumbs}")

        try:
            main_department = breadcrumbs[0]
            main_department = Department(main_department)
        except ValueError:
            self.logger.info(
                f"Main store department {main_department} is irrelevant. Skipping..."
            )
            return False

        any_exclusion = [
            s for excl in EXCLUSION_LIST for s in breadcrumbs if excl in s.lower()
        ]

        if any_exclusion:
            self.logger.info(
                f"Hit excluded store departments: {any_exclusion}. Skipping..."
            )
            return False

        return True

    def get_name(self, response: Response) -> str:
        name = response.xpath("//span[@itemprop='name']/text()").get()

        return name

    def get_brand(self, response: Response) -> str:
        brand = response.xpath("//span[@class='brand value']/text()").get()

        return brand

    def get_ean13(self, response: Response) -> str | None:
        img_link_parts = (
            response.xpath("//meta[@itemprop='image']/@content")
            .re_first(r"(https://.*\.jpe?g)")
            .split("/")
            .pop()
            .split("-")
        )

        if len(img_link_parts) < 2 or len(img_link_parts[1]) != 13:
            return

        return img_link_parts[1]

    @staticmethod
    def extract_discount_and_prices(
        response: Response,
    ) -> tuple[bool, float, float | None]:
        """
        Extracts whether or not the product is discounted and its both prices
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
