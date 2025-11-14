"""
Unit tests for the 'models.product' module.
"""

import unittest

from models.product import QuantityUnit, Category, Department


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


class TestDepartment(unittest.TestCase):
    """
    Tests the 'Department' class.
    """

    def test_string_to_enum(self):
        department = Department("Produits laitiers, oeufs, fromages")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.LAITIER)

        department = Department("Boucherie, volaille, poissonnerie")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.VIANDE)

        department = Department("Charcuterie, traiteur")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.CHARCUTERIE)

        department = Department("Marché frais")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.FRAIS)

        department = Department("Epicerie salée")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.EPICERIE)

        department = Department("Fruits, légumes")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.FRUIT_LEGUME)

        department = Department("Surgelés")
        self.assertIsInstance(department, Department)
        self.assertIs(department, Department.SURGELE)

        with self.assertRaises(ValueError):
            department = Department("XYZ")

            self.assertIsInstance(department, Department)


if __name__ == "__main__":
    unittest.main()
