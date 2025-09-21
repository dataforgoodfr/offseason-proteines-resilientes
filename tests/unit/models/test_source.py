"""
Unit tests for the 'models.source' module.
"""

import unittest

from models.source import Origin


class TestOrigin(unittest.TestCase):
    """
    Tests the 'Origin' class.
    """

    def test_string_to_enum(self):
        origin = Origin("OpenFoodFacts")

        self.assertIsInstance(origin, Origin)
        self.assertIs(origin, Origin.OPEN_FOOD_FACTS)

        origin = Origin("aUChan")

        self.assertIsInstance(origin, Origin)
        self.assertIs(origin, Origin.AUCHAN)

        with self.assertRaises(ValueError):
            origin = Origin("XYZ")

            self.assertIsInstance(origin, Origin)


if __name__ == "__main__":
    unittest.main()
