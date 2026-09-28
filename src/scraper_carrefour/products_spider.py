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
    CategoryValues.AIGUILLETTES_VEGETALES: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.BASTONETS_POISSON_VEGETAUX: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.BOULETTES_VEGETALES: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.ESCALOPES_VEGETALES_PANEES: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.GALETTE_VEGETALE_CEREALES: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.JAMBON_VEGETAL: ["Charcuterie végétale"],
    CategoryValues.KNAX_VEGETALES: ["Charcuterie végétale"],
    CategoryValues.LARDONS_VEGETAUX: ["Charcuterie végétale"],
    CategoryValues.NUGGETS_VEGETAUX: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.SAUCISSES_VEGETALES: ["Charcuterie végétale"],
    CategoryValues.STEAK_VEGETAL: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.SUPREME_FAUX_POULET: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.FLOCON_DAVOINE: ["Mueslis et Avoines", "Céréales adultes"],
    CategoryValues.QUINOA: ["Quinoa, Boulgour et Céréales"],
    CategoryValues.SARRASIN: ["Quinoa, Boulgour et Céréales"],
    CategoryValues.SEITAN: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.FALAFELS: ["Steaks, Panés et Galettes végétales"],
    CategoryValues.FEVES: ["Lentilles et Légumes secs", "Légumes natures"],
    CategoryValues.FLAGEOLETS: ["Flageolets"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Flageolets"],
    CategoryValues.GALETTES_DE_LEGUMINEUSES: ["Traiteur"],
    CategoryValues.HARICOTS_BLANCS: ["Lentilles et Légumes secs"],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: ["Haricots blancs"],
    CategoryValues.HARICOTS_NOIRS: ["Lentilles et Légumes secs"],
    CategoryValues.HARICOTS_NOIRS_CONSERVE: ["Haricots rouges"],
    CategoryValues.HARICOTS_ROUGES: ["Haricots rouges"],
    CategoryValues.HARICOTS_ROUGES_CONSERVE: ["Haricots rouges"],
    CategoryValues.LENTILLES_BLONDES: ["Lentilles et Légumes secs"],
    CategoryValues.LENTILLES_CORAIL: ["Lentilles et Légumes secs"],
    CategoryValues.LENTILLES_VERTES: ["Lentilles et Légumes secs"],
    CategoryValues.LENTILLES_VERTES_CONSERVE: [
        "Lentilles",
        "Lentilles et Légumes secs",
    ],
    CategoryValues.POIS_CASSES: ["Lentilles et Légumes secs"],
    CategoryValues.POIS_CHICHES: ["Lentilles et Légumes secs"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Pois chiche"],
    CategoryValues.AMANDES: ["Légumes et Fruits secs"],
    CategoryValues.BEURRE_DE_CACAHUETE: [
        "Pâtes à tartiner et Crèmes",
        "Pâtes à tartiner, Confitures et Miels",
    ],
    CategoryValues.CACAHUETES: ["Cacahuètes"],
    CategoryValues.GRANES_CHIA: ["Graines"],
    CategoryValues.GRANES_COURGE: ["Graines"],
    CategoryValues.GRANES_LIN: ["Graines"],
    CategoryValues.GRANES_TOURNESOL: ["Graines"],
    CategoryValues.NOISETTES: [
        "Pistaches, Noix de cajou et Amandes",
        "Fruits secs et mélanges",
        "Fruits secs et Fruits confits",
    ],
    CategoryValues.NOIX_CAJOUS: [
        "Pistaches, Noix de cajou et Amandes",
        "Graines",
        "Fruits secs et mélanges",
    ],
    CategoryValues.PIGNONS_PIN: [
        "Fruits secs et Fruits confits",
        "Légumes et Fruits secs",
        "Fruits secs et mélanges",
    ],
    CategoryValues.PISTACHES: [
        "Pistaches, Noix de cajou et Amandes",
        "Fruits secs et mélanges",
    ],
    CategoryValues.BRIE: ["Brie"],
    CategoryValues.BUCHE_DE_CHEVRE: [
        "Bûches et Fromage de chèvre",
    ],
    CategoryValues.CAMEMBERT: ["Camembert"],
    CategoryValues.COMTE: ["Comté"],
    CategoryValues.COULOMMIERS: ["Coulommiers"],
    CategoryValues.EMMENTAL: ["Emmental"],
    CategoryValues.FETA: ["Feta"],
    CategoryValues.FROMAGE_BLANC: [
        "Fromages blancs allégés et 0%",
        "Fromages blancs natures",
    ],
    CategoryValues.FROMAGE_RACLETTE: ["Raclette"],
    CategoryValues.LAIT_DEMI_ECREME: ["Lait demi-écrémé", "Lait et Oeufs"],
    CategoryValues.LAIT_ENTIER: ["Lait entier", "Lait et Oeufs"],
    CategoryValues.MOZZARELLA: ["Mozzarella"],
    CategoryValues.OEUFS: ["Œufs"],
    CategoryValues.PARMESAN_RAPE: [
        "Fromages râpés et parmesans",
        "Parmesan et Gorgonzola",
    ],
    CategoryValues.PETITS_SUISSES: ["Petits suisses et Yaourts enfants"],
    CategoryValues.ROQUEFORT: ["Roquefort"],
    CategoryValues.SKYR: ["Yaourts allégés, 0% et Skyrs"],
    CategoryValues.YAOURT_NATURE_0: ["Yaourts allégés, 0% et Skyrs", "Yaourts natures"],
    CategoryValues.ANCHOIS: ["Poissons fumés"],
    CategoryValues.CABILLAUD: ["Cabillaud et Poissons blancs", "Poissons natures"],
    CategoryValues.COLIN_PANE: [
        "Poissons panés",
        "Poissons panés et cuisinés",
    ],
    CategoryValues.CREVETTES: ["Crevettes et Crustacés", "Fruits de mer et Crustacés"],
    CategoryValues.LIMANDE: ["Poissons panés et cuisinés", "Poissons panés"],
    CategoryValues.MAQUEREAU_CONSERVE: ["Maquereaux"],
    CategoryValues.MAQUEREAU_FRAIS: ["Poissons entiers"],
    CategoryValues.NOIX_DE_SAINT_JACQUES: [
        "Coquillages et crustacés",
        "Moules et Coquillages",
        "Fruits de mer et Crustacés",
    ],
    CategoryValues.SARDINES: ["Sardines"],
    CategoryValues.SARDINES_FRAICHES: [
        "Brochettes et Grillades poisson",
        "Poissons entiers",
        "Filets et pavés",
    ],
    CategoryValues.SAUMON: ["Saumons et Truites", "Poissons natures"],
    CategoryValues.SAUMON_FUME: ["Saumons fumés"],
    CategoryValues.SURIMI: ["Surimis"],
    CategoryValues.THON: ["Thon"],
    CategoryValues.THON_FRAIS: [
        "Brochettes et Grillades poisson",
        "Cabillaud et Poissons blancs",
    ],
    CategoryValues.TRUITE_FUMEE: ["Truites fumées"],
    CategoryValues.BARRES_PROTEINEES: ["Nutrition et Protéine"],
    CategoryValues.CASEINE: ["Hydratation et Poudres"],
    CategoryValues.ISOLAT_WHEY: ["Hydratation et Poudres"],
    CategoryValues.PROTEINES_VEGETALES_POUDRE: ["Hydratation et Poudres"],
    CategoryValues.PROTEINES_SOJA_TEXTUREES: [
        "Lentilles et Légumes secs",
        "Quinoa, Boulgour et Céréales",
    ],
    CategoryValues.TEMPEH: ["Tofu"],
    CategoryValues.TOFU_FUME: ["Tofu", "Steaks, Panés et Galettes végétales"],
    CategoryValues.TOFU_NATURE: ["Tofu"],
    CategoryValues.AIGUILLETTES_DINDE: ["Dindes"],
    CategoryValues.BLANC_DE_DINDE_TRANCHES: ["Blanc de dinde"],
    CategoryValues.CHIPOLATAS: ["Chipolatas et Saucisses"],
    CategoryValues.CONFIT_DE_CANARD: ["Cassoulets et Confits", "Canard"],
    CategoryValues.CORDON_BLEU: ["Cordons bleus", "Volailles panées et volailles"],
    CategoryValues.COTES_AGNEAU: ["Agneau"],
    CategoryValues.COTES_DE_PORC: ["Porc", "Grillades et Brochettes", "Grands formats"],
    CategoryValues.CUISSE_POULET: ["Cuisses et Ailes"],
    CategoryValues.ENTRECOTE_BOEUF: ["Boeuf", "Boucherie et Poissonnerie"],
    CategoryValues.ESCALOPES_DE_DINDE: ["Dindes"],
    CategoryValues.ESCALOPE_DE_VEAU: ["Veau"],
    CategoryValues.FILET_MIGNON_DE_PORC: ["Porc"],
    CategoryValues.GIGOT_AGNEAU: ["Agneau"],
    CategoryValues.JAMBON_BLANC: ["Jambons blancs"],
    CategoryValues.JAMBON_CRU: ["Jambons crus et secs"],
    CategoryValues.LAPIN: ["Lapin"],
    CategoryValues.LARDONS: ["Lardons"],
    CategoryValues.MAGRET_DE_CANARD: ["Canard"],
    CategoryValues.MERGUEZ: ["Merguez"],
    CategoryValues.NUGGETS: ["Nuggets et Tenders", "Volailles panées et volailles"],
    CategoryValues.POITRINE_FUMEE_BACON: [
        "Jambons crus et Charcuteries tranchées",
        "Bacon et Poitrines",
        "Bacon, Rosette et Salami",
    ],
    CategoryValues.POULET_FERMIER: ["Poulets entiers"],
    CategoryValues.POULET_FILET: ["Filets et Aiguillettes"],
    CategoryValues.RILLETTES: ["Rillettes"],
    CategoryValues.ROTI_DE_BOEUF: ["Boeuf"],
    CategoryValues.ROTI_DE_PORC: ["Porc", "Rôtis"],
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: ["Knacks"],
    CategoryValues.SAUCISSON_SEC: [
        "Charcuterie apéritive",
        "Saucissons et Fuets",
    ],
    CategoryValues.SAUTE_DE_VEAU: ["Veau"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Steaks hachés"],
}


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    CHARCUTERIE = "Charcuterie et Traiteur"
    EPICERIE = "Epicerie salée"
    FRUITS_LEGUMES = "Fruits et Légumes"
    OEUFS_PRODUITS_LAITIERS = "Crèmerie et Produits laitiers"
    SUCRE = "Epicerie sucrée"
    SURGELE = "Surgelés"
    VEGETAL = "Nutrition et Végétale"
    VIANDES_POISSONS = "Viandes et Poissons"

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


class CarrefourProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Carrefour retail website.
    """

    name = "carrefour_products"
    allowed_domains = ["www.carrefour.fr"]

    custom_settings = {}

    current_page = 0
    query: str
    url: str

    def __get_next_page(self) -> str:
        """
        Returns the next URL to visit while incrementing the current page index.
        """

        self.current_page += 1
        self.url = f"https://www.carrefour.fr/s?filters[facet_enseignes][0]=Drive ou livraison à domicile&q={self.query}&page={self.current_page}"

        self.logger.debug(f"Next page set to {self.current_page}")

        return self.url

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        self.query = query

        yield Request(
            url=self.__get_next_page(),
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
            callback=self.parse,
        )

    def parse(self, response: Response):
        product_links = response.xpath(
            "//li[@class='product-list-grid__item']/article/div/div/div/a[contains(@class, 'product-card-click-wrapper')]/@href"
        ).getall()
        yield from response.follow_all(
            product_links, meta={"playwright": True}, callback=self.parse_product
        )

        next_button = response.xpath(
            "//button[@aria-label='Afficher les produits suivants']"
        ).get()

        if next_button is not None:
            self.logger.debug("Next button detected")

            yield Request(
                url=self.__get_next_page(),
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

        base_price = float(
            response.css("script::text").re_first(r'"product_basePrice":([.0-9]+)')
        )
        current_price = float(
            response.css("script::text").re_first(r'"product_price":([.0-9]+)')
        )
        discounted = base_price - current_price > 0
        item["price"] = base_price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = current_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.logger.info(f"Product {item['ean']} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        self.logger.debug(f"Product cache info: {self.__get_product_info.cache_info()}")

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = [
            s.strip()
            for s in response.xpath(
                "//li[contains(@class, 'c-breadcrumbs__breadcrumb')]/a/text()"
            ).getall()
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

    def get_ean13(self, response: Response) -> str:
        product_info = self.__get_product_info(response)

        return product_info["gtin13"]

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.

        Examples:
        la barquette de 2x90 g (par pièce)
        la barquette de 2 cuisses - 450g (total)
        les 20 saucisses 700 g (total)
        les 2 galettes de 100g (par pièce)
        le paquet de 320g de 12 (total)
        la barquette de 200g - 18 pièces
        """

        product_info = self.__get_product_info(response)
        quantity_text = product_info["description"]

        m = re.match("(.+) ([,.0-9]+) ?(ml|cl|L|kg|g)?", quantity_text, re.IGNORECASE)

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
                case _:
                    return

        # check if packaging text contains total: Les 2 briques de 30cl - 60cl
        # sometimes not: les 6 briques de 1 l
        is_separator = quantity_text.find("-")
        if is_separator > 0:
            self.logger.info(
                f"Quantity found: {quantity_text} / extracted: {quantity}{quantity_unit}"
            )
            return (quantity, quantity_unit)
        else:
            nb = int("".join(filter(str.isdigit, raw_multiplier)) or 1)
            self.logger.info(
                f"Quantity found: {quantity_text} / extracted: {quantity * nb}{quantity_unit}"
            )
            return (quantity * nb, quantity_unit)
