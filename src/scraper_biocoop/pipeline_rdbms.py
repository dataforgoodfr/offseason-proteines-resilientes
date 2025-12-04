from logging import DEBUG, getLogger
from typing import Optional

from itemadapter import ItemAdapter
from scrapy import Item
from scrapy.exceptions import DropItem
from scrapy.spiders import Spider
from sqlalchemy import select

from models.category import Category
from models.price import Price
from models.product import Product
from models.source import Origin, Source
from utils.database import RDBMSPipelineMixin

from .items import ProductItem


class ProductPipeline(RDBMSPipelineMixin):
    """
    Scrapy pipeline used to store items into a RDBMS via SQLAlchemy.
    """

    def process_item(self, item: Item, spider: Spider):
        logger = getLogger(__name__)

        if isinstance(item, ProductItem):
            adapter = ItemAdapter(item)

            ean = adapter.get("ean")

            existing_product: Optional[Product] = (
                self.db_session.query(Product).filter(Product.ean_13 == ean).first()
            )

            if existing_product:
                logger.debug(f"Product {ean} already present in database")

                if existing_product.disabled:
                    raise DropItem(f"Product {ean} is disabled. Skipping...", DEBUG)

                logger.debug(f"Adding new source to product {ean}")
                existing_product.sources.append(
                    Source(
                        origin=Origin.BIOCOOP,
                        url=item["url"],
                        price=Price(
                            amount=item["price"],
                            discounted=item["discounted"],
                            discounted_amount=item.get("discounted_price"),
                        )
                        if item["price"] is not None
                        else None,
                    )
                )
            else:
                logger.debug(f"Adding new product {ean}")

                query = select(Category).where(Category.name == item["category"])
                category = self.db_session.scalars(query).one()

                product = Product(
                    ean_13=ean,
                    name=item["name"],
                    brand=item["brand"],
                    category=category,
                    quantity=item["quantity"],
                    quantity_unit=item["quantity_unit"],
                    sources=[
                        Source(
                            origin=Origin.BIOCOOP,
                            url=item["url"],
                            price=Price(
                                amount=item["price"],
                                discounted=item["discounted"],
                                discounted_amount=item.get("discounted_price"),
                            )
                            if item["price"] is not None
                            else None,
                        ),
                    ],
                )

                self.db_session.add(product)

        self.db_session.commit()

        return item
