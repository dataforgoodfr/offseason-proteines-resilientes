import json
from collections.abc import Generator
from enum import StrEnum, unique
from functools import lru_cache

from scrapy import Request, Spider
from scrapy.http import Response

from models.category import CategoryValues
from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider

# Name of the cookie used to specify the store ID.
STORE_COOKIE_NAME = "storeId"

# Mapping between categories and departments.
CAT_DEPT_MAPPING = {
    CategoryValues.AIGUILLETTES_VEGETALES: ["Végétal"],
    CategoryValues.BOULETTES_VEGETALES: ["Végétal", "Plats cuisinés bio"],
    CategoryValues.ESCALOPES_VEGETALES_PANEES: ["Végétal"],
    CategoryValues.FALAFELS: ["Végétal"],
    CategoryValues.GALETTES_DE_LEGUMINEUSES: ["Plats cuisinés bio", "Végétal"],
    CategoryValues.GALETTE_VEGETALE_CEREALES: ["Végétal"],
    CategoryValues.JAMBON_VEGETAL: ["Végétal"],
    CategoryValues.KNAX_VEGETALES: ["Végétal"],
    CategoryValues.LARDONS_VEGETAUX: ["Lardon, dés, poitrine", "Végétal"],
    CategoryValues.NUGGETS_VEGETAUX: ["Végétal"],
    CategoryValues.SAUCISSES_VEGETALES: ["Végétal"],
    CategoryValues.STEAK_VEGETAL: ["Végétal"],
    CategoryValues.FLOCON_DAVOINE: ["Céréales adulte"],
    CategoryValues.QUINOA: ["Semoule, céréales, blé", "Légumes secs"],
    CategoryValues.SARRASIN: ["Légumes secs, sous-vide"],
    CategoryValues.SEITAN: ["Plats cuisinés bio"],
    CategoryValues.FEVES: [
        "Légumes verts",
        "Légumes natures",
    ],
    CategoryValues.FLAGEOLETS: ["Légumes secs, sous-vide"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Lentilles et légumes secs"],
    CategoryValues.HARICOTS_BLANCS: ["Légumes secs"],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: ["Lentilles et légumes secs"],
    CategoryValues.HARICOTS_NOIRS_CONSERVE: [
        "Epicerie espagnole et portugaise",
        "Lentilles et légumes secs",
    ],
    CategoryValues.HARICOTS_ROUGES_CONSERVE: ["Lentilles et légumes secs"],
    CategoryValues.LENTILLES_BLONDES: ["Légumes secs"],
    CategoryValues.LENTILLES_CORAIL: ["Légumes secs"],
    CategoryValues.LENTILLES_VERTES: ["Légumes secs, sous-vide", "Légumes secs"],
    CategoryValues.LENTILLES_VERTES_CONSERVE: ["Lentilles et légumes secs"],
    CategoryValues.POIS_CASSES: ["Légumes secs"],
    CategoryValues.POIS_CHICHES: ["Légumes secs"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Lentilles et légumes secs"],
    CategoryValues.AMANDES: [
        "Fruits séchés et Fruits secs",
        "Fruits secs, aide à la pâtisserie",
    ],
    CategoryValues.BEURRE_DE_CACAHUETE: ["Pâte à tartiner, crème de marrons"],
    CategoryValues.CACAHUETES: ["Cacahuètes, pistaches et noix de cajou"],
    CategoryValues.GRAINES_CHIA: [
        "Fruits séchés et Fruits secs",
        "Sucre, farine, pâtisserie bio",
    ],
    CategoryValues.GRAINES_COURGE: [
        "Amandes, noisettes et mélanges",
        "Sucre, farine, pâtisserie bio",
    ],
    CategoryValues.GRAINES_TOURNESOL: [
        "Fruits et légumes bio",
        "Epicerie espagnole et portugaise",
        "Fruits séchés et Fruits secs",
    ],
    CategoryValues.NOISETTES: [
        "Fruits séchés et Fruits secs",
        "Fruits secs, aide à la pâtisserie",
    ],
    CategoryValues.NOIX_CAJOUS: [
        "Fruits séchés et Fruits secs",
        "Cacahuètes, pistaches et noix de cajou",
    ],
    CategoryValues.PIGNONS_PIN: ["Fruits séchés et Fruits secs"],
    CategoryValues.PISTACHES: ["Cacahuètes, pistaches et noix de cajou"],
    CategoryValues.BRIE: ["Camemberts, coulommiers et bries", "Fromages à la coupe"],
    CategoryValues.BUCHE_DE_CHEVRE: ["Chèvres et brebis"],
    CategoryValues.CAMEMBERT: ["Camemberts, coulommiers et bries"],
    CategoryValues.COMTE: ["Comté, emmental, gouda et autres", "Fromages à la coupe"],
    CategoryValues.COULOMMIERS: ["Camemberts, coulommiers et bries"],
    CategoryValues.EMMENTAL: [
        "Comté, emmental, gouda et autres",
        "Fromages à la coupe",
    ],
    CategoryValues.FETA: ["Mozzarella et burrata, feta, mascarpone"],
    CategoryValues.FROMAGE_BLANC: ["Yaourts et fromages blancs natures"],
    CategoryValues.FROMAGE_RACLETTE: [
        "Raclette, tartiflette et fondue",
        "Fromages à la coupe",
    ],
    CategoryValues.LAIT_DEMI_ECREME: [
        "Laits demi-écrémés",
        "Laits bio",
        "Laits sans lactose",
    ],
    CategoryValues.LAIT_ENTIER: ["Laits entiers", "Laits bio"],
    CategoryValues.MOZZARELLA: ["Mozzarella et burrata, feta, mascarpone"],
    CategoryValues.OEUFS: ["Oeufs"],
    CategoryValues.PARMESAN_RAPE: ["Fromages râpés et parmesan"],
    CategoryValues.PETITS_SUISSES: ["Yaourts et fromages blancs natures"],
    CategoryValues.ROQUEFORT: ["Roquefort et bleu"],
    CategoryValues.SKYR: ["Skyr, bien-être et 0%"],
    CategoryValues.YAOURT_NATURE_0: ["Skyr, bien-être et 0%"],
    CategoryValues.ANCHOIS: ["Anchois, harengs et rollmops"],
    CategoryValues.CABILLAUD: ["Filets, pavés et poissons entiers", "Poissons natures"],
    CategoryValues.COLIN_PANE: ["Panés", "Poissons panés"],
    CategoryValues.CREVETTES: ["Fruits de mer, crustacés"],
    CategoryValues.LIMANDE: ["Panés", "Poissons natures"],
    CategoryValues.MAQUEREAU_CONSERVE: ["Maquereaux"],
    CategoryValues.MAQUEREAU_FRAIS: ["Saumons et poissons fumés"],
    CategoryValues.NOIX_DE_SAINT_JACQUES: [
        "Crevettes, coquillages et crustacés",
        "Fruits de mer, crustacés",
    ],
    CategoryValues.SARDINES: ["Sardines"],
    CategoryValues.SAUMON: [
        "Filets et pavés",
        "Filets, pavés et poissons entiers",
        "Poissons natures",
    ],
    CategoryValues.SAUMON_FUME: ["Saumons et poissons fumés"],
    CategoryValues.SURIMI: ["Surimis"],
    CategoryValues.THON: ["Thon"],
    CategoryValues.TRUITE_FUMEE: ["Saumons et poissons fumés"],
    CategoryValues.BARRES_PROTEINEES: ["Minceur et sport"],
    CategoryValues.ISOLAT_WHEY: ["Minceur et sport"],
    CategoryValues.PROTEINES_VEGETALES_POUDRE: ["Minceur et sport"],
    CategoryValues.PROTEINES_SOJA_TEXTUREES: ["Légumes secs, sous-vide"],
    CategoryValues.TOFU_FUME: ["Plats cuisinés bio", "Végétal"],
    CategoryValues.TOFU_NATURE: ["Végétal", "Plats cuisinés bio"],
    CategoryValues.BLANC_DE_DINDE_TRANCHES: ["Jambon et roti de volaille"],
    CategoryValues.CHIPOLATAS: ["Saucisse, paupiette et farce"],
    CategoryValues.CONFIT_DE_CANARD: [
        "Canard et Lapin",
        "Cassoulets, confits, choucroutes",
    ],
    CategoryValues.CORDON_BLEU: [
        "Panés, nuggets, grignottes",
        "Volailles, panés de volailles, autres",
    ],
    CategoryValues.COTES_AGNEAU: ["Veau, agneau et abat"],
    CategoryValues.COTES_DE_PORC: ["Porc"],
    CategoryValues.CUISSE_POULET: ["Poulet"],
    CategoryValues.ENTRECOTE_BOEUF: ["Boeuf"],
    CategoryValues.ESCALOPES_DE_DINDE: ["Dinde"],
    CategoryValues.ESCALOPE_DE_VEAU: ["Veau, agneau et abat"],
    CategoryValues.FILET_MIGNON_DE_PORC: ["Porc"],
    CategoryValues.GIGOT_AGNEAU: [
        "Veau, agneau et abat",
        "Volailles, panés de volailles, autres",
    ],
    CategoryValues.JAMBON_BLANC: ["Jambon blanc et rôti"],
    CategoryValues.JAMBON_CRU: ["Jambon cru et sec"],
    CategoryValues.LAPIN: ["Canard et Lapin"],
    CategoryValues.LARDONS: ["Lardon, dés, poitrine"],
    CategoryValues.MAGRET_DE_CANARD: ["Canard et Lapin"],
    CategoryValues.MERGUEZ: ["Saucisse, paupiette et farce"],
    CategoryValues.NUGGETS: [
        "Panés, nuggets, grignottes",
        "Volailles, panés de volailles, autres",
    ],
    CategoryValues.POITRINE_FUMEE_BACON: ["Lardon, dés, poitrine"],
    CategoryValues.POULET_FERMIER: ["Poulet"],
    CategoryValues.POULET_FILET: ["Poulet"],
    CategoryValues.RILLETTES: ["Pâté, rillette, foie gras", "Pâtés, foie gras"],
    CategoryValues.ROTI_DE_BOEUF: ["Boeuf"],
    CategoryValues.ROTI_DE_PORC: ["Jambon blanc, viande cuite"],
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: [
        "Knack, saucisse, boudin, saucisson cuit"
    ],
    CategoryValues.SAUCISSON_SEC: ["Saucisson sec, chorizo"],
    CategoryValues.SAUTE_DE_VEAU: ["Veau, agneau et abat"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Viande hachée", "Steaks, viandes hachées"],
}


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    CHARCUTERIE = "Charcuterie, traiteur"
    EPICERIE = "Epicerie salée"
    FRAIS = "Marché frais"
    FRUITS_LEGUMES = "Fruits et Légumes"
    OEUFS_PRODUITS_LAITIERS = "Produits laitiers, oeufs et fromages"
    SUCRE = "Epicerie sucrée"
    SURGELES = "Surgelés"
    VIANDES = "Viandes, poissons"

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


class SuperUProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Super U retail website.
    """

    name = "super_u_products"
    allowed_domains = ["www.coursesu.com"]

    custom_settings = {}

    current_page = 0
    query: str
    url: str

    def __get_next_page(self) -> str:
        """
        Returns the next URL to visit while incrementing the current page index.
        """

        self.current_page += 1
        self.url = f"https://www.coursesu.com/recherche?q={self.query}&page={self.current_page}"

        self.logger.debug(f"Next page set to {self.current_page}")

        return self.url

    async def start(self):
        query = getattr(self, "query", None)
        store_id = getattr(self, "store_id", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")
        if store_id is None:
            raise AttributeError("Missing 'store_id' argument")

        self.query = query

        yield Request(
            url=self.__get_next_page(),
            cookies={STORE_COOKIE_NAME: store_id},
            meta={"impersonate": "chrome119"},
            callback=self.parse,
        )

    def parse(self, response: Response):
        product_links = response.css("a.product-tile-link")
        yield from response.follow_all(
            product_links,
            meta={"impersonate": "chrome119"},
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
        breadcrumbs = response.xpath(
            "//li[@class='breadcrumb-element']/a/span/text()"
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

        microdata_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        product_data = [
            json.loads(data) for data in microdata_content if "Product" in data
        ]

        return product_data.pop()

    def get_name(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["name"]

    def get_brand(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["brand"]["name"]

    def get_ean13(self, response: Response) -> str | None:
        product_info = self.__get_product_info(response)

        return product_info["sku"]

    @staticmethod
    def extract_discount_and_prices(
        response: Response,
    ) -> tuple[bool, float, float | None] | None:
        """
        Extracts whether or not the product is discounted and its both prices
        (normal and discounted) from the response.

        Returns None if no price can be found.
        """

        current_product = response.css(".product-columns")

        current_price = current_product.xpath(
            ".//span[has-class('sale-price')]/@data-item-price"
        ).get()
        if current_price is None:
            return

        is_discounted = (
            current_product.xpath(".//span[has-class('discount')]").get() is not None
        )

        if is_discounted:
            base_price = current_product.xpath(
                ".//span[@class='pdp-standard-price-value']/text()"
            ).get()
            base_price = float(base_price.replace("€", "").replace(",", ".").strip())
            current_price = float(current_price)
            if current_price == base_price:
                is_discounted = False
        else:
            base_price = float(current_price)

        return (
            is_discounted,
            base_price,
            current_price if is_discounted else None,
        )

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        poids_net = response.xpath(
            '//p[@class="pdp-description-text"]/text()'
        ).re_first(r"Poids net: (.+)")

        if poids_net is None:
            return

        raw_quantity = poids_net.split()[0]
        quantity = float(raw_quantity.replace(",", "."))

        raw_quantity_unit = poids_net.split()[1]

        match raw_quantity_unit.lower():
            case "kg":
                quantity_unit = QuantityUnit.KILOGRAM
            case "g":
                quantity = quantity / 1000
                quantity_unit = QuantityUnit.KILOGRAM

        return (quantity, quantity_unit)
