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
    CategoryValues.AIGUILLETTES_VEGETALES: ["Tofus, émincés, galettes"],
    CategoryValues.BOULETTES_VEGETALES: ["Alternatives à la viande"],
    CategoryValues.ESCALOPES_VEGETALES_PANEES: ["Panés et nuggets"],
    CategoryValues.FALAFELS: ["Tofus, émincés, galettes"],
    CategoryValues.GALETTE_VEGETALE_CEREALES: ["Tofus, émincés, galettes"],
    CategoryValues.JAMBON_VEGETAL: ["Charcuteries végétales"],
    CategoryValues.KNAX_VEGETALES: ["Alternatives à la viande"],
    CategoryValues.LARDONS_VEGETAUX: ["Charcuteries végétales"],
    CategoryValues.NUGGETS_VEGETAUX: ["Panés et nuggets"],
    CategoryValues.SAUCISSES_VEGETALES: ["Alternatives à la viande"],
    CategoryValues.STEAK_VEGETAL: ["Alternatives à la viande"],
    CategoryValues.TOFU_FUME: ["Tofus, émincés, galettes"],
    CategoryValues.TOFU_NATURE: ["Tofus, émincés, galettes"],
    CategoryValues.FLOCON_DAVOINE: ["Céréales adultes"],
    CategoryValues.QUINOA: ["Couscous, Blés et Céréales"],
    CategoryValues.FEVES: ["Haricots et flageolets", "Légumes et purées"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Haricots et flageolets"],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: ["Haricots et flageolets"],
    CategoryValues.HARICOTS_NOIRS_CONSERVE: ["Haricots et flageolets"],
    CategoryValues.HARICOTS_ROUGES_CONSERVE: ["Haricots et flageolets"],
    CategoryValues.LENTILLES_BLONDES: ["Légumes secs"],
    CategoryValues.LENTILLES_CORAIL: ["Légumes secs"],
    CategoryValues.LENTILLES_VERTES: ["Légumes secs"],
    CategoryValues.LENTILLES_VERTES_CONSERVE: ["Lentilles et pois chiches"],
    CategoryValues.POIS_CASSES: ["Légumes secs"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Lentilles et pois chiches"],
    CategoryValues.AMANDES: ["Fruits à coques"],
    CategoryValues.BEURRE_DE_CACAHUETE: ["Pâtes à tartiner"],
    CategoryValues.CACAHUETES: ["Cacahuètes, pistaches…"],
    CategoryValues.GRAINES_CHIA: ["Légumes secs"],
    CategoryValues.GRAINES_COURGE: ["Fruits secs"],
    CategoryValues.GRAINES_TOURNESOL: ["Graines, fruits séchés"],
    CategoryValues.NOISETTES: ["Fruits à coques"],
    CategoryValues.NOIX_CAJOUS: ["Cacahuètes, pistaches…"],
    CategoryValues.PIGNONS_PIN: ["Fruits à coques"],
    CategoryValues.PISTACHES: ["Cacahuètes, pistaches…"],
    CategoryValues.BRIE: ["Camemberts Coulommiers Bries"],
    CategoryValues.BUCHE_DE_CHEVRE: ["Chèvres et Brebis"],
    CategoryValues.CAMEMBERT: ["Camemberts Coulommiers Bries"],
    CategoryValues.COMTE: ["Bloc emmental Comté Gouda", "Sélection du fromager"],
    CategoryValues.COULOMMIERS: ["Camemberts Coulommiers Bries"],
    CategoryValues.EMMENTAL: ["Bloc emmental Comté Gouda"],
    CategoryValues.FETA: ["Mozzarellas Burratas Fetas"],
    CategoryValues.FROMAGE_BLANC: ["Skyrs, fromages blancs,allégés"],
    CategoryValues.FROMAGE_RACLETTE: ["Raclettes Tartiflettes Panés"],
    CategoryValues.LAIT_DEMI_ECREME: ["Laits demi-écrémés", "Laits bio"],
    CategoryValues.LAIT_ENTIER: ["Laits entiers", "Laits bio"],
    CategoryValues.MOZZARELLA: ["Mozzarellas Burratas Fetas"],
    CategoryValues.ROQUEFORT: ["Roqueforts et bleus"],
    CategoryValues.SKYR: ["Skyrs, fromages blancs,allégés"],
    CategoryValues.YAOURT_NATURE_0: ["Natures et arômatisés"],
    CategoryValues.ANCHOIS: ["Anchois et Harengs, Rollmops"],
    CategoryValues.CABILLAUD: ["Filets, Pavés, Dos et Lamelles", "Poissons"],
    CategoryValues.COLIN_PANE: ["Panés et Steaks de poissons"],
    CategoryValues.CREVETTES: ["Coquillages et Crustacés"],
    CategoryValues.LIMANDE: ["Panés et Steaks de poissons", "Poissons panés"],
    CategoryValues.MAQUEREAU_CONSERVE: ["Maquereaux"],
    CategoryValues.NOIX_DE_SAINT_JACQUES: ["Fruits de mer et coquilles"],
    CategoryValues.SARDINES: ["Sardines"],
    CategoryValues.SAUMON: ["Filets, Pavés, Dos et Lamelles"],
    CategoryValues.SAUMON_FUME: ["Saumons et Poissons fumés"],
    CategoryValues.SURIMI: ["Surimis"],
    CategoryValues.THON: ["Thons"],
    CategoryValues.TRUITE_FUMEE: ["Saumons et Poissons fumés"],
    CategoryValues.BARRES_PROTEINEES: ["Minceur & Sport"],
    CategoryValues.BLANC_DE_DINDE_TRANCHES: ["Charcuteries de volaille"],
    CategoryValues.CHIPOLATAS: ["Saucisses et Grillades"],
    CategoryValues.CONFIT_DE_CANARD: ["Canards et Cailles", "Cassoulets et Sud ouest"],
    CategoryValues.CORDON_BLEU: ["Cordons Bleus et Croqs"],
    CategoryValues.COTES_DE_PORC: ["Porc"],
    CategoryValues.CUISSE_POULET: ["Poulets"],
    CategoryValues.ENTRECOTE_BOEUF: ["Viande bovine"],
    CategoryValues.ESCALOPES_DE_DINDE: ["Dindes"],
    CategoryValues.ESCALOPE_DE_VEAU: ["Veau"],
    CategoryValues.JAMBON_BLANC: ["Jambons blancs et rôtis"],
    CategoryValues.JAMBON_CRU: ["Charcuteries sèches tranchées"],
    CategoryValues.LAPIN: ["Lapins et autres gibiers"],
    CategoryValues.LARDONS: ["Lardons, Dés, Émincés, Bacons"],
    CategoryValues.MAGRET_DE_CANARD: ["Canards et Cailles"],
    CategoryValues.MERGUEZ: ["Saucisses et Grillades"],
    CategoryValues.NUGGETS: ["Nuggets et Tenders", "Volailles et panés"],
    CategoryValues.POITRINE_FUMEE_BACON: ["Lardons, Dés, Émincés, Bacons"],
    CategoryValues.POULET_FERMIER: ["Poulets"],
    CategoryValues.POULET_FILET: ["Poulets"],
    CategoryValues.RILLETTES: ["Pâtés, rillettes et foies gras"],
    CategoryValues.ROTI_DE_PORC: ["Jambons blancs et rôtis"],
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: ["Knacks, Saucisses, Boudins"],
    CategoryValues.SAUCISSON_SEC: ["Saucissons entiers et Chorizos"],
    CategoryValues.SAUTE_DE_VEAU: ["Veau"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Steaks hachés"],
}


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


# Web cookies to send with each request.
COOKIES = {
    "datadome": "kz625vGVbHMeCWweWc9sIujqkix8NZnGJI2Gxrc2xENbnGUF0HTrGfOPQXk9taSD4WnPjRGalpr~pPMn0wU~I_Zn0~ijSHfMvs6OU1V1jamVr5~diQKRn4t06cJYjEkv",
    "wdrivesr2": "!84x7v196niOrMsVc/xhadgKZDG6v1AQv5kFFD1fu89fdwS/VgEdEdMoC/fZPCTD3MKR9RM3ZiKqRdQ==",
    "TS01b20143": "0130c016ab8bff21ab2a53bb31f0c9a146365d5c6a0fe8eda6239d4f4e6948cad54cb5d1b3f3a5dcfcf9325b037f1183222864271a",
    "TS01e6e41f": "0130c016ab8bff21ab2a53bb31f0c9a146365d5c6a0fe8eda6239d4f4e6948cad54cb5d1b3f3a5dcfcf9325b037f1183222864271a",
    "cdrivesr2": "!zWc8V…2NFoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiYzpnb29nbGVhZHMtZVQzclp4RVkiLCJjOmNvb2tpZWludC1oM1BqRms0VCIsImM6YWItdGFzdHkiLCJjOmdvb2dsZWFuYS00VFhuSmlnUiJdfSwicHVycG9zZXMiOnsiZW5hYmxlZCI6WyJjb29raWVzZXQtUmVmR2NhS2EiLCJjb29raWVzZXQtS2FEOVVwOW4iLCJjb29raWVzZXQtTWVqWFVqVmoiXX0sInZlcnNpb24iOjJ9",
    "euconsent-v2": "CQssfAAQssfAAAHABBENC2FgAAAAAAAAAAAAAAAAAAAA.IAAA.YAAAAAAAAAAA",
    "_gcl_au": "1.1.1994375785.1793018125",
    "_ga_5LY7M0RFYE": "GS2.1.s1793018125$o1$g1$t1793018140$j45$l0$h0",
    "_ga": "GA1.1.1718431953.1793018125",
    "_MFB_": "fHwxfHx8W118fHx8",
}


# HTTP headers to send with each request.
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,pt;q=0.8,es;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Host": "fd14-courses.leclercdrive.fr",
    "Referer": "https://fd14-courses.leclercdrive.fr/magasin-033701-033701-Tours-Nord.aspx",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0",
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
            meta={"playwright": True},
            cookies=COOKIES,
            headers=HEADERS,
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
                meta={"playwright": True},
                cookies=COOKIES,
                headers=HEADERS,
                callback=self.parse_product,
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

        discounted, base_price, discounted_price = self.extract_discount_and_prices(
            response
        )
        item["price"] = base_price
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
        breadcrumbs = response.xpath(
            "//ul[@class='ulWCAD307_FilAriane']/li/a/text()"
        ).getall()

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
        Extracts whether or not the product is discounted and its both prices
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

        if (
            quantity_unit == QuantityUnit.PIECE
            and self.get_category() == CategoryValues.OEUFS
        ):
            item_name = self.get_name(response)
            eggs_num = quantity
            quantity, quantity_unit = self.compute_eggs_weight(eggs_num, item_name)

            self.logger.info(
                f"Converted eggs quantity {int(eggs_num)} to weight {quantity} kg..."
            )

        return (quantity, quantity_unit)
