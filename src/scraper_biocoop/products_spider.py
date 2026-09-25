import re
from collections.abc import Generator
from enum import StrEnum, unique

from scrapy import Request, Spider
from scrapy.http import Response

from models.category import CategoryValues
from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider

# Mapping between categories and departments.
CAT_DEPT_MAPPING = {
    CategoryValues.ESCALOPES_VEGETALES_PANEES: ["Spécialités végétales"],
    CategoryValues.FALAFELS: ["Traiteur végétal"],
    CategoryValues.GALETTE_VEGETALE_CEREALES: ["Traiteur végétal"],
    CategoryValues.JAMBON_VEGETAL: ["Spécialités végétales"],
    CategoryValues.KNAX_VEGETALES: ["Spécialités végétales"],
    CategoryValues.NUGGETS_VEGETAUX: ["Spécialités végétales"],
    CategoryValues.SAUCISSES_VEGETALES: ["Spécialités végétales"],
    CategoryValues.STEAK_VEGETAL: ["Spécialités végétales"],
    CategoryValues.BLE_COMPLET: ["Quinoa, boulghour, céréales"],
    CategoryValues.FLOCON_DAVOINE: ["Mueslis, flocons"],
    CategoryValues.QUINOA: ["Quinoa, boulghour, céréales"],
    CategoryValues.SARRASIN: ["Graines", "Quinoa, Semoule, Céréales"],
    CategoryValues.SEIGLE: ["Mueslis, flocons"],
    CategoryValues.SEITAN: ["Spécialités végétales"],
    CategoryValues.FLAGEOLETS: ["Légumineuses"],
    CategoryValues.FLAGEOLETS_CONSERVE: ["Conserves de légumes"],
    CategoryValues.HARICOTS_BLANCS: ["Légumineuses"],
    CategoryValues.HARICOTS_BLANCS_CONSERVE: ["Conserves de légumes"],
    CategoryValues.HARICOTS_ROUGES: ["Légumineuses"],
    CategoryValues.HARICOTS_ROUGES_CONSERVE: ["Conserves de légumes"],
    CategoryValues.LENTILLES_BLONDES: ["Légumineuses"],
    CategoryValues.LENTILLES_CORAIL: ["Légumineuses"],
    CategoryValues.LENTILLES_VERTES: ["Légumineuses"],
    CategoryValues.LENTILLES_VERTES_CONSERVE: ["Conserves de légumes"],
    CategoryValues.POIS_CASSES: ["Légumineuses"],
    CategoryValues.POIS_CHICHES: ["Légumineuses"],
    CategoryValues.POIS_CHICHES_CONSERVE: ["Conserves de légumes"],
    CategoryValues.AMANDES: ["Oléagineux"],
    CategoryValues.BEURRE_DE_CACAHUETE: ["Pâtes à tartiner"],
    CategoryValues.GRAINES_CHIA: ["Graines"],
    CategoryValues.GRAINES_COURGE: ["Graines"],
    CategoryValues.GRAINES_LIN: ["Légumineuses, graines"],
    CategoryValues.GRAINES_TOURNESOL: ["Légumineuses, graines"],
    CategoryValues.NOISETTES: ["Oléagineux"],
    CategoryValues.NOIX_CAJOUS: ["Oléagineux"],
    CategoryValues.PIGNONS_PIN: ["Oléagineux"],
    CategoryValues.PISTACHES: ["Fruits secs", "Oléagineux"],
    CategoryValues.BRIE: ["Camembert, Brie, pâtes molles"],
    CategoryValues.BUCHE_DE_CHEVRE: ["Chèvres et brebis"],
    CategoryValues.CAMEMBERT: ["Camembert, Brie, pâtes molles"],
    CategoryValues.COMTE: ["Emmental, Comté, pâtes cuites"],
    CategoryValues.COULOMMIERS: ["Camembert, Brie, pâtes molles"],
    CategoryValues.EMMENTAL: ["Râpé"],
    CategoryValues.FETA: ["Mozzarella, buratta, mascarpone"],
    CategoryValues.FROMAGE_BLANC: ["Lait de vache"],
    CategoryValues.LAIT_DEMI_ECREME: ["Laits de vache"],
    CategoryValues.LAIT_ENTIER: ["Laits de vache"],
    CategoryValues.MOZZARELLA: ["Mozzarella, buratta, mascarpone", "Râpé"],
    CategoryValues.OEUFS: ["Œufs"],
    CategoryValues.PARMESAN_RAPE: ["Râpé"],
    CategoryValues.ROQUEFORT: ["Roquefort et bleus"],
    CategoryValues.SKYR: ["Lait de vache"],
    CategoryValues.YAOURT_NATURE_0: ["Lait de brebis, chèvre"],
    CategoryValues.ANCHOIS: ["Poissons, crustacés"],
    CategoryValues.COLIN_PANE: ["Poissons"],
    CategoryValues.CREVETTES: ["Poissons, crustacés"],
    CategoryValues.MAQUEREAU_CONSERVE: ["Conserves de poissons"],
    CategoryValues.MAQUEREAU_FRAIS: ["Poissons, crustacés"],
    CategoryValues.SARDINES: ["Conserves de poissons"],
    CategoryValues.SAUMON_FUME: ["Poissons, crustacés"],
    CategoryValues.THON: ["Conserves de poissons"],
    CategoryValues.BARRES_PROTEINEES: ["Sport"],
    CategoryValues.ISOLAT_WHEY: ["Sport"],
    CategoryValues.PROTEINES_VEGETALES_POUDRE: ["Sport"],
    CategoryValues.PROTEINES_SOJA_TEXTUREES: ["Légumineuses"],
    CategoryValues.TEMPEH: ["Tofus, seitans"],
    CategoryValues.TOFU_FUME: ["Tofus, seitans"],
    CategoryValues.TOFU_NATURE: ["Tofus, seitans"],
    CategoryValues.CHIPOLATAS: ["Saucisserie"],
    CategoryValues.CORDON_BLEU: ["Volaille"],
    CategoryValues.COTES_DE_PORC: ["Porc"],
    CategoryValues.CUISSE_POULET: ["Volaille"],
    CategoryValues.FILET_MIGNON_DE_PORC: ["Porc"],
    CategoryValues.JAMBON_BLANC: ["Jambons"],
    CategoryValues.JAMBON_CRU: ["Jambons"],
    CategoryValues.LARDONS: ["Lardons"],
    CategoryValues.MERGUEZ: ["Saucisserie"],
    CategoryValues.NUGGETS: ["Volaille"],
    CategoryValues.POITRINE_FUMEE_BACON: ["Porc"],
    CategoryValues.POULET_FERMIER: ["Volaille"],
    CategoryValues.POULET_FILET: ["Volaille"],
    CategoryValues.RILLETTES: ["Pâtés"],
    CategoryValues.ROTI_DE_PORC: ["Porc"],
    CategoryValues.SAUCISSON_SEC: ["Pâtés, saucissons"],
    CategoryValues.STEAK_HACHE_BOEUF: ["Boeuf"],
}


@unique
class Department(StrEnum):
    """
    The main store departments.
    """

    EPICERIE = "Epicerie Salée"
    FRUITS_LEGUMES = "Fruits et Légumes"
    OEUFS_PRODUITS_LAITIERS = "Crémerie"
    SUCRE = "Epicerie Sucrée"
    SURGELE = "Surgelés"
    VIANDES = "Traiteur, Boucherie, Poissonnerie"
    SPORT = "Bien-être, Santé"
    VRAC = "Vrac"

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


class BiocoopProductsSpider(Spider, ProductSpider):
    """
    Scrapy Spider for the products of the Biocoop retail website.
    """

    name = "biocoop_products"
    allowed_domains = ["www.biocoop.fr"]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        if self.get_category() == "Œufs":
            url = "https://www.biocoop.fr/magasin-biocoop_biocite/cremerie/oeufs-beurres-cremes/oeufs.html"
        else:
            url = f"https://www.biocoop.fr/magasin-biocoop_biocite/catalogsearch/result/?q={query}&p=1"

        yield Request(
            url=url,
            callback=self.parse,
            meta={
                "handle_httpstatus_list": [302],
            },
            dont_filter=True,
        )

    def parse(self, response: Response):
        if response.status == 302:
            product_links = [response.url]
        else:
            product_links = response.xpath(
                "//div[@class='product-item-info']/a/@href"
            ).getall()
        yield from response.follow_all(product_links, callback=self.parse_product)

        next_page_url = response.css("a.next-page ::attr(data-href)").get()

        if next_page_url is not None:
            self.logger.debug(f"Next button detected: {next_page_url}")

            yield response.follow(next_page_url, callback=self.parse)

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

        discounted, base_price, discounted_price = self.extract_discount_and_prices(
            response
        )
        item["price"] = base_price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.logger.info(f"Product {ean} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        yield item

    def is_relevant(self, response: Response) -> bool:
        breadcrumbs = response.css("script::text").re_first(
            r"'product_category1': '(.+)'"
        )
        breadcrumbs = bytes(breadcrumbs, "utf-8").decode("unicode_escape").split("/")

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
        name = response.xpath("//span[@itemprop='name']/text()").get()

        return name

    def get_brand(self, response: Response) -> str:
        brand = response.xpath("//span[@class='brand value']/text()").get()

        return brand

    def get_ean13(self, response: Response) -> str | None:
        img_link_parts = (
            response.xpath("//meta[@itemprop='image']/@content")
            .re_first(r"(https://.*\.jpe?g)")
            .split("/")
            .pop()
            .split("-")
        )

        if len(img_link_parts) < 2 or len(img_link_parts[1]) != 13:
            return

        return img_link_parts[1]

    @staticmethod
    def extract_discount_and_prices(
        response: Response,
    ) -> tuple[bool, float, float | None]:
        """
        Extracts whether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """

        # Current price, could be the discounted one.
        current_price = float(
            response.xpath("//meta[@property='product:price:amount']/@content").get()
        )

        # The presence of an "old price" means that there is a discount.
        # The discounted price is before the crossed out price.
        is_discounted = response.xpath("//span[@class='old-price']").get() is not None

        if is_discounted:
            old_price = response.xpath(
                "//span[@class='old-price']/span/span/span/text()"
            ).get()

            if old_price is not None:
                base_price = float(
                    re.match("([.,0-9]+)", old_price).group(1).replace(",", ".")
                )
            else:
                base_price = current_price
            return (is_discounted, base_price, current_price)
        else:
            return (is_discounted, current_price, None)

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        is_vrac = (
            response.xpath("//div[@class='vrac-options-wrapper']").get() is not None
        )

        if is_vrac:
            quantity = 100 / 1000
            quantity_unit = QuantityUnit.KILOGRAM

            return (quantity, quantity_unit)
        else:
            quantity_attribute = response.xpath(
                "//div[@class='part-product']/span/text()"
            ).get()

            if quantity_attribute is not None:
                m = re.match(
                    "([.0-9]+) ?(cl|ml|L|kg|g|u)", quantity_attribute, re.IGNORECASE
                )

                if m is not None:
                    raw_quantity = m.group(1)  # 200, 1,5
                    raw_quantity_unit = m.group(2)  # g, kg, L, l, cl

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
                        case "u":
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

                    return (quantity, quantity_unit)
