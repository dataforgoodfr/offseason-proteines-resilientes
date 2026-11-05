"""
Unit tests for the 'off_data_collector.cli' module.
"""

import unittest
from json import loads as load_json

from models.environmental_facts import GreenScore
from models.nutrition_facts import NovaScore, NutriScore
from models.source import Origin
from off_data_collector.cli import __create_new_source as create_new_source

# Taken from an Open Food Facts API v3 response.
DATA_SAMPLE = """
{
  "brands": "Super U",
  "carbohydrates_100g": 0,
  "ecoscore_data": {
    "agribalyse": {
      "co2_agriculture": 3.75,
      "co2_consumption": 0.00683,
      "co2_distribution": 0.0406,
      "co2_packaging": 0.378,
      "co2_processing": 1.09,
      "co2_total": 5.58,
      "co2_transportation": 0.317
    }
  },
  "ecoscore_grade": "d",
  "energy-kcal_100g": 124,
  "fat_100g": 3.93,
  "nova_group": 1,
  "nutriments_estimated": {
    "alcohol_100g": 0,
    "alpha-linolenic-acid_100g": 0.079,
    "arachidonic-acid_100g": 0.069,
    "butyric-acid_100g": 0,
    "calcium_100g": 0.00969,
    "capric-acid_100g": 0,
    "caproic-acid_100g": 0,
    "caprylic-acid_100g": 0,
    "cholesterol_100g": 0.0763,
    "crude-ash_100g": 0.98,
    "docosahexaenoic-acid_100g": 0.022,
    "eicosapentaenoic-acid_100g": 0.0078,
    "fiber_100g": 0,
    "fructose_100g": 0,
    "glucose_100g": 0,
    "lactose_100g": 0,
    "lauric-acid_100g": 0.017,
    "linoleic-acid_100g": 1.38,
    "maltose_100g": 0,
    "monounsaturated-fat_100g": 4.52,
    "myristic-acid_100g": 0.08,
    "oleic-acid_100g": 2.66,
    "palmitic-acid_100g": 2.11,
    "pantothenic-acid_100g": 0.00098,
    "polyols_100g": 0,
    "polyunsaturated-fat_100g": 2.34,
    "potassium_100g": 0.227,
    "stearic-acid_100g": 0.6,
    "sucrose_100g": 0,
    "vitamin-b1_100g": 0.00012,
    "vitamin-b2_100g": 0.00048,
    "vitamin-b6_100g": 0.00054,
    "vitamin-pp_100g": 0.00704,
    "water_100g": 68.1
  },
  "nutrition_data": "on",
  "nutrition_data_per": "100g",
  "nutrition_data_prepared_per": "100g",
  "nutrition_grade_fr": "a",
  "product_name": "Filet de poulet nature",
  "proteins_100g": 22.2,
  "salt_100g": 0,
  "saturated-fat_100g": 0.7,
  "sugars_100g": 0,
  "product_quantity": "2.5",
  "product_quantity_unit": "kg"
}
"""


class TestCreateNewSource(unittest.TestCase):
    """
    Tests the '__create_new_source' function.
    """

    def test_parse_data(self):
        reference = "5413458060185"
        data = load_json(DATA_SAMPLE)

        source = create_new_source(reference, data)

        self.assertIs(source.origin, Origin.OPEN_FOOD_FACTS)
        self.assertEqual(
            source.url, f"https://fr.openfoodfacts.org/product/{reference}/"
        )

        self.assertEqual(source.nutrition_facts.nutriscore, NutriScore.A)
        self.assertEqual(source.nutrition_facts.novascore, NovaScore.Group1)
        self.assertEqual(source.nutrition_facts.calories_100g, 124.0)
        self.assertEqual(source.nutrition_facts.fat_100g, 3.93)
        self.assertEqual(source.nutrition_facts.saturated_fat_100g, 0.7)
        self.assertEqual(source.nutrition_facts.carbohydrates_100g, 0.0)
        self.assertEqual(source.nutrition_facts.sugars_100g, 0.0)
        self.assertEqual(source.nutrition_facts.fiber_100g, None)
        self.assertEqual(source.nutrition_facts.protein_100g, 22.2)
        self.assertEqual(source.nutrition_facts.salt_100g, 0.0)

        self.assertEqual(source.environmental_facts.green_score, GreenScore.D)

        self.assertEqual(source.environmental_facts.co2_agriculture, 3.75)
        self.assertEqual(source.environmental_facts.co2_consumption, 0.00683)
        self.assertEqual(source.environmental_facts.co2_distribution, 0.0406)
        self.assertEqual(source.environmental_facts.co2_packaging, 0.378)
        self.assertEqual(source.environmental_facts.co2_processing, 1.09)
        self.assertEqual(source.environmental_facts.co2_total, 5.58)
        self.assertEqual(source.environmental_facts.co2_transportation, 0.317)


if __name__ == "__main__":
    unittest.main()
