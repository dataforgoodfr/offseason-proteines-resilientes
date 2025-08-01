from scrapy import Request, Spider

from .items import ProductItem


class AuchanProductsSpider(Spider):
    """
    Scrapy Spider for the products of the Auchan retail website.
    """

    name = "auchan_products"
    allowed_domains = ["www.auchan.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        url = f"https://www.auchan.fr/recherche?text={query}&page=1"

        yield Request(url=url, callback=self.parse)

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
