from collections.abc import Generator
from enum import StrEnum, unique
from re import IGNORECASE, match

from scrapy import Request, Spider
from scrapy.http import Response

from models.category import CategoryValues
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

# Mapping between categories and departments.
CAT_DEPT_MAPPING = {
    CategoryValues.AIGUILLETTES_VEGETALES: ["Simili-carnés, tofu"],
    CategoryValues.BASTONETS_POISSON_VEGETAUX: ["Simili-carnés, tofu"],
    CategoryValues.BASTONETS_POISSON_VEGETAUX_CONSERVE: ["Simili-carnés, tofu"],
    CategoryValues.BOULETTES_VEGETALES: ["Simili-carnés, tofu"],
    CategoryValues.BOULETTES_VEGETALES_SURGELE: ["Surgelés"],
    CategoryValues.ESCALOPES_VEGETALES_PANEES: ["Simili-carnés, tofu"],
    CategoryValues.GALETTE_VEGETALE_CEREALES: ["Simili-carnés, tofu"],
    CategoryValues.GALETTE_VEGETALE_CEREALES_SURGELE: ["Surgelés"],
    CategoryValues.JAMBON_VEGETAL: ["Simili-carnés, tofu"],
    CategoryValues.KNAX_VEGETALES: ["Simili-carnés, tofu"],
    CategoryValues.LARDONS_VEGETAUX: ["Simili-carnés, tofu"],
    CategoryValues.NUGGETS_VEGETAUX: ["Simili-carnés, tofu"],
    CategoryValues.NUGGETS_VEGETAUX_SURGELE: ["Surgelés"],
    CategoryValues.SAUCISSES_VEGETALES: ["Simili-carnés, tofu"],
    CategoryValues.SIMILI_THON: ["Traiteur végétal"],
    CategoryValues.STEAK_VEGETAL: ["Simili-carnés, tofu"],
    CategoryValues.STEAK_VEGETAL_SURGELE: ["Surgelés"],
    CategoryValues.SUPREME_FAUX_POULET: ["Simili-carnés, tofu"],
    CategoryValues.FLOCON_DAVOINE: ["Céréales adultes"],
    CategoryValues.QUINOA: ["Céréales, galettes, quinoa"],
    CategoryValues.SARRASIN: ["Lentilles, légumes secs"],
    CategoryValues.FALAFELS: ["Traiteur végétal"],
    CategoryValues.FALAFELS_POUDRE: ["Chapelure, fécule"],
    CategoryValues.FEVES: ["Autres légumes", "Mono légumes surgelés"],
    CategoryValues.FLAGEOLETS: ["Légumes secs, graines", "Lentilles, légumes secs"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Flageolets", "Mono légumes surgelés"],
    CategoryValues.GALETTES_DE_LEGUMINEUSES: ["Céréales, légumineuses"],
    CategoryValues.HARICOTS_BLANCS: [
        "Légumes secs, graines",
        "Lentilles, légumes secs",
    ],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: [
        "Haricots blancs",
        "Mono légumes surgelés",
    ],
    CategoryValues.HARICOTS_NOIRS: ["Légumes secs, graines", "Lentilles, légumes secs"],
    CategoryValues.HARICOTS_NOIRS_CONSERVE: ["Haricots rouge", "Mono légumes surgelés"],
    CategoryValues.HARICOTS_ROUGES: [
        "Légumes secs, graines",
        "Lentilles, légumes secs",
    ],
    CategoryValues.HARICOTS_ROUGES_CONSERVE: [
        "Haricots rouge",
        "Mono légumes surgelés",
    ],
    CategoryValues.LENTILLES_BLONDES: [
        "Légumes secs, graines",
        "Lentilles, légumes secs",
    ],
    CategoryValues.LENTILLES_BLONDES_CONSERVE: ["Lentilles"],
    CategoryValues.LENTILLES_CORAIL: [
        "Légumes secs, graines",
        "Lentilles, légumes secs",
    ],
    CategoryValues.LENTILLES_VERTES: [
        "Lentilles, légumes secs",
        "Légumes secs, graines",
    ],
    CategoryValues.LENTILLES_VERTES_CONSERVE: ["Lentilles", "Mono légumes surgelés"],
    CategoryValues.LUPIN: ["Autres légumes"],
    CategoryValues.POIS_CASSES: ["Légumes secs, graines", "Lentilles, légumes secs"],
    CategoryValues.POIS_CHICHES: ["Légumes secs, graines", "Lentilles, légumes secs"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Pois chiches"],
    CategoryValues.AMANDES: ["Amandes"],
    CategoryValues.BEURRE_DE_CACAHUETE: ["Pâtes à tartiner"],
    CategoryValues.CACAHUETES: ["Cacahuètes"],
    CategoryValues.GRANES_CHIA: ["Mélanges, graines, fruits exotiques"],
    CategoryValues.GRANES_COURGE: ["Mélanges, graines, fruits exotiques"],
    CategoryValues.GRANES_LIN: ["Mélanges, graines, fruits exotiques"],
    CategoryValues.GRANES_TOURNESOL: ["Mélanges, graines, fruits exotiques"],
    CategoryValues.NOISETTES: ["Noix, noisettes"],
    CategoryValues.NOIX_CAJOUS: ["Noix de cajou"],
    CategoryValues.PIGNONS_PIN: [
        "Légumes secs, graines",
        "Mélanges, graines, fruits exotiques",
    ],
    CategoryValues.PISTACHES: ["Pistaches"],
    CategoryValues.BRIE: ["Brie", "Brie, bleu, fromage crémeux"],
    CategoryValues.BUCHE_DE_CHEVRE: ["Fromages de chèvre"],
    CategoryValues.CAMEMBERT: ["Camembert"],
    CategoryValues.COMTE: [
        "Emmental, Gruyère, Comté",
        "Emmental, Comté, Parmesan, Mimolette",
    ],
    CategoryValues.COULOMMIERS: ["Coulommiers"],
    CategoryValues.EMMENTAL: ["Emmental, Gruyère, Comté"],
    CategoryValues.FETA: ["Fêta, fromages de brebis"],
    CategoryValues.FROMAGE_BLANC: ["Fromages blancs"],
    CategoryValues.FROMAGE_RACLETTE: ["Raclette"],
    CategoryValues.LAIT_DEMI_ECREME: ["Lait demi-écrémé"],
    CategoryValues.LAIT_ENTIER: ["Lait entier"],
    CategoryValues.MOZZARELLA: ["Mozzarella"],
    CategoryValues.OEUFS: ["Oeufs de plein air", "Oeufs standards"],
    CategoryValues.PARMESAN_RAPE: ["Parmesan, grana padano râpés"],
    CategoryValues.PETITS_SUISSES: ["Petits suisses"],
    CategoryValues.ROQUEFORT: ["Roquefort", "Brie, bleu, fromage crémeux"],
    CategoryValues.SKYR: ["Skyr"],
    CategoryValues.YAOURT_NATURE_0: ["Yaourts nature", "Yaourts au bifidus, bien-être"],
    CategoryValues.ANCHOIS: ["Anchois, harengs, apéritifs de la mer"],
    CategoryValues.CABILLAUD: ["Cabillaud, merlan", "Surgelés"],
    CategoryValues.COLIN_PANE: ["Poissons panés, plats préparés", "Surgelés"],
    CategoryValues.CREVETTES: ["Crevettes, crustacés", "Surgelés"],
    CategoryValues.LIMANDE: ["Autres poissons", "Surgelés"],
    CategoryValues.MAQUEREAU_CONSERVE: ["Maquereaux"],
    CategoryValues.MAQUEREAU_FRAIS: ["Marée du jour", "Autres poissons"],
    CategoryValues.NOIX_DE_SAINT_JACQUES: ["Marée du jour", "Surgelés"],
    CategoryValues.SARDINES: ["Sardines"],
    CategoryValues.SARDINES_FRAICHES: ["Marée du jour", "Surgelés"],
    CategoryValues.SAUMON: ["Marée du jour", "Saumon, truite", "Surgelés"],
    CategoryValues.SAUMON_FUME: ["Saumon fumé"],
    CategoryValues.SURIMI: ["Surimi, bâtonnets"],
    CategoryValues.THON: ["Thon"],
    CategoryValues.THON_FRAIS: ["Marée du jour"],
    CategoryValues.TRUITE_FUMEE: ["Truite fumée"],
    CategoryValues.BARRES_PROTEINEES: ["Barres de céréales"],
    CategoryValues.ISOLAT_WHEY: ["Nutrition sportive"],
    CategoryValues.PROTEINES_VEGETALES_POUDRE: ["Nutrition sportive"],
    CategoryValues.TOFU_FUME: ["Simili-carnés, tofu"],
    CategoryValues.TOFU_NATURE: ["Simili-carnés, tofu"],
    CategoryValues.AIGUILLETTES_DINDE: ["Dinde"],
    CategoryValues.BLANC_DE_DINDE_TRANCHES: ["Blanc de dinde"],
    CategoryValues.CHIPOLATAS: ["Chipolatas, saucisses barbecue"],
    CategoryValues.CONFIT_DE_CANARD: ["Canard", "Confits, gésiers"],
    CategoryValues.CORDON_BLEU: ["Cordons bleus, panés", "Surgelés"],
    CategoryValues.COTES_AGNEAU: ["Agneau"],
    CategoryValues.COTES_DE_PORC: ["Porc", "Surgelés"],
    CategoryValues.CUISSE_POULET: ["Cuisses, pilons, ailes", "Surgelés"],
    CategoryValues.ENTRECOTE_BOEUF: ["Boeuf"],
    CategoryValues.ESCALOPES_DE_DINDE: ["Dinde"],
    CategoryValues.ESCALOPE_DE_VEAU: ["Veau"],
    CategoryValues.FILET_MIGNON_DE_PORC: ["Porc"],
    CategoryValues.GIGOT_AGNEAU: ["Agneau"],
    CategoryValues.JAMBON_BLANC: ["Jambon blanc", "Jambon, rôti"],
    CategoryValues.JAMBON_CRU: [
        "Jambon cru, charcuterie en tranche",
        "Jambon cru, sec, fumé",
    ],
    CategoryValues.LAPIN: ["Lapins"],
    CategoryValues.LARDONS: ["Lardons"],
    CategoryValues.MAGRET_DE_CANARD: ["Canard"],
    CategoryValues.MERGUEZ: ["Merguez", "Barbecue, saucisses, brochettes"],
    CategoryValues.NUGGETS: ["Nuggets", "Surgelés"],
    CategoryValues.POITRINE_FUMEE_BACON: ["Bacon, poitrine"],
    CategoryValues.POULET_FERMIER: ["Poulets entiers"],
    CategoryValues.POULET_FILET: ["Escalopes, filets, aiguilettes", "Surgelés"],
    CategoryValues.RILLETTES: ["Rillettes"],
    CategoryValues.ROTI_DE_BOEUF: ["Boeuf"],
    CategoryValues.ROTI_DE_PORC: ["Porc", "Rôti"],
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: ["Knacks, saucisses"],
    CategoryValues.SAUCISSON_SEC: ["Saucisson sec entier"],
    CategoryValues.SAUTE_DE_VEAU: ["Veau"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Steaks hachés", "Surgelés"],
}


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

        if self.get_category() == "Œufs":
            url = "https://www.auchan.fr/oeufs-produits-laitiers/cremerie-oeufs-laits/oeufs/ca-n010103?page=1"
        else:
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
            self.logger.debug(f"Next button detected: {next_button}")

            yield from response.follow_all(
                css="a.pagination-adjacent__link::attr(href)", callback=self.parse
            )

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        if not self.is_relevant(response):
            self.logger.info("Product is irrelevant. Skipping...")
            return

        item["name"] = self.get_name(response)
        item["brand"] = self.get_brand(response)
        item["category"] = self.get_category()
        item["url"] = response.url

        eans = self.get_ean13s(response)

        if eans is None:
            self.logger.info("No EAN found. Skipping...")
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
            self.logger.info(f"Product {item['eans'][0]} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = response.xpath(
            "//span[@class='site-breadcrumb__item']/a/text()"
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

    def get_ean13s(self, response: Response) -> list[str] | None:
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
        Extracts whether or not the product is discounted and its both prices
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

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        product_attributes = response.css(
            ".offer-selector__attributes span.product-attribute"
        )

        for product_attribute in product_attributes:
            m = match(
                "Contenance : (\\d+x)?([.,0-9]+) ?(ml|cl|L|kg|g|œufs|pièces)",
                product_attribute.attrib["aria-label"],
                IGNORECASE,
            )

            if m is not None:
                multiplier = m.group(1)  # None or 2x, 6x
                raw_quantity = m.group(2)  # 200, 1,5
                raw_quantity_unit = m.group(3)  # g, kg, L, l, cl, ml

                quantity = float(raw_quantity.replace(",", "."))

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
                    case "pièces" | "œufs":
                        quantity_unit = QuantityUnit.PIECE
                        if self.get_category() == CategoryValues.OEUFS:
                            item_name = self.get_name(response)
                            eggs_num = quantity
                            quantity, quantity_unit = self.compute_eggs_weight(
                                eggs_num, item_name
                            )
                            self.logger.info(
                                f"Converted eggs quantity {int(eggs_num)} to weight {quantity} kg..."
                            )
                    case _:
                        return

                if multiplier is None:
                    return (quantity, quantity_unit)
                else:
                    nb = int("".join(filter(str.isdigit, multiplier)))
                    return (quantity * nb, quantity_unit)
