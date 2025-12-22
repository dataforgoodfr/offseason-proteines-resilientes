from logging import getLogger
from typing import Optional

from itemadapter import ItemAdapter
from scrapy import Item
from scrapy.exceptions import DropItem
from scrapy.spiders import Spider
from sqlalchemy import select

from models.category import Category
from models.nutrition_facts import NutritionFacts
from models.price import Price
from models.product import Product
from models.source import Origin, Source
from utils.database import RDBMSPipelineMixin
from utils.spider import ProductItem


class ProductPipeline(RDBMSPipelineMixin):
    """
    Scrapy pipeline used to store items into a RDBMS via SQLAlchemy.
    """

    def process_item(self, item: Item, spider: Spider):
        logger = getLogger(__name__)

        if isinstance(item, ProductItem):
            adapter = ItemAdapter(item)

            ean_from_item = adapter.get("ean")  # Utilise "ean" au singulier

            if ean_from_item is None:
                logger.warning(f"Product item is missing EAN. Skipping item: {item}")
                raise DropItem(f"Missing EAN for item {item}")

            # On utilise cet ean_from_item pour la recherche
            existing_product: Optional[Product] = (
                self.db_session.query(Product)
                .filter(Product.ean_13 == ean_from_item)
                .first()
            )

            if existing_product:
                logger.debug(f"Product {ean_from_item} already present in database")
                # ... le reste de la logique de mise à jour ...
                # Si on ajoute une source, il faudra aussi y associer les nutrition_facts si présentes dans l'item
                source = Source(
                    origin=Origin.PICARD,
                    url=item["url"],
                    price=Price(
                        amount=item["price"],
                        discounted=item["discounted"],
                        discounted_amount=item.get("discounted_price"),
                    )
                    if item.get("price") is not None
                    else None,
                )
                if item.get("nutrition_facts"):
                    nutrition_facts_data = item["nutrition_facts"]
                    nutrition_facts = NutritionFacts(
                        nutriscore=nutrition_facts_data.get("nutriscore"),
                        novascore=nutrition_facts_data.get("novascore"),
                        calories_100g=nutrition_facts_data.get("calories_100g"),
                        fat_100g=nutrition_facts_data.get("fat_100g"),
                        saturated_fat_100g=nutrition_facts_data.get(
                            "saturated_fat_100g"
                        ),
                        carbohydrates_100g=nutrition_facts_data.get(
                            "carbohydrates_100g"
                        ),
                        sugars_100g=nutrition_facts_data.get("sugars_100g"),
                        fiber_100g=nutrition_facts_data.get("fiber_100g"),
                        protein_100g=nutrition_facts_data.get("protein_100g"),
                        salt_100g=nutrition_facts_data.get("salt_100g"),
                    )
                    source.nutrition_facts = nutrition_facts
                existing_product.sources.append(source)

            else:
                logger.debug(f"Adding new product {ean_from_item}")

                query = select(Category).where(Category.name == item["category"])
                category = self.db_session.scalars(query).one()

                new_source = Source(
                    origin=Origin.PICARD,
                    url=item["url"],
                    price=Price(
                        amount=item["price"],
                        discounted=item["discounted"],
                        discounted_amount=item.get("discounted_price"),
                    )
                    if item.get("price") is not None
                    else None,
                )
                if item.get("nutrition_facts"):
                    nutrition_facts_data = item["nutrition_facts"]
                    nutrition_facts = NutritionFacts(
                        nutriscore=nutrition_facts_data.get("nutriscore"),
                        novascore=nutrition_facts_data.get("novascore"),
                        calories_100g=nutrition_facts_data.get("calories_100g"),
                        fat_100g=nutrition_facts_data.get("fat_100g"),
                        saturated_fat_100g=nutrition_facts_data.get(
                            "saturated_fat_100g"
                        ),
                        carbohydrates_100g=nutrition_facts_data.get(
                            "carbohydrates_100g"
                        ),
                        sugars_100g=nutrition_facts_data.get("sugars_100g"),
                        fiber_100g=nutrition_facts_data.get("fiber_100g"),
                        protein_100g=nutrition_facts_data.get("protein_100g"),
                        salt_100g=nutrition_facts_data.get("salt_100g"),
                    )
                    new_source.nutrition_facts = nutrition_facts

                product = Product(
                    ean_13=ean_from_item,  # Utilise l'ean récupéré
                    name=item["name"],
                    brand=item["brand"],
                    category=category,
                    quantity=item["quantity"],
                    quantity_unit=item["quantity_unit"],
                    sources=[new_source],
                )

                self.db_session.add(product)

        self.db_session.commit()

        return item
