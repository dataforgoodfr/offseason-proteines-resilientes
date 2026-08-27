import json
from collections.abc import Generator
from enum import StrEnum, unique

from scrapy import Request, Spider
from scrapy.http import Response

from models.category import CategoryValues
from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider

# Mapping between categories and departments.
CAT_DEPT_MAPPING = {
    CategoryValues.GALETTE_VEGETALE_CEREALES_SURGELE: ["Accompagnements"],
    CategoryValues.NUGGETS_VEGETAUX_SURGELE: ["Plats cuisinés végétariens"],
    CategoryValues.FEVES: ["Légumineuses"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Haricots"],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: ["Haricots"],
    CategoryValues.LENTILLES_VERTES_CONSERVE: ["Légumineuses"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Légumineuses"],
    CategoryValues.CABILLAUD: ["Cabillaud"],
    CategoryValues.COLIN_PANE: ["Poissons panés, meunières"],
    CategoryValues.CREVETTES: ["Crevettes, langoustes, autres crustacés"],
    CategoryValues.LIMANDE: ["Poissons panés, meunières"],
    CategoryValues.MAQUEREAU_FRAIS: ["Thon et maquereau"],
    CategoryValues.NOIX_DE_SAINT_JACQUES: ["Saint-Jacques"],
    CategoryValues.SARDINES_FRAICHES: ["Thon et maquereau"],
    CategoryValues.SAUMON: ["Saumon et truite"],
    CategoryValues.SAUMON_FUME: ["Saumon et truite"],
    CategoryValues.THON_FRAIS: ["Thon et maquereau"],
    CategoryValues.TRUITE_FUMEE: ["Poissons marinés, fumés, cuisinés"],
    CategoryValues.CHIPOLATAS: ["Barbecue"],
    CategoryValues.CONFIT_DE_CANARD: ["Canard"],
    CategoryValues.CORDON_BLEU: ["Volailles panées"],
    CategoryValues.COTES_AGNEAU: ["Agneau"],
    CategoryValues.COTES_DE_PORC: ["Porc"],
    CategoryValues.CUISSE_POULET: ["Poulet et dinde"],
    CategoryValues.ENTRECOTE_BOEUF: ["Boeuf", "Viandes BIO et labellisées"],
    CategoryValues.ESCALOPES_DE_DINDE: ["Poulet et dinde"],
    CategoryValues.ESCALOPE_DE_VEAU: ["Veau"],
    CategoryValues.GIGOT_AGNEAU: ["Agneau"],
    CategoryValues.LAPIN: ["Viandes"],
    CategoryValues.MAGRET_DE_CANARD: ["Canard"],
    CategoryValues.MERGUEZ: ["Barbecue"],
    CategoryValues.NUGGETS: ["Volailles panées"],
    CategoryValues.POULET_FILET: ["Poulet et dinde"],
    CategoryValues.SAUTE_DE_VEAU: ["Veau"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Boeuf"],
}


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    EPICERIE = "Épicerie salée"
    FRUITS_LEGUMES = "Légumes et fruits"
    SUCRE = "Épicerie sucrée"
    VIANDES = "Viandes et poissons"

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


class PicardProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Picard retail website.
    """

    name = "picard_products"
    allowed_domains = ["www.picard.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        url = f"https://www.picard.fr/recherche?q={query}"

        yield Request(
            url=url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
            callback=self.parse,
        )

    def parse(self, response: Response):
        product_links = response.xpath(
            '//a[has-class("js-gtm-pi-product-link")]/@href'
        ).getall()
        yield from response.follow_all(
            product_links, meta={"playwright": True}, callback=self.parse_product
        )

        next_page_url = response.css('[rel="next"] ::attr(href)').get()

        if next_page_url is not None:
            self.logger.debug(f"Next page detected: {next_page_url}")
            yield Request(
                url=next_page_url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse,
            )

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        if not self.is_relevant(response):
            self.logger.info("Product is irrelevant. Skipping...")
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
            self.logger.info(f"Product {item['ean']} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    def is_relevant(self, response: Response) -> bool:
        microdata_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        microdata = [json.loads(data) for data in microdata_content]
        itemlist = [
            data for data in microdata if data["@type"] == "BreadcrumbList"
        ].pop()
        breadcrumbs = [item["name"] for item in itemlist["itemListElement"]]

        if len(breadcrumbs) == 0:
            self.logger.info("No breadcrumbs detected")
            return False

        self.logger.info(f"Breadcrumbs on the page: {breadcrumbs}")

        expected_departments = CAT_DEPT_MAPPING[self.get_category()]
        if any(x in breadcrumbs for x in expected_departments):
            return True
        else:
            self.logger.info(
                f"Store department '{breadcrumbs.pop()}' is irrelevant for category '{self.get_category()}'. Skipping..."
            )
            return False

    def get_name(self, response: Response) -> str:
        name = response.xpath("//h1[@itemprop='name']/text()").get()
        return name.strip()

    def get_brand(self, response: Response) -> str:
        brand = response.xpath("//meta[@itemprop='brand']/@content").get()
        return brand

    def get_ean13(self, response: Response) -> str:
        ean = response.xpath("//meta[@itemprop='gtin13']/@content").get()
        return ean

    @staticmethod
    def extract_discount_and_prices(
        response: Response,
    ) -> tuple[bool, float, float | None] | None:
        """
        Extracts whether or not the product is discounted and its both prices
        (normal and discounted) from the response.

        Returns None if no price can be found.
        """

        current_product = response.css(".pi-ProductPage-top")

        base_price = response.xpath("//meta[@itemprop='price']/@content").get()
        if base_price is None:
            return

        is_discounted = (
            current_product.xpath(".//div[@class='pi-ProductOffer-salesPrice']").get()
            is not None
        )

        if is_discounted:
            discounted_price = (
                response.css(".pi-ProductOffer-salesPrice")
                .css("div:has(> span) *::text")
                .getall()
                .pop()
            )

            discounted_price = float(
                discounted_price.replace("€", "").replace(",", ".").strip()
            )

        return (
            is_discounted,
            float(base_price),
            discounted_price if is_discounted else None,
        )

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """
        current_product = response.css(".pi-ProductPage-top")

        w = current_product.xpath(
            ".//div[@class='pi-ProductDetails-weight']/span/text()"
        ).get()
        raw_quantity_unit = w.split().pop(-1)
        raw_quantity = w.split().pop(-2)
        quantity = float(raw_quantity.replace(",", "."))

        match raw_quantity_unit.lower():
            case "kg":
                quantity_unit = QuantityUnit.KILOGRAM
            case "g":
                quantity = quantity / 1000
                quantity_unit = QuantityUnit.KILOGRAM

        return (quantity, quantity_unit)
