from itemadapter import ItemAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .items import ProductItem
from models.base import Base
from models.product import Product
from models.source import Source


# The default SQLite database filename.
DEFAULT_SQLITE_FILENAME = "data.sqlite"


class ProductPipeline:
    """
    Scrapy pipeline used to store items into a RDBMS via SQLAlchemy.
    """

    def __init__(self):
        engine = create_engine("sqlite+pysqlite:///" + DEFAULT_SQLITE_FILENAME)
        Base.metadata.create_all(engine)

        self.db_engine = engine

    def open_spider(self, spider):
        self.db_session = Session(self.db_engine)

    def close_spider(self, spider):
        self.db_session.close()

    def process_item(self, item, spider):
        if isinstance(item, ProductItem):
            adapter = ItemAdapter(item)

            for ean in adapter.get("eans"):
                existing_product = (
                    self.db_session.query(Product).filter(Product.ean_13 == ean).first()
                )

                if existing_product:
                    existing_product.sources.append(Source(url=item["url"]))
                else:
                    product = Product(
                        ean_13=ean,
                        name=item["name"],
                        brand=item["brand"],
                        sources=[
                            Source(
                                url=item["url"],
                            )
                        ],
                    )

                    self.db_session.add(product)

        self.db_session.commit()

        return item
