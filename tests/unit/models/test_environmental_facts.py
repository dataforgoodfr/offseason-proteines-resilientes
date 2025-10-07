"""
Unit tests for the 'models.environmental_facts' module.
"""

import unittest

from models.environmental_facts import GreenScore


class TestGreenScore(unittest.TestCase):
    """
    Tests the 'GreenScore' class.
    """

    def test_string_to_enum(self):
        greenscore = GreenScore("A")

        self.assertIsInstance(greenscore, GreenScore)
        self.assertIs(greenscore, GreenScore.A)

        greenscore = GreenScore("b")

        self.assertIsInstance(greenscore, GreenScore)
        self.assertIs(greenscore, GreenScore.B)

        greenscore = GreenScore("a+")

        self.assertIsInstance(greenscore, GreenScore)
        self.assertIs(greenscore, GreenScore.A_PLUS)

        greenscore = GreenScore("a-plus")

        self.assertIsInstance(greenscore, GreenScore)
        self.assertIs(greenscore, GreenScore.A_PLUS)

        greenscore = GreenScore("A_Plus")

        self.assertIsInstance(greenscore, GreenScore)
        self.assertIs(greenscore, GreenScore.A_PLUS)

        with self.assertRaises(ValueError):
            greenscore = GreenScore("G")

            self.assertIsInstance(greenscore, GreenScore)


if __name__ == "__main__":
    unittest.main()
