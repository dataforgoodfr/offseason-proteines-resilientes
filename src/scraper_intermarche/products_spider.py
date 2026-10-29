import json
import re
from collections.abc import Generator
from enum import StrEnum, unique
from functools import lru_cache

from scrapy import Request, Spider
from scrapy.http import Response

from models.category import CategoryValues
from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider

# Mapping between categories and departments.
CAT_DEPT_MAPPING = {
    CategoryValues.BOULETTES_VEGETALES: ["Nutrition et Diététique"],
    CategoryValues.ESCALOPES_VEGETALES_PANEES: ["Traiteur végétal"],
    CategoryValues.FALAFELS: ["Pâtes farcies"],
    CategoryValues.GALETTE_VEGETALE_CEREALES: ["Repas diététiques"],
    CategoryValues.NUGGETS_VEGETAUX: ["Traiteur végétal"],
    CategoryValues.SAUCISSES_VEGETALES: ["Traiteur végétal", "Entrées et Feuilletés"],
    CategoryValues.STEAK_VEGETAL: ["Traiteur végétal", "Entrées et Feuilletés"],
    CategoryValues.FLOCON_DAVOINE: ["Céréales diététiques"],
    CategoryValues.QUINOA: ["Blé et Céréales"],
    CategoryValues.FLAGEOLETS: ["Lentilles, Pois cassé et Légumes secs"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Haricots blancs, Rouges et Flageolets"],
    CategoryValues.HARICOTS_BLANCS: ["Lentilles, Pois cassé et Légumes secs"],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: ["Haricots blancs, Rouges et Flageolets"],
    CategoryValues.HARICOTS_NOIRS_CONSERVE: ["Haricots blancs, Rouges et Flageolets"],
    CategoryValues.HARICOTS_ROUGES: ["Lentilles, Pois cassé et Légumes secs"],
    CategoryValues.HARICOTS_ROUGES_CONSERVE: ["Haricots blancs, Rouges et Flageolets"],
    CategoryValues.LENTILLES_BLONDES: ["Lentilles, Pois cassé et Légumes secs"],
    CategoryValues.LENTILLES_CORAIL: [
        "Lentilles, Pois cassé et Légumes secs",
        "Repas diététiques",
    ],
    CategoryValues.LENTILLES_VERTES: ["Lentilles, Pois cassé et Légumes secs"],
    CategoryValues.LENTILLES_VERTES_CONSERVE: ["Lentilles et Pois chiches"],
    CategoryValues.POIS_CASSES: ["Lentilles, Pois cassé et Légumes secs"],
    CategoryValues.POIS_CHICHES: ["Lentilles et Pois chiches"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Lentilles et Pois chiches"],
    CategoryValues.AMANDES: ["Aide à la pâtisserie", "Amandes et noisettes"],
    CategoryValues.BEURRE_DE_CACAHUETE: ["Pâtes à tartiner"],
    CategoryValues.CACAHUETES: ["Cacahuètes et Fruits secs"],
    CategoryValues.GRAINES_CHIA: ["Repas diététiques"],
    CategoryValues.GRAINES_COURGE: ["Repas diététiques"],
    CategoryValues.GRAINES_TOURNESOL: ["Fruits à coque"],
    CategoryValues.NOISETTES: ["Aide à la pâtisserie ", "Fruits à coque"],
    CategoryValues.NOIX_CAJOUS: ["Cacahuètes et Fruits secs"],
    CategoryValues.PIGNONS_PIN: ["Aide à la pâtisserie", "Légumes sec"],
    CategoryValues.PISTACHES: ["Cacahuètes et Fruits secs"],
    CategoryValues.BRIE: ["Camemberts, Coulommiers, Bries"],
    CategoryValues.BUCHE_DE_CHEVRE: ["Chèvres et Brebis"],
    CategoryValues.CAMEMBERT: ["Camemberts, Coulommiers, Bries"],
    CategoryValues.COMTE: ["Emmentals, Comtés et Goudas"],
    CategoryValues.COULOMMIERS: ["Camemberts, Coulommiers, Bries"],
    CategoryValues.EMMENTAL: ["Emmentals, Comtés et Goudas"],
    CategoryValues.FETA: ["Mozzarella, Feta et Mascarpone"],
    CategoryValues.FROMAGE_BLANC: ["Fromages blancs"],
    CategoryValues.FROMAGE_RACLETTE: ["Raclettes fondus et Tartiflettes"],
    CategoryValues.LAIT_DEMI_ECREME: ["Laits demi-écrémés"],
    CategoryValues.LAIT_ENTIER: ["Laits entiers"],
    CategoryValues.MOZZARELLA: ["Mozzarella, Feta et Mascarpone"],
    CategoryValues.OEUFS: ["Oeufs"],
    CategoryValues.PARMESAN_RAPE: ["Fromages râpés"],
    CategoryValues.PETITS_SUISSES: ["Petits suisses "],
    CategoryValues.ROQUEFORT: ["Roqueforts et Bleus"],
    CategoryValues.SKYR: ["Skyrs"],
    CategoryValues.YAOURT_NATURE_0: ["Allégés"],
    CategoryValues.ANCHOIS: ["Harengs et Anchois"],
    CategoryValues.CABILLAUD: ["Dos et Autres morceaux", "Poissons natures"],
    CategoryValues.COLIN_PANE: ["Poissons panés", "Poissons panés et cuisinés"],
    CategoryValues.CREVETTES: [
        "Fruits de mer et crustacés",
        "Crevettes et Fruits de mer préparés",
    ],
    CategoryValues.LIMANDE: ["Poissons panés et cuisinés", "Poissons panés"],
    CategoryValues.MAQUEREAU_CONSERVE: ["Maquereaux"],
    CategoryValues.NOIX_DE_SAINT_JACQUES: ["Coquilles et Noix de St jacques"],
    CategoryValues.SARDINES: ["Sardines"],
    CategoryValues.SAUMON: ["Poissons natures"],
    CategoryValues.SAUMON_FUME: ["Saumon et Poissons fumés"],
    CategoryValues.SURIMI: ["Surimis et Batônnets"],
    CategoryValues.THON: ["Thons et Saumons"],
    CategoryValues.TRUITE_FUMEE: ["Saumon et Poissons fumés"],
    CategoryValues.ISOLAT_WHEY: ["Whey et protéine en poudre"],
    CategoryValues.BARRES_PROTEINEES: ["Barres de céréales"],
    CategoryValues.TOFU_FUME: ["Repas diététiques"],
    CategoryValues.TOFU_NATURE: ["Repas diététiques"],
    CategoryValues.BLANC_DE_DINDE_TRANCHES: ["Blancs de dinde"],
    CategoryValues.CHIPOLATAS: ["Saucisserie"],
    CategoryValues.CONFIT_DE_CANARD: ["Canards"],
    CategoryValues.CORDON_BLEU: ["Cordons Bleus et Panés de volaille"],
    CategoryValues.COTES_AGNEAU: ["Agneaux"],
    CategoryValues.COTES_DE_PORC: ["Porcs"],
    CategoryValues.CUISSE_POULET: ["Poulets"],
    CategoryValues.ENTRECOTE_BOEUF: ["Viandes bovines"],
    CategoryValues.ESCALOPES_DE_DINDE: ["Dindes"],
    CategoryValues.ESCALOPE_DE_VEAU: ["Veaux"],
    CategoryValues.FILET_MIGNON_DE_PORC: ["Porcs"],
    CategoryValues.GIGOT_AGNEAU: ["Agneaux"],
    CategoryValues.JAMBON_BLANC: ["Jambons blancs et Rôtis"],
    CategoryValues.JAMBON_CRU: ["Jambons crus"],
    CategoryValues.LARDONS: ["Lardons natures et Fumés"],
    CategoryValues.MAGRET_DE_CANARD: ["Canards"],
    CategoryValues.MERGUEZ: ["Saucisserie"],
    CategoryValues.NUGGETS: ["Nuggets"],
    CategoryValues.POITRINE_FUMEE_BACON: ["Bacon et Poitrines"],
    CategoryValues.POULET_FERMIER: ["Poulets"],
    CategoryValues.POULET_FILET: ["Poulets"],
    CategoryValues.RILLETTES: ["Rillettes"],
    CategoryValues.ROTI_DE_BOEUF: ["Viandes bovines"],
    CategoryValues.ROTI_DE_PORC: ["Rôtis"],
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: ["Saucisses", "Knacks"],
    CategoryValues.SAUCISSON_SEC: ["Saucissons secs"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Viandes hachées"],
}


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    LAITIER = "Fromages, Crèmerie et Oeufs"
    VIANDE = "Viandes et Poissons"
    CHARCUTERIE = "Charcuterie"
    EPICERIE = "Épicerie salée"
    SUCRE = "Épicerie sucrée"
    FRUIT_LEGUME = "Fruits et Légumes"
    SURGELE = "Surgelés"
    ALTERNATIVE = "Alimentation alternative"

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


# HTTP headers to send with each request.
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,pt;q=0.8,es;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.intermarche.com/accueil",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "sec-ch-device-memory": "8",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.138", "Not;A=Brand";v="24.0.0.0", "Google Chrome";v="128.0.6613.138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
}

# Web cookies to send with each request.
COOKIES = {
    "datadome": "7_uMda9h4vr1oYSSL4AB3GyEfOXpaJlEnljGYsGgj1JkRPvPqRbf_H0xvxSAVuGUtiuWDq_E7yo3ol4DNZpJCnvTmEHfPxfuVPrcXVMcPZWkrYgLEU1xoDvNwgaWr5Wu",
    "itm_pdv": "{%22ref%22:%2209117%22%2C%22isEcommerce%22:true%2C%22name%22:%22Super%2520Notre%2520Dame%2520D'oe%22%2C%22city%22:%22Notre%2520Dame%2520D'oe%22}",
    "novaParams": "{%22pdvRef%22:%2209117%22}",
}


class IntermarcheProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Intermarché retail website.
    """

    name = "intermarche_products"
    allowed_domains = ["www.intermarche.com"]

    custom_settings = {}

    current_page = 0
    query: str
    url: str

    def __get_next_page(self) -> str:
        """
        Returns the next URL to visit while incrementing the current page index.
        """

        self.current_page += 1
        if self.get_category() == "Œufs":
            self.url = f"https://www.intermarche.com/rayons/fromages-cremerie-et-oeufs/oeufs/16773?page={self.current_page}"
        else:
            self.url = f"https://www.intermarche.com/recherche/{self.query}?page={self.current_page}"

        self.logger.debug(f"Next page set to {self.current_page}")

        return self.url

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        self.query = query

        yield Request(
            url=self.__get_next_page(),
            cookies=COOKIES,
            headers=HEADERS,
            callback=self.parse,
        )

    def parse(self, response: Response):
        product_links = response.xpath(
            "//a[@class='link transition-colors font-normal font-body text-body-lg text-c-primary flex h-full flex-col no-underline']/@href"
        ).getall()

        yield from response.follow_all(
            product_links,
            cookies=COOKIES,
            headers=HEADERS,
            callback=self.parse_product,
        )

        if response.xpath("//body").re_first("hasNextPage.*: ?true}"):
            self.logger.debug("Next page detected")

            yield Request(
                url=self.__get_next_page(),
                cookies=COOKIES,
                headers=HEADERS,
                callback=self.parse,
            )

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

        self.logger.debug(f"Product cache info: {self.__get_product_info.cache_info()}")

        yield item

    def is_relevant(self, response: Response) -> bool:
        microdata_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).get()
        microdata = json.loads(microdata_content)

        breadcrumbs_data = [
            data for data in microdata if data["@type"] == "BreadcrumbList"
        ].pop()
        breadcrumbs = [
            listitem["name"] for listitem in breadcrumbs_data["itemListElement"]
        ]

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

    @lru_cache(maxsize=8, typed=True)
    def __get_product_info(self, response: Response):
        """
        Extracts the product information from the response.

        The product information is cached.
        """

        microdata_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).get()

        product_data = [
            data for data in json.loads(microdata_content) if data["@type"] == "Product"
        ]

        return product_data.pop()

    def get_name(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["name"]

    def get_brand(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["brand"]

    def get_ean13(self, response: Response) -> str | None:
        ean = response.url.split("/").pop()

        if not ean:
            return

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

        current_product = response.css(".mb-16")

        # current price, only if no discount
        current_price = current_product.xpath(
            ".//div[@class='product--price']/p/text()"
        ).get()

        if current_price is not None:
            is_discounted = False
            base_price = float(current_price.replace("€", "").replace(",", ".").strip())
        else:
            prices = current_product.xpath(
                ".//div[has-class('product--price')]/span/text()"
            ).getall()
            if len(prices) == 0:
                return None
            elif len(prices) == 1 or prices[0] == prices[1]:
                is_discounted = False
                base_price = float(prices[0].replace("€", "").replace(",", ".").strip())
            else:
                is_discounted = True
                discounted_price = float(
                    prices[0].replace("€", "").replace(",", ".").strip()
                )
                base_price = float(
                    prices[1]
                    .replace("au lieu de", "")
                    .replace("€", "")
                    .replace(",", ".")
                    .strip()
                )

        return (
            is_discounted,
            base_price,
            discounted_price if is_discounted else None,
        )

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

        packaging = response.xpath(
            '//p[@class="transition-colors font-normal font-body text-body-sm text-grey-700"]/text()'
        ).get()

        m = re.match(
            "(.+) ([.0-9]+) ?(ml|cl|L|kg|g)?",
            packaging,
            re.IGNORECASE,
        )

        if m is None:
            return

        raw_multiplier = m.group(1)  # les 2 plaquettes, la bouteille
        raw_quantity = m.group(
            2
        )  # 200, 1,5 = usually the total quantity, but sometimes not!
        raw_quantity_unit = m.group(3)  # g, kg, L, l, cl

        quantity = float(raw_quantity.replace(",", "."))

        if raw_quantity_unit is None:
            quantity_unit = QuantityUnit.PIECE

            if self.get_category() == CategoryValues.OEUFS:
                item_name = self.get_name(response)
                eggs_num = quantity
                quantity, quantity_unit = self.compute_eggs_weight(eggs_num, item_name)

                self.logger.info(
                    f"Converted eggs quantity {int(eggs_num)} to weight {quantity} kg..."
                )
        else:
            match raw_quantity_unit.lower():
                case "kg":
                    quantity_unit = QuantityUnit.KILOGRAM
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

        # check if packaging text contains total: Les 2 briques de 30cl - 60cl
        # sometimes not: les 6 briques de 1 l
        is_separator = packaging.find("-")
        if is_separator > 0:
            return (quantity, quantity_unit)
        else:
            nb = int("".join(filter(str.isdigit, raw_multiplier)) or 1)
            return (quantity * nb, quantity_unit)
