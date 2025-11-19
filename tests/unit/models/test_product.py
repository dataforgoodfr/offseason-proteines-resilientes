"""
Unit tests for the 'models.product' module.
"""

import unittest

from models.product import QuantityUnit, Category


class TestQuantityUnit(unittest.TestCase):
    """
    Tests the 'QuantityUnit' class.
    """

    def test_string_to_enum(self):
        quantity_unit = QuantityUnit("kg")

        self.assertIsInstance(quantity_unit, QuantityUnit)
        self.assertIs(quantity_unit, quantity_unit.KILOGRAM)

        quantity_unit = QuantityUnit("Kg")

        self.assertIsInstance(quantity_unit, QuantityUnit)
        self.assertIs(quantity_unit, QuantityUnit.KILOGRAM)

        quantity_unit = QuantityUnit("l")

        self.assertIsInstance(quantity_unit, QuantityUnit)
        self.assertIs(quantity_unit, QuantityUnit.LITRE)

        with self.assertRaises(ValueError):
            quantity_unit = QuantityUnit("XYZ")

            self.assertIsInstance(quantity_unit, QuantityUnit)


class TestCategory(unittest.TestCase):
    """
    Tests the 'Category' class.
    """

    def test_string_to_enum(self):
        category = Category("Viandes")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.VIANDE)

        category = Category("ViAnDes")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.VIANDE)

        category = Category("Poissons et fruits de mer")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.POISSON)

        category = Category("Œufs et produits laitiers")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.LAITIER)

        category = Category("Légumineuses")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.LEGUMINEUSE)

        category = Category("Produits à base de soja")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.SOJA)

        category = Category("Légumes et assimilés")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.ASSIMILE)

        category = Category("Céréales et pseudo-céréales")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.CEREALE)

        category = Category("Noix et graines")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.NOIX)

        category = Category("Poudres protéinées")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.POUDRE)

        category = Category("Alternatives végétales")
        self.assertIsInstance(category, Category)
        self.assertIs(category, Category.ALTERNATIVE)

        with self.assertRaises(ValueError):
            category = Category("XYZ")

            self.assertIsInstance(category, Category)


if __name__ == "__main__":
    unittest.main()
