from re import match, IGNORECASE
from logging import DEBUG, getLogger

from scrapy import Request, Spider

from .items import ProductItem
from models.product import QuantityUnit, Category, Department

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

        url = f"https://www.auchan.fr/recherche?text={query}&categorylevel1=produits20laitiers2c20oeufs2c20fromages&categorylevel1=boucherie2c20volaille2c20poissonnerie&categorylevel1=fruits2c20le9gumes&categorylevel1=surgele9s&categorylevel1=epicerie20sucre9e&categorylevel1=epicerie20sale9e&categorylevel1=charcuterie2c20traiteur"

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
        logger = getLogger(__name__)

        item = ProductItem()

        breadcrumbs = response.xpath(
            "//span[@class='site-breadcrumb__item']/a/text()"
        ).getall()

        exclusion_list = (
            "cuisiné",
            "bébé",
            "pizza",
            "bouillon",
            "boisson",
            "alcools",
            "glaces",
            "biscuits",
        )
        if Department(breadcrumbs[1]) is None or [
            excl for excl in exclusion_list for s in breadcrumbs if excl in s.lower()
        ]:
            if Department(breadcrumbs[1]) is None:
                logger.debug(f"Dept {breadcrumbs[1]} skipped")
            else:
                excluded = [
                    s
                    for excl in exclusion_list
                    for s in breadcrumbs
                    if excl in s.lower()
                ]
                logger.debug(f"Product {excluded} skipped")
            pass
        else:
            item["name"] = response.xpath(
                "//div[@itemtype='https://schema.org/Product']/meta[@itemprop='name']/@content"
            ).get()
            item["brand"] = response.xpath("//meta[@itemprop='brand']/@content").get()
            item["eans"] = self.extract_eans(response)
            item["url"] = response.url

            item["department"] = Department(breadcrumbs[1])
            category_found = self.normalised_category(breadcrumbs, item["name"])
            if category_found is None:
                logger.debug(
                    f"{item['name']},{item['eans']},{breadcrumbs[1]} NO CATEGORY FOUND"
                )
                pass
            else:
                item["category"] = category_found

            (discounted, price, discounted_price) = self.extract_discount_and_prices(
                response
            )
            item["price"] = price
            item["discounted"] = discounted
            if discounted:
                item["discounted_price"] = discounted_price

            quantity, quantity_unit = self.extract_quantity(response)
            item["quantity"] = quantity
            item["quantity_unit"] = quantity_unit

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
    def extract_discount_and_prices(response) -> float:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """

        basePrice = float(response.css("script::text").re_first(r'"price": ?([.0-9]+)'))
        currentPrice = float(response.xpath("//meta[@itemprop='price']/@content").get())

        is_discounted = basePrice - currentPrice > 0

        return (
            is_discounted,
            basePrice,
            currentPrice if is_discounted else None,
        )

    @staticmethod
    def extract_quantity(response) -> tuple[float, QuantityUnit] | None:
        """
        Extracts the product quantity and its unit from the response, and
        normalises it into either kg or L.
        """

        product_attributes = response.css(
            ".offer-selector__attributes span.product-attribute"
        )

        for product_attribute in product_attributes:
            m = match(
                "Contenance : (\\d+x)?([.,0-9]+) ?(ml|cl|L|kg|g)",
                product_attribute.attrib["aria-label"],
                IGNORECASE,
            )

            if m is not None:
                multiplier = m.group(1)  # None or 2x, 6x
                raw_quantity = m.group(2)  # 200, 1,5
                raw_quantity_unit = m.group(3)  # g, kg, L, l, cl, ml

                quantity = float(raw_quantity.replace(",", "."))
                quantity_unit = raw_quantity_unit

                match raw_quantity_unit.lower():
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

                if multiplier is None:
                    return (quantity, quantity_unit)
                else:
                    nb = int("".join(filter(str.isdigit, multiplier)))
                    return (quantity * nb, quantity_unit)

    @staticmethod
    def normalised_category(breadcrumbs, name) -> Category:
        """
        Get the normalised category from the breadcrumbs.
        """
        main_dpt = breadcrumbs[1]

        if Department(main_dpt) == Department.LAITIER:
            categorie = Category.LAITIER
        elif (
            "Conserves de poisson" in breadcrumbs
            or "Poissons, crustacés" in breadcrumbs
            or "Poissons, fruits de mer" in breadcrumbs
            or "Marée du jour" in breadcrumbs
            or "Traiteur de la mer" in breadcrumbs
        ):
            categorie = Category.POISSON
        elif (
            (
                Department(main_dpt) == Department.VIANDE
                or Department(main_dpt) == Department.CHARCUTERIE
                or "La boucherie à la coupe" in breadcrumbs
                or "La charcuterie à la coupe" in breadcrumbs
                or "Viandes" in breadcrumbs
            )
            and "Simili-carnés, tofu" not in breadcrumbs
            and "Panés végétaux" not in breadcrumbs
        ):
            categorie = Category.VIANDE
        elif (
            "Lentilles, pois chiches" in breadcrumbs
            or "Haricots, flageolets" in breadcrumbs
            or "Lentilles, légumes secs" in breadcrumbs
            or "lupin" in name.lower()
            or "fèves" in name.lower()
            or "falafel" in name.lower()
        ):
            categorie = Category.LEGUMINEUSE
        elif (
            "Simili-carnés, tofu" in breadcrumbs or "Epicerie salée" in breadcrumbs
        ) and ("tofu" in name.lower() or "soja" in name.lower()):
            categorie = Category.SOJA
        elif "Simili-carnés, tofu" in breadcrumbs or "Panés végétaux" in breadcrumbs:
            categorie = Category.ALTERNATIVE
        elif (
            "Céréales, galettes, quinoa" in breadcrumbs
            or "Céréales adultes" in breadcrumbs
            or "quinoa" in name.lower()
        ) and ("chia" not in name.lower() or "courge" not in name.lower()):
            categorie = Category.CEREALE
        elif (
            "Mélanges, graines, fruits exotiques" in breadcrumbs
            or "Légumes secs, graines" in breadcrumbs
            or "Cacahuètes, pistaches, mélanges" in breadcrumbs
            or "Noix, noisettes" in breadcrumbs
            or "chia" in name.lower()
            or "courge" in name.lower()
            or "beurre de cacahuète" in name.lower()
        ):
            categorie = Category.NOIX
        elif "Barres de céréales" in breadcrumbs:
            categorie = Category.POUDRE
        else:
            categorie = None

        return categorie
