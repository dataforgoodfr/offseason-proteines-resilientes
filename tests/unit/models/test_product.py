"""
Unit tests for the 'models.product' module.
"""

import unittest

from models.product import NutriScore, NovaScore


class TestNutriScore(unittest.TestCase):
    """
    Tests the 'NutriScore' class.
    """

    def test_string_to_enum(self):
        nutriscore = NutriScore("A")

        self.assertIsInstance(nutriscore, NutriScore)
        self.assertIs(nutriscore, NutriScore.A)

        nutriscore = NutriScore("b")

        self.assertIsInstance(nutriscore, NutriScore)
        self.assertIs(nutriscore, NutriScore.B)


class TestNovaScore(unittest.TestCase):
    """
    Tests the 'NovaScore' class.
    """

    def test_string_to_enum(self):
        novascore = NovaScore(1)

        self.assertIsInstance(novascore, NovaScore)
        self.assertIs(novascore, NovaScore.Group1)

        novascore = NovaScore("3")

        self.assertIsInstance(novascore, NovaScore)
        self.assertIs(novascore, NovaScore.Group3)


if __name__ == "__main__":
    unittest.main()
