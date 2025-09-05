import unittest
from variant_ini_parser import VariantIniParser

class TestVariantIniParser(unittest.TestCase):

    def test_parse_variants_ini(self):
        ini_content = """
[test_variant]
pawn = p
knight = n:N
customPiece1 = x:mybetza

[test_variant2:test_variant]
knight = n:anotherbetza
customPiece2 = y:anotherbetza2
"""
        parser = VariantIniParser(ini_content)
        pieces = parser.parse()

        self.assertEqual(len(pieces), 7)

        # test_variant pieces
        pawn = next((p for p in pieces if p["name"] == "Pawn" and p["variant"] == "test_variant"), None)
        self.assertIsNotNone(pawn)
        self.assertEqual(pawn["betza"], "fmWfceF")

        knight1 = next((p for p in pieces if p["name"] == "Knight" and p["variant"] == "test_variant"), None)
        self.assertIsNotNone(knight1)
        self.assertEqual(knight1["betza"], "N")

        custom1 = next((p for p in pieces if p["name"] == "Custom Piece 1" and p["variant"] == "test_variant"), None)
        self.assertIsNotNone(custom1)
        self.assertEqual(custom1["betza"], "mybetza")

        # test_variant2 pieces (should inherit and override)
        pawn2 = next((p for p in pieces if p["name"] == "Pawn" and p["variant"] == "test_variant2"), None)
        self.assertIsNotNone(pawn2)
        self.assertEqual(pawn2["betza"], "fmWfceF")

        knight2 = next((p for p in pieces if p["name"] == "Knight" and p["variant"] == "test_variant2"), None)
        self.assertIsNotNone(knight2)
        self.assertEqual(knight2["betza"], "anotherbetza")

        custom1_inherited = next((p for p in pieces if p["name"] == "Custom Piece 1" and p["variant"] == "test_variant2"), None)
        self.assertIsNotNone(custom1_inherited)
        self.assertEqual(custom1_inherited["betza"], "mybetza")

        custom2 = next((p for p in pieces if p["name"] == "Custom Piece 2" and p["variant"] == "test_variant2"), None)
        self.assertIsNotNone(custom2)
        self.assertEqual(custom2["betza"], "anotherbetza2")

if __name__ == '__main__':
    unittest.main()
