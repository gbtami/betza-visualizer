import unittest
import json
from variant_ini_parser import VariantIniParser

class TestVariantIniParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('fsf_built_in_variants_catalog.json', 'r') as f:
            cls.fsf_catalog = json.load(f)
        with open('fsf_built_in_variant_properties.json', 'r') as f:
            cls.fsf_variant_properties = json.load(f)

    def test_parse_variants_ini_with_fsf_catalog(self):
        with open('tests/variants.ini', 'r') as f:
            ini_content = f.read()

        parser = VariantIniParser(ini_content, self.fsf_catalog, self.fsf_variant_properties)
        pieces = parser.parse()

        self.assertGreater(len(pieces), 0)

        # Test allwayspawns variant which inherits from chess
        allways_pawn = next((p for p in pieces if p["name"] == "Allwayspawns-p" and p["variant"] == "allwayspawns"), None)
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
        variant_properties = {
            "chess": {"double_step": True}
        }

        parser = VariantIniParser(ini_content, piece_catalog, variant_properties)
        pieces = parser.parse()

        allways_king = next((p for p in pieces if p["name"] == "King" and p["variant"] == "allwayspawns"), None)
        self.assertIsNotNone(allways_king)
        self.assertEqual(allways_king["betza"], "K")

        allways_pawn = next((p for p in pieces if p["name"] == "Allwayspawns-p" and p["variant"] == "allwayspawns"), None)
        self.assertIsNotNone(allways_pawn)
        self.assertEqual(allways_pawn["betza"], "mWfceFifmnD")

    def test_king_override(self):
        ini_content = """
[centaurking:chess]
king = k:KN
"""
        piece_catalog = [
            {"name": "King", "variant": "chess", "betza": "K"},
            {"name": "Pawn", "variant": "chess", "betza": "fmWfceF"}
        ]
        variant_properties = {
            "chess": {"double_step": True}
        }
        parser = VariantIniParser(ini_content, piece_catalog, variant_properties)
        pieces = parser.parse()

        centaur_king = next((p for p in pieces if p['name'] == 'King' and p['variant'] == 'centaurking'), None)
        self.assertIsNotNone(centaur_king)
        self.assertEqual(centaur_king['betza'], 'KN')

    def test_king_override_inheritance(self):
        ini_content = """
[basevariant]
king = k:N

[childvariant:basevariant]
pawn = p:fW
"""
        piece_catalog = []
        variant_properties = {}
        parser = VariantIniParser(ini_content, piece_catalog, variant_properties)
        pieces = parser.parse()

        child_king = next((p for p in pieces if p['name'] == 'King' and p['variant'] == 'childvariant'), None)
        self.assertIsNotNone(child_king)
        self.assertEqual(child_king['betza'], 'N')

    def test_double_step_logic(self):
        ini_content = """
[withdoublestep:chess]
king = k:K

[withoutdoublestep:chess]
doubleStep = false
"""
        piece_catalog = [
            {"name": "Pawn", "variant": "chess", "betza": "fmWfceF"}
        ]
        variant_properties = {
            "chess": {"double_step": True}
        }
        parser = VariantIniParser(ini_content, piece_catalog, variant_properties)
        pieces = parser.parse()

        pawn1 = next((p for p in pieces if p['variant'] == 'withdoublestep' and p['name'] == 'Pawn'), None)
        self.assertIsNotNone(pawn1)
        self.assertTrue('imfnA' in pawn1['betza'])

        pawn2 = next((p for p in pieces if p['variant'] == 'withoutdoublestep' and p['name'] == 'Pawn'), None)
        self.assertIsNotNone(pawn2)
        self.assertFalse('imfnA' in pawn2['betza'])


if __name__ == '__main__':
    unittest.main()
