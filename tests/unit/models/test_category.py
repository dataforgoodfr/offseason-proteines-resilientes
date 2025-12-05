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
        self.assertIs(category, CategoryValues.VIANDES)

        category = CategoryValues("Poissons et fruits de mer")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.POISSONS)

        category = CategoryValues("Œufs et produits laitiers")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.OEUFS_PRODUITS_LAITIERS)

        category = CategoryValues("Légumineuses")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.LEGUMINEUSES)

        category = CategoryValues("Produits à base de soja")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.SOJA)

        category = CategoryValues("Légumes et assimilés")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.LEGUMES)

        category = CategoryValues("Céréales et pseudo-céréales")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.CEREALES)

        category = CategoryValues("Noix et graines")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.NOIX)

        category = CategoryValues("Poudres protéinées")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.POUDRES)

        category = CategoryValues("Alternatives végétales")
        self.assertIsInstance(category, CategoryValues)
        self.assertIs(category, CategoryValues.ALTERNATIVES)

        with self.assertRaises(ValueError):
            category = CategoryValues("XYZ")

            self.assertIsInstance(category, CategoryValues)


if __name__ == "__main__":
    unittest.main()
