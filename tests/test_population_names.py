import unittest

from src.ingest_population import normalise_abs_lga_name, normalise_tmr_lga_name


class LgaNameTests(unittest.TestCase):
    def test_standard_suffixes(self):
        self.assertEqual(normalise_tmr_lga_name("Brisbane City"), "brisbane")
        self.assertEqual(normalise_tmr_lga_name("Rockhampton Region"), "rockhampton")
        self.assertEqual(normalise_tmr_lga_name("Cherbourg Aboriginal Shire"), "cherbourg")

    def test_abs_qualifier(self):
        self.assertEqual(normalise_abs_lga_name("Central Highlands (Qld)"), "central highlands")


if __name__ == "__main__":
    unittest.main()
