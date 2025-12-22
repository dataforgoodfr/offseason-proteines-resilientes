import re
from collections.abc import Generator
from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http import Response

from models.product import QuantityUnit
from utils.spider import ProductItem, ProductSpider


class PicardProductsSpider(Spider, ProductSpider):
    """
    Scrapy PicardSpider for the products of the Picard retail website.
    """

    name = "picard_products"

    BASE_URL = "https://www.picard.fr"
    START_URL_TEMPLATE = "https://www.picard.fr/recherche?q={query}&sz=1000"  # sz=1000 means 1000 products per page, which means we don't need to manage pagination

    PRODUCT_LINKS_XPATH = "//div[@class='pi-ProductList-content']//li[contains(@class,'pi-ProductGrid-item')]//div/a/@href"
    PRODUCT_NAME_XPATH = "//h1[@itemprop='name']/text()"
    PRODUCT_BRAND_XPATH = "//meta[@itemprop='brand']/@content"
    PRODUCT_EAN_XPATH = "//meta[@itemprop='gtin13']/@content"
    PRODUCT_TITLE_XPATH = "//h1[@class='product-title']/text()"
    PRODUCT_QUANTITY_XPATH = "//div[@class='pi-ProductDetails-weight']/span/text()"
    PRODUCT_PRICE_XPATH = "//div[@class='pi-ProductDetails-salesPrice']/meta/@content"
    PRODUCT_DISCOUNTED_PRICE_XPATH = "//div[@class='pi-ProductOffer-salesPrice']"
    PRODUCT_NUTRISCORE_XPATH = "//div[@class='pi-ProductTabsNutrition-nutriscoreBlock']//span[@class='sr-only']/text()"
    PRODUCT_NUTRITION_TABLE_COL1_XPATH = (
        "//table[@class='pi-ProductTabsNutrition-table']/tbody/tr/td[1]"
    )
    PRODUCT_NUTRITION_TABLE_COL2_XPATH = (
        "//table[@class='pi-ProductTabsNutrition-table']/tbody/tr/td[2]"
    )
    PRODUCT_NUTRITION_TABLE_COL3_XPATH = (
        "//table[@class='pi-ProductTabsNutrition-table']/tbody/tr/td[3]"
    )

    allowed_domains = [urlparse(BASE_URL).netloc]

    custom_settings = {}

    async def start(self):
        query = getattr(self, "query", None)

        if query is None:
            raise AttributeError("Missing 'query' argument")

        yield Request(
            url=self.START_URL_TEMPLATE.format(query=query), callback=self.parse
        )

    def parse(self, response: Response, **kwargs):
        product_links = response.xpath(self.PRODUCT_LINKS_XPATH).getall()
        yield from response.follow_all(product_links, callback=self.parse_product)

    def parse_product(self, response: Response) -> Generator[ProductItem]:
        item = ProductItem()

        ean = self.get_ean13(response)

        if ean is None:
            self.log("No EAN-13 found. Skipping...")
            return

        item["ean"] = ean
        item["name"] = self.get_name(response)
        item["brand"] = self.get_brand(response)
        item["category"] = self.get_category()
        item["url"] = response.url

        discounted, base_price, discounted_price = (
            PicardProductsSpider.extract_discount_and_prices(response)
        )
        item["price"] = base_price
        item["discounted"] = discounted
        if discounted:
            item["discounted_price"] = discounted_price

        quantity, quantity_unit = self.get_quantity(response) or (None, None)

        if quantity is None:
            self.log(f"Product {ean} has no quantity. Skipping...")
            return

        item["quantity"] = quantity
        item["quantity_unit"] = quantity_unit

        item["nutrition_facts"] = self.get_nutrition_facts(response)

        yield item

    def is_relevant(self, response: Response) -> bool:
        # Not yet implemented.
        return True

    def get_name(self, response: Response) -> str:
        name = response.xpath(self.PRODUCT_NAME_XPATH).get()

        return name

    def get_brand(self, response: Response) -> str:
        brand = response.xpath(self.PRODUCT_BRAND_XPATH).get()
        brand = (
            brand.strip() if brand else "PicardUnknownBrand"
        )  # Fallback to PicardUnknownBrand if not found

        return brand

    def get_ean13(self, response: Response) -> str | None:
        ean = response.xpath(self.PRODUCT_EAN_XPATH).get() or ""

        if not ean:
            return

        return ean

    @classmethod
    def extract_discount_and_prices(cls, response) -> tuple[bool, float, float | None]:
        """
        Extracts wether or not the product is discounted and its both prices
        (normal and discounted) from the response.
        """

        raw_base_price = response.xpath(cls.PRODUCT_PRICE_XPATH).get().strip()
        base_price = float(re.sub(r"[^\d.,]", "", raw_base_price).replace(",", "."))

        raw_discounted_price = response.xpath(cls.PRODUCT_DISCOUNTED_PRICE_XPATH).get()
        if raw_discounted_price is not None:
            raw_discounted_price = raw_discounted_price.strip()
            current_price = float(
                re.sub(r"[^\d.,]", "", raw_discounted_price).replace(",", ".")
            )
            return (True, base_price, current_price)
        else:
            return (False, base_price, None)

    def get_quantity(self, response: Response) -> tuple[float, QuantityUnit] | None:
        quantity_attribute = response.xpath(self.PRODUCT_QUANTITY_XPATH).get()
        self.log("quantity_attribute :" + quantity_attribute)

        if quantity_attribute is not None:
            # replace &nbsp; with normal space
            quantity_attribute = quantity_attribute.replace("&nbsp;", " ").replace(
                "\xa0", " "
            )
            m = re.search(
                r"(\d+[\.,]?\d*)\s*([a-zA-Z]+)",
                quantity_attribute,
                re.IGNORECASE,
            )
            # self.log("m :" + m)
            if m is not None:
                raw_quantity = m.group(1)  # 200, 1,5
                raw_quantity_unit = m.group(2)  # g, kg, L, l, cl

                self.log("raw_quantity :" + raw_quantity)
                self.log("raw_quantity_unit :" + raw_quantity_unit)

                quantity = float(raw_quantity.replace(",", "."))

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
                    case _:
                        return

                return (quantity, quantity_unit)

    def get_nutrition_facts(self, response):
        nutrition_facts = {}

        col1_labels = response.xpath(self.PRODUCT_NUTRITION_TABLE_COL1_XPATH)
        col2_contents = response.xpath(self.PRODUCT_NUTRITION_TABLE_COL2_XPATH)
        col3_contents = response.xpath(self.PRODUCT_NUTRITION_TABLE_COL3_XPATH)

        nutrition_table = []
        for i in range(min(len(col1_labels), len(col2_contents), len(col3_contents))):
            # label = get_text_content(col1_elements[i]).strip()
            col1_label = col1_labels[i].xpath("string(.)").get("").strip()
            col2_content = "".join(
                [
                    # str(html.tostring(div, encoding="unicode"))
                    div.xpath("string(.)").get("")
                    for div in col2_contents[i].xpath(".//div")
                ]
            ).strip()
            col3_content = "".join(
                [
                    # str(html.tostring(div, encoding="unicode"))
                    div.xpath("string(.)").get("")
                    for div in col3_contents[i].xpath(".//div")
                ]
            ).strip()  # 3rd column in text format

            nutrition_table.append(
                {
                    "label": col1_label,
                    "content1": col2_content,  # Ex: "<div>588 kJ</div><div>140 kcal</div>"
                    "content2": col3_content,  # Ex: "<div>140</div>"
                }
            )

        # Step 3: Extract the Nutri-Score (first, before the other nutrients)
        nutriscore_result = response.xpath(self.PRODUCT_NUTRISCORE_XPATH).get()
        nutriscore_value = nutriscore_result if nutriscore_result else ""
        # Remove "nutriscore-" prefix (case insensitive) and keep only the letter
        nutrition_facts["nutriscore"] = (
            nutriscore_value.replace("nutriscore-", "")
            .replace("NUTRISCORE-", "")
            .strip()
            .upper()
            if nutriscore_value
            else ""
        )

        # Step 4: Map and assign nutrients
        for idx, row in enumerate(nutrition_table):
            label = row["label"].lower()

            # Extract all divs from column 2
            divs = col2_contents[idx].xpath(".//div")

            # Special case: Energy in kcal
            if "energie" in label:
                if len(divs) == 2:
                    # calories_100g_raw = content of the second div only (without tags)
                    nutrition_facts["calories_100g_raw"] = divs[1].get().strip()

                    calories_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["calories_100g_raw"]
                    )
                    if calories_match:
                        nutrition_facts["calories_100g"] = float(
                            calories_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["calories_100g"] = 0.0
                else:
                    nutrition_facts["calories_100g"] = 0.0

            # Special case: Fats with saturated fats
            elif "matières grasses" in label:
                if len(divs) == 2:
                    nutrition_facts["fat_100g_raw"] = divs[0].get().strip()
                    nutrition_facts["saturated_fat_100g_raw"] = divs[1].get().strip()

                    fat_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["fat_100g_raw"]
                    )
                    if fat_match:
                        nutrition_facts["fat_100g"] = float(
                            fat_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["fat_100g"] = 0.0

                    saturated_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["saturated_fat_100g_raw"]
                    )
                    if saturated_match:
                        nutrition_facts["saturated_fat_100g"] = float(
                            saturated_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["saturated_fat_100g"] = 0.0

                else:
                    nutrition_facts["fat_100g"] = 0.0
                    nutrition_facts["saturated_fat_100g"] = 0.0

            # Special case: Carbohydrates with sugars
            elif "glucides" in label:
                if len(divs) == 2:
                    nutrition_facts["carbohydrates_100g_raw"] = divs[0].get().strip()
                    nutrition_facts["sugars_100g_raw"] = divs[1].get().strip()

                    carbs_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["carbohydrates_100g_raw"]
                    )
                    if carbs_match:
                        nutrition_facts["carbohydrates_100g"] = float(
                            carbs_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["carbohydrates_100g"] = 0.0

                    sugars_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["sugars_100g_raw"]
                    )
                    if sugars_match:
                        nutrition_facts["sugars_100g"] = float(
                            sugars_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["sugars_100g"] = 0.0
                else:
                    nutrition_facts["carbohydrates_100g"] = 0.0
                    nutrition_facts["sugars_100g"] = 0.0

            # Special case: Fiber
            elif "fibres alimentaires" in label:
                if len(divs) == 1:
                    # fiber_100g_raw = content of the first (and only) div (without tags)
                    nutrition_facts["fiber_100g_raw"] = divs[0].get().strip()

                    fiber_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["fiber_100g_raw"]
                    )
                    if fiber_match:
                        nutrition_facts["fiber_100g"] = float(
                            fiber_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["fiber_100g"] = 0.0
                else:
                    nutrition_facts["fiber_100g"] = 0.0

            # Special case: Proteins
            elif "protéines" in label:
                if len(divs) == 1:
                    # protein_100g_raw = content of the first (and only) div (without tags)
                    nutrition_facts["protein_100g_raw"] = divs[0].get().strip()

                    protein_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["protein_100g_raw"]
                    )
                    if protein_match:
                        nutrition_facts["protein_100g"] = float(
                            protein_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["protein_100g"] = 0.0
                else:
                    nutrition_facts["protein_100g"] = 0.0

            # Special case: Salt
            elif "sel" in label:
                if len(divs) == 1:
                    # salt_100g_raw = content of the first (and only) div (without tags)
                    nutrition_facts["salt_100g_raw"] = divs[0].get().strip()

                    salt_match = re.search(
                        r"(\d+[,.]?\d*)", nutrition_facts["salt_100g_raw"]
                    )
                    if salt_match:
                        nutrition_facts["salt_100g"] = float(
                            salt_match.group(1).replace(",", ".")
                        )
                    else:
                        nutrition_facts["salt_100g"] = 0.0
                else:
                    nutrition_facts["salt_100g"] = 0.0

        # Initialize default values if not found
        for key in [
            "calories_100g",
            "fat_100g",
            "saturated_fat_100g",
            "carbohydrates_100g",
            "sugars_100g",
            "fiber_100g",
            "protein_100g",
            "salt_100g",
        ]:
            if key not in nutrition_facts:
                nutrition_facts[key] = 0.0

        for key in [
            "calories_100g_raw",
            "fat_100g_raw",
            "saturated_fat_100g_raw",
            "carbohydrates_100g_raw",
            "sugars_100g_raw",
            "fiber_100g_raw",
            "protein_100g_raw",
            "salt_100g_raw",
        ]:
            if key not in nutrition_facts:
                nutrition_facts[key] = ""

        # There is no novascore on the Picard website)
        # nutrition_facts["novascore"] = None

        return nutrition_facts
