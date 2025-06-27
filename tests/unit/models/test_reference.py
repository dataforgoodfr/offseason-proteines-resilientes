"""
Unit tests for the 'models.reference' module.
"""

import unittest

from models.reference import Type


class TestType(unittest.TestCase):
    """
    Tests the 'Type' class.
    """

    def test_string_to_enum(self):
        ref_type = Type("EAN")

        self.assertIsInstance(ref_type, Type)
        self.assertIs(ref_type, Type.EAN)

        ref_type = Type("ean")

        self.assertIsInstance(ref_type, Type)
        self.assertIs(ref_type, Type.EAN)

        ref_type = Type("eAn")

        self.assertIsInstance(ref_type, Type)
        self.assertIs(ref_type, Type.EAN)


if __name__ == "__main__":
    unittest.main()
