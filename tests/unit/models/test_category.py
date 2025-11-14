"""
Unit tests for the 'models.category' module.
"""

import unittest

from models.category import CategoryValues


class TestCategory(unittest.TestCase):
    """
    Tests the 'Category' class.
    """

    def test_string_to_enum(self):
        category = CategoryValues("Viandes")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.VIANDE)

        category = CategoryValues("Poissons et fruits de mer")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.POISSON)

        category = CategoryValues("Œufs et produits laitiers")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.LAITIER)

        category = CategoryValues("Légumineuses")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.LEGUMINEUSE)

        category = CategoryValues("Produits à base de soja")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.SOJA)

        category = CategoryValues("Légumes et assimilés")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.LEGUME)

        category = CategoryValues("Céréales et pseudo-céréales")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.CEREALE)

        category = CategoryValues("Noix et graines")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.NOIX)

        category = CategoryValues("Poudres protéinées")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.POUDRE)

        category = CategoryValues("Alternatives végétales")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.ALTERNATIVE)

        with self.assertRaises(ValueError):
            category = CategoryValues("XYZ")

            self.assertIsInstance(category, CategoryValues)


if __name__ == "__main__":
    unittest.main()
