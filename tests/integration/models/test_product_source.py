"""
Integration tests between the 'models.product' and 'models.source' modules.
"""

import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.base import Base
from models.nutrition_facts import NutritionFacts, NutriScore, NovaScore
from models.price import Price
from models.product import Product, QuantityUnit, Category
from models.source import Source, Origin


class TestProductSource(unittest.TestCase):
    """
    Tests the integration between the 'models.product.Product' and
    'models.source.Source' classes.
    """

    def setUp(self):
        self.db_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.db_engine)

    def tearDown(self):
        Base.metadata.drop_all(self.db_engine)

    def test_create_products(self):
        with Session(self.db_engine) as session:
            product_a = Product(
                ean_13="7622300336738",
                name="Product A",
                brand="Brand A",
                quantity=0.5,
                quantity_unit=QuantityUnit.KILOGRAM,
                category=Category.VIANDE,
                aliment="Aliment A",
                sources=[
                    Source(
                        origin=Origin.AUCHAN,
                        url="https://www.store-a.com",
                        nutrition_facts=NutritionFacts(
                            nutriscore=NutriScore.A,
                            novascore=NovaScore.Group3,
                            calories_100g=89,
                            fat_100g=3.1,
                            saturated_fat_100g=0.5,
                            carbohydrates_100g=8.5,
                            sugars_100g=1.4,
                            fiber_100g=4.4,
                            protein_100g=4.5,
                            salt_100g=0.66,
                        ),
                    ),
                    Source(
                        origin=Origin.BIOCOOP,
                        url="https://www.store-b.com",
                        price=Price(
                            amount=3.62,
                            discounted=True,
                            discounted_amount=1.62,
                        ),
                    ),
                ],
            )
            product_b = Product(
                ean_13="8625503639758",
                name="Product B",
                brand="Brand B",
                quantity=1.5,
                quantity_unit=QuantityUnit.LITRE,
                category=Category.LAITIER,
                aliment="Aliment B",
                sources=[
                    Source(
                        origin=Origin.CARREFOUR,
                        url="https://www.store-a.com",
                    ),
                ],
            )

            session.add_all([product_a, product_b])
            session.commit()

            self.assertEqual(session.query(Product).count(), 2)

            query = select(Product).where(Product.name == "Product A")
            result = session.scalars(query).one()
            self.assertEqual(result.ean_13, product_a.ean_13)
            self.assertEqual(result.name, product_a.name)
            self.assertEqual(result.quantity, product_a.quantity)
            self.assertEqual(result.quantity_unit, product_a.quantity_unit)
            self.assertEqual(result.category, product_a.category)
            self.assertEqual(result.aliment, product_a.aliment)
            self.assertEqual(len(result.sources), 2)
            self.assertEqual(result.sources[0].origin, product_a.sources[0].origin)
            self.assertEqual(result.sources[0].url, product_a.sources[0].url)
            self.assertEqual(
                result.sources[0].nutrition_facts.fat_100g,
                product_a.sources[0].nutrition_facts.fat_100g,
            )
            self.assertEqual(result.sources[1].price, product_a.sources[1].price)


if __name__ == "__main__":
    unittest.main()
