"""
Integration tests between the 'models.product' and 'models.reference' modules.
"""

import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.base import Base
from models.reference import Type as RefType, Reference
from models.product import NovaScore, NutriScore, Product


class TestProductReference(unittest.TestCase):
    """
    Tests the integration between the 'models.product.Product' and
    'models.reference.Reference' classes.
    """

    def setUp(self):
        self.db_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.db_engine)

    def tearDown(self):
        Base.metadata.drop_all(self.db_engine)

    def test_create_products(self):
        with Session(self.db_engine) as session:
            product_a = Product(
                name="Product A",
                references=[
                    Reference(type=RefType.EAN, value="12345"),
                ],
                nutriscore=NutriScore.A,
                novascore=NovaScore.Group2,
                fat_100g=2.3,
                saturated_fat_100g=1.1,
                carbohydrates_100g=5.6,
                sugars_100g=8.4,
                fiber_100g=13.2,
                proteins_100g=2.1,
                salt_100g=3.6,
            )
            product_b = Product(
                name="Product B",
                references=[
                    Reference(type=RefType.EAN, value="67890"),
                ],
                nutriscore=NutriScore.D,
                novascore=NovaScore.Group4,
                fat_100g=26.1,
                saturated_fat_100g=16.7,
                carbohydrates_100g=34.6,
                sugars_100g=21.0,
                fiber_100g=5.4,
                proteins_100g=4.9,
                salt_100g=7.8,
            )

            session.add_all([product_a, product_b])
            session.commit()

            self.assertEqual(session.query(Product).count(), 2)

            query = select(Product).where(Product.name == "Product A")
            result = session.scalars(query).one()
            self.assertEqual(result.name, product_a.name)
            self.assertEqual(result.nutriscore, product_a.nutriscore)
            self.assertEqual(result.fiber_100g, product_a.fiber_100g)


if __name__ == "__main__":
    unittest.main()
