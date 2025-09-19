from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import List

from .items import ProductItem
from models.base import Base
from models.price import Price
from models.product import Product
from models.source import Source


# The default SQLite database filename.
DEFAULT_SQLITE_FILENAME = "data.sqlite"


class ProductPipeline:
    """
    Contexte manager to store items into a RDBMS via SQLAlchemy.

    Example of usage :

    with ProductPipeline() as pipeline:
        pipeline.insert_items(items)
    """

    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = "sqlite+pysqlite:///" + DEFAULT_SQLITE_FILENAME

        self.db_engine = create_engine(database_url)
        Base.metadata.create_all(self.db_engine)
        self.db_session = None

    def __enter__(self):
        self.db_session = Session(self.db_engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db_session:
            try:
                if exc_type is None:
                    self.db_session.commit()
                else:
                    self.db_session.rollback()
            finally:
                self.db_session.close()
                self.db_session = None

    def insert_items(self, items: List[ProductItem]):
        """Process an item and add it to the database."""
        if self.db_session is None:
            raise RuntimeError(
                "Pipeline not started. Use 'with ProductPipeline() as pipeline:'"
            )

        if isinstance(items, List[ProductItem]):
            for item in items:
                for ean in item.eans:
                    existing_product = (
                        self.db_session.query(Product)
                        .filter(Product.ean_13 == ean)
                        .first()
                    )

                    if existing_product:
                        existing_product.sources.append(
                            Source(url=items["url"], price=Price(amount=items["price"]))
                        )
                    else:
                        product = Product(
                            ean_13=ean,
                            name=items["name"],
                            brand=items["brand"],
                            sources=[
                                Source(
                                    url=items["url"], price=Price(amount=items["price"])
                                )
                            ],
                        )
                        self.db_session.add(product)
        return items
