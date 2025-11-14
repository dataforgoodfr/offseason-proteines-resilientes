from logging import DEBUG, getLogger
from typing import Optional

from itemadapter import ItemAdapter
from scrapy import Item
from scrapy.exceptions import DropItem
from scrapy.spiders import Spider
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .items import ProductItem
from models.base import Base
from models.price import Price
from models.product import Product
from models.source import Source, Origin
from utils.database import DEFAULT_DATABASE_URL


class ProductPipeline:
    """
    Scrapy pipeline used to store items into a RDBMS via SQLAlchemy.
    """

    def open_spider(self, spider: Spider):
        database_url = spider.settings.get("DATABASE_URL", DEFAULT_DATABASE_URL)

        engine = create_engine(database_url)
        Base.metadata.create_all(engine)

        self.db_engine = engine
        self.db_session = Session(self.db_engine)

    def close_spider(self, spider: Spider):
        self.db_session.close()

    def process_item(self, item: Item, spider: Spider):
        logger = getLogger(__name__)

        if isinstance(item, ProductItem):
            adapter = ItemAdapter(item)

            for ean in adapter.get("eans"):
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
                            origin=Origin.AUCHAN,
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
                    product = Product(
                        ean_13=ean,
                        name=item["name"],
                        brand=item["brand"],
                        quantity=item["quantity"],
                        quantity_unit=item["quantity_unit"],
                        sources=[
                            Source(
                                origin=Origin.AUCHAN,
                                url=item["url"],
                                price=Price(
                                    amount=item["price"],
                                    discounted=item["discounted"],
                                    discounted_amount=item.get("discounted_price"),
                                )
                                if item["price"] is not None
                                else None,
                            )
                        ],
                    )

                    self.db_session.add(product)

        self.db_session.commit()

        return item
