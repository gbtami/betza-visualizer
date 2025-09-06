import unittest
import json
from variant_ini_parser import VariantIniParser

class TestVariantIniParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('fsf_built_in_variants_catalog.json', 'r') as f:
            cls.fsf_catalog = json.load(f)

    def test_parse_variants_ini_with_fsf_catalog(self):
        with open('tests/variants.ini', 'r') as f:
            ini_content = f.read()

        parser = VariantIniParser(ini_content, self.fsf_catalog)
        pieces = parser.parse()

        self.assertGreater(len(pieces), 0)

        # Test allwayspawns variant which inherits from chess
        allways_pawn = next((p for p in pieces if p["name"] == "Custom Piece 1" and p["variant"] == "allwayspawns"), None)
        self.assertIsNotNone(allways_pawn)
        self.assertEqual(allways_pawn["betza"], "mWfceFifmnD")

        allways_king = next((p for p in pieces if p["name"] == "King" and p["variant"] == "allwayspawns"), None)
        self.assertIsNotNone(allways_king)
        self.assertEqual(allways_king["betza"], "K")

        # Test 3check-crazyhouse which inherits from crazyhouse
        crazyhouse_knight = next((p for p in self.fsf_catalog if p["name"] == "Knight" and p["variant"] == "crazyhouse"), None)
        self.assertIsNotNone(crazyhouse_knight)

        threecheck_knight = next((p for p in pieces if p["name"] == "Knight" and p["variant"] == "3check-crazyhouse"), None)
        self.assertIsNotNone(threecheck_knight)
        self.assertEqual(threecheck_knight["betza"], crazyhouse_knight["betza"])

        # Let's test a more complex inheritance like 'gothhouse:capablanca'
        gothhouse_knight = next((p for p in pieces if p["name"] == "Knight" and p["variant"] == "gothhouse"), None)
        self.assertIsNotNone(gothhouse_knight)

        capablanca_knight = next((p for p in self.fsf_catalog if p["name"] == "Knight" and p["variant"] == "capablanca"), None)
        self.assertIsNotNone(capablanca_knight)
        self.assertEqual(gothhouse_knight["betza"], capablanca_knight["betza"])

        gothhouse_chancellor = next((p for p in pieces if p["name"] == "Chancellor" and p["variant"] == "gothhouse"), None)
        self.assertIsNotNone(gothhouse_chancellor)
        capablanca_chancellor = next((p for p in self.fsf_catalog if p["name"] == "Chancellor" and p["variant"] == "capablanca"), None)
        self.assertIsNotNone(capablanca_chancellor)
        self.assertEqual(gothhouse_chancellor["betza"], capablanca_chancellor["betza"])

    def test_inheritance_from_catalog(self):
        ini_content = """
[allwayspawns:chess]
customPiece1 = p:mWfceFifmnD
"""
        # A minimal catalog for this test
        piece_catalog = [
            {"name": "King", "variant": "chess", "betza": "K"},
            {"name": "Pawn", "variant": "chess", "betza": "fmWfceF"}
        ]

        parser = VariantIniParser(ini_content, piece_catalog)
        pieces = parser.parse()

        allways_king = next((p for p in pieces if p["name"] == "King" and p["variant"] == "allwayspawns"), None)
        self.assertIsNotNone(allways_king)
        self.assertEqual(allways_king["betza"], "K")

if __name__ == '__main__':
    unittest.main()
