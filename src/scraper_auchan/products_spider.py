from collections.abc import Generator
from enum import StrEnum, unique
from re import IGNORECASE, match

from scrapy import Request, Spider
from scrapy.http import Response

from models.product import QuantityUnit
from utils.spider import ProductSpider

from .items import ProductItem

# Name of the cookie used to specify the "journey" ID.
#
# A journey ID is required to get the price on the product pages as it is tied
# to a physical store.
#
# See https://github.com/dataforgoodfr/offseason-proteines-resilientes/issues/2
# for more information.
JOURNEY_COOKIE_NAME = "lark-journey"

# List of store department that are not relevant.
EXCLUSION_LIST = (
    "cuisiné",
    "bébé",
    "pizza",
    "bouillon",
    "boisson",
    "alcools",
    "glaces",
)


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    CHARCUTERIE = "Charcuterie, traiteur"  # cn12
    EPICERIE = "Epicerie salée"  # cn06
    FRAIS = "Marché frais"  # cb19
    FRUITS_LEGUMES = "Fruits, légumes"  # cn03
    OEUFS_PRODUITS_LAITIERS = "Produits laitiers, oeufs, fromages"  # cn01
    SUCRE = "Epicerie sucrée"  # cn05
    SURGELES = "Surgelés"  # cn04
    VIANDES = "Boucherie, volaille, poissonnerie"  # cn02

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


class AuchanProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Auchan retail website.
    """

    name = "auchan_products"
    allowed_domains = ["www.auchan.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)
        journey_id = getattr(self, "journey_id", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")
        if journey_id is None:
            raise AttributeError("Missing 'journey_id' argument")

        url = (
            f"https://www.auchan.fr/recherche?text={query}&page=1"
            "&categorylevel1=produits20laitiers2c20oeufs2c20fromages"
            "&categorylevel1=boucherie2c20volaille2c20poissonnerie"
            "&categorylevel1=fruits2c20le9gumes"
            "&categorylevel1=fruits2c20le9gumes"
            "&categorylevel1=surgele9s"
            "&categorylevel1=epicerie20sucre9e"
            "&categorylevel1=epicerie20sale9e"
            "&categorylevel1=charcuterie2c20traiteur"
        )

        yield Request(
            url=url, cookies={JOURNEY_COOKIE_NAME: journey_id}, callback=self.parse
        )

    def parse(self, response: Response):
        product_links = response.css("a.product-thumbnail__details-wrapper")
        yield from response.follow_all(product_links, callback=self.parse_product)

        next_button = response.css("a.pagination-adjacent__link span.next").get()

        if next_button is not None:
            self.log(f"Next button detected: {next_button}")

            yield from response.follow_all(
                css="a.pagination-adjacent__link::attr(href)", callback=self.parse
            )

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        if not self.is_relevant(response):
            self.log("Product is irrelevant. Skipping...")
            return

        item["name"] = self.get_name(response)
        item["brand"] = self.get_brand(response)
        item["category"] = self.get_category()
        item["url"] = response.url

        eans = self.get_ean13s(response)

        if eans is None:
            self.log("No EAN found. Skipping...")
            return

        item["eans"] = eans

        discounted, price, discounted_price = self.extract_discount_and_prices(
            response
        ) or (None, None, None)

        if price is not None:
            item["price"] = price
            item["discounted"] = discounted

            if discounted:
                item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {item['eans'][0]} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    def is_relevant(self, response: Response) -> bool:
        """
        Filters out irrelevant products based on the store department.
        """

        breadcrumbs = response.xpath(
            "//span[@class='site-breadcrumb__item']/a/text()"
        ).getall()

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

    def get_name(self, response: Response) -> str:
        name = response.xpath(
            "//div[@itemtype='https://schema.org/Product']/meta[@itemprop='name']/@content"
        ).get()

        return name

    def get_brand(self, response: Response) -> str:
        brand = response.xpath("//meta[@itemprop='brand']/@content").get()

        return brand

    def get_ean13(self, response: Response) -> str | None:
        """
        Unused.

        Unlike other distributors, Auchan returns multiple EAN-13 per product
        page. As such, the EAN-13s are returned by the 'get_ean13s' method
        instead.
        """

        return

    @staticmethod
    def get_ean13s(response: Response) -> list[str] | None:
        content_wrappers = response.css(
            ".product-description__feature-wrapper .product-description__feature-group-wrapper"
        )

        for content_wrapper in content_wrappers:
            label = content_wrapper.css(
                ".product-description__feature-label::text"
            ).get()

            if label == "Réf / EAN :":
                eans = content_wrapper.css(
                    ".product-description__feature-values::text"
                ).re(r"(\d{13})")

                return eans

    @staticmethod
    def extract_discount_and_prices(
        response: Response,
    ) -> tuple[bool, float, float | None] | None:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.

        Returns None if no price can be found.
        """

        page_scripts = response.css("script::text")
        raw_base_price = page_scripts.re_first(r'"price": ?([.0-9]+)')

        if raw_base_price is None:
            return None

        base_price = float(raw_base_price)
        current_price = float(
            response.xpath("//meta[@itemprop='price']/@content").get()
        )

        is_discounted = base_price - current_price > 0

        return (
            is_discounted,
            base_price,
            current_price if is_discounted else None,
        )

    @staticmethod
    def get_quantity(response: Response) -> tuple[float, QuantityUnit] | None:
        product_attributes = response.css(
            ".offer-selector__attributes span.product-attribute"
        )

        for product_attribute in product_attributes:
            m = match(
                "Contenance : (\\d+x)?([.,0-9]+) ?(ml|cl|L|kg|g)",
                product_attribute.attrib["aria-label"],
                IGNORECASE,
            )

            if m is not None:
                multiplier = m.group(1)  # None or 2x, 6x
                raw_quantity = m.group(2)  # 200, 1,5
                raw_quantity_unit = m.group(3)  # g, kg, L, l, cl, ml

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

                if multiplier is None:
                    return (quantity, quantity_unit)
                else:
                    nb = int("".join(filter(str.isdigit, multiplier)))
                    return (quantity * nb, quantity_unit)
