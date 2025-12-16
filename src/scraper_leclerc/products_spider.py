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

    ALTERNATIVES = "Alimentation alternative"
    CHARCUTERIE = "Charcuterie Traiteur"
    EPICERIE = "Epicerie salée"
    FRUITS_LEGUMES = "Fruits Légumes"
    OEUFS_PRODUITS_LAITIERS = "Laitier Oeufs Végétal"
    SUCRE = "Epicerie sucrée"
    SURGELES = "Surgelés"
    VIANDES = "Viandes Poissons"

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


# Web cookies to send with each request.
COOKIES = {
    "datadome": "oS~RtmWvLsjPZFHMwLYyobN_TFoaKno_h_TAUlPySSj~LcGkR_LDXuZm6sNPSrl_v9UOJl3Cs3cdVHKcZe71UMhJUxnYeHj7QJhlwOygTJ0VD8VXUyGcL977BKyKNuHl",
    "wdrivesr2": "!peK6dVxY0scdDWGYX+grUxlNrp1QYLFI2jUHkHnUj9HPXmlcg8AiR2x5I4BjsomZ1PsGkMwHgm6EKQ==",
    "TS01b20143": "0130c016ab3f04cec1443baf33dbcf1d983460e0a93a39f2247af008c98376dc2928bca3a43723f5fd275626c695428c740a15c5bd",
    "cdrivesr2": "!5abDGLLO3eN/DCbNk4xdzclww0TjJd2nM3yplP5B47wWWlQHdX+YKlvqSPqxwFBJy96JUt8mO/sPW4M=",
    "TS01e6e41f": "0130c016ab3f04cec1443baf33dbcf1d983460e0a93a39f2247af008c98376dc2928bca3a43723f5fd275626c695428c740a15c5bd",
}


class LeclercProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Leclerc retail website.
    """

    name = "leclerc_products"
    allowed_domains = ["leclercdrive.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        url = f"https://fd14-courses.leclercdrive.fr/magasin-033701-033701-Tours-Nord/recherche.aspx?TexteRecherche={query}"

        yield Request(
            url=url,
            cookies=COOKIES,
            callback=self.parse,
        )

    def parse(self, response: Response):
        some_results = (
            response.xpath("//div[@class='divWCRS340_PasDeResultats']/h2/text()").get()
            is None
        )

        if some_results:
            all_scripts = response.css("script::text").getall()
            cdata = [s for s in all_scripts if "CDATA" in s]
            products = [c for c in cdata if "sUrlPageProduit" in c].pop()

            product_links = re.findall(r'"sUrlPageProduit":"([^"]+)"', products)

            yield from response.follow_all(
                product_links,
                cookies=COOKIES,
                callback=self.parse_product,
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

        discounted, base_price, discounted_price = self.extract_discount_and_prices(
            response
        )
        item["price"] = base_price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {item['ean']} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        self.log(f"Product cache info: {self.__get_product_info.cache_info()}")

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = response.xpath(
            "//ul[@class='ulWCAD307_FilAriane']/li/a/text()"
        ).getall()

        if len(breadcrumbs) == 0:
            self.log("No breadcrumbs detected")
            return False

        self.log(f"Breadcrumbs on the page: {breadcrumbs}")

        try:
            main_department = breadcrumbs[2].strip()
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

        pid = response.url.split("/").pop().split("-")[2]

        jstext = response.css('script:contains("sLibelleLigne1")::text').get()
        pattern = f'"IdProduit":{pid}'
        product_data = re.split(pattern, jstext)[1]

        return product_data

    def get_name(self, response: Response) -> str:
        product_info = self.__get_product_info(response)
        name = re.search(r'"sLibelleLigne1":"([^"]+)"', product_info).group(1)

        return name

    def get_brand(self, response: Response) -> str:
        product_info = self.__get_product_info(response)
        brand1 = re.search(r'"sLibelleMarque":"([^"]+)"', product_info)
        if brand1 is not None:
            brand = brand1.group(1)
        else:
            jstext = response.css('script:contains("sLibelleLigne1")::text').get()
            brand2 = re.search(r'Marque commerciale : ([^\r",]+)', jstext)
            if brand2 is not None:
                brand = brand2.group(1).split("\\r")[0]
            else:
                brand = "Unknown"

        return brand

    def get_ean13(self, response: Response) -> str:
        product_info = self.__get_product_info(response)
        ean = re.search(r'"sCodeEAN":"([0-9]{13})"', product_info).group(1)

        return ean

    def extract_discount_and_prices(
        self, response: Response
    ) -> tuple[bool, float, float | None]:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """
        product_info = self.__get_product_info(response)

        current_price = float(
            re.search(r'"nrPVUnitaireTTC":([.0-9]+)', product_info).group(1)
        )
        is_discounted = (
            re.search(r'"nrPVUnitaireBRIIDeduit":([.0-9]+)', product_info) is not None
        )

        if is_discounted:
            discounted_price = float(
                re.search(r'"nrPVUnitaireBRIIDeduit":([.0-9]+)', product_info).group(1)
            )

            return (is_discounted, current_price, discounted_price)
        else:
            return (is_discounted, current_price, None)

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        product_info = self.__get_product_info(response)

        quantity = float(
            re.search(r'"nrContenanceTotale":([.0-9]+)', product_info).group(1)
        )
        quantity_unit = re.search(
            r'"sUniteMesureTotale":"([^"]+)"', product_info
        ).group(1)
        quantity_unit = QuantityUnit(quantity_unit)

        return (quantity, quantity_unit)
