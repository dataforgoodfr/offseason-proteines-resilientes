from logging import DEBUG
from re import IGNORECASE, match

from scrapy import Request, Spider

from models.product import QuantityUnit

from .items import ProductItem

# Name of the cookie used to specify the "journey" ID.
#
# A journey ID is required to get the price on the product pages as it is tied
# to a physical store.
#
# See https://github.com/dataforgoodfr/offseason-proteines-resilientes/issues/2
# for more information.
JOURNEY_COOKIE_NAME = "lark-journey"


class AuchanProductsSpider(Spider):
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

        url = f"https://www.auchan.fr/recherche?text={query}&page=1"

        yield Request(
            url=url, cookies={JOURNEY_COOKIE_NAME: journey_id}, callback=self.parse
        )

    def parse(self, response):
        product_links = response.css("a.product-thumbnail__details-wrapper")
        yield from response.follow_all(product_links, callback=self.parse_product)

        next_button = response.css("a.pagination-adjacent__link span.next").get()

        if next_button is not None:
            self.log(f"Next button detected: {next_button}")

            yield from response.follow_all(
                css="a.pagination-adjacent__link::attr(href)", callback=self.parse
            )

    def parse_product(self, response):
        item = ProductItem()

        item["name"] = response.xpath(
            "//div[@itemtype='https://schema.org/Product']/meta[@itemprop='name']/@content"
        ).get()
        item["brand"] = response.xpath("//meta[@itemprop='brand']/@content").get()
        item["eans"] = self.extract_eans(response)
        item["url"] = response.url

        (discounted, price, discounted_price) = self.extract_discount_and_prices(
            response
        )
        item["price"] = price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.extract_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {item['eans'][0]} has no quantity. Skipping...", DEBUG)
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    @staticmethod
    def extract_eans(response) -> list[str]:
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
    def extract_discount_and_prices(response) -> float:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """

        basePrice = float(response.css("script::text").re_first(r'"price": ?([.0-9]+)'))
        currentPrice = float(response.xpath("//meta[@itemprop='price']/@content").get())

        is_discounted = basePrice - currentPrice > 0

        return (
            is_discounted,
            basePrice,
            currentPrice if is_discounted else None,
        )

    @staticmethod
    def extract_quantity(response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

        product_attributes = response.css(
            ".offer-selector__attributes span.product-attribute"
        )

        for product_attribute in product_attributes:
            m = match(
                "Contenance : (\\d+x)?([.0-9]+)(ml|cl|L|kg|g)",
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
