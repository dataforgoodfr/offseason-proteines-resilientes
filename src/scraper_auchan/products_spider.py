from scrapy import Request, Spider

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
        item["price"] = self.extract_price(response)
        item["url"] = response.url

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
                ).re("(\d{13})")

                return eans

    @staticmethod
    def extract_price(response) -> float:
        """
        Extracts the price from the response and turns it from the string
        pattern 'X,YY€' into a float.
        """

        value = response.css(".product-price::text").get()

        return float(value.replace("€", "").replace(",", ".").strip())
