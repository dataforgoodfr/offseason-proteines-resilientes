"""
Unit tests for the 'models.product' module.
"""

import unittest

from models.product import QuantityUnit


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


if __name__ == "__main__":
    unittest.main()
