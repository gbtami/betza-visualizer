import json
import unittest
from pathlib import Path

class TestFsfBuiltInVariantsCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog_path = Path(__file__).parent.parent.parent / 'fsf_built_in_variants_catalog.json'
        with open(catalog_path, 'r') as f:
            cls.catalog = json.load(f)

    def get_pieces_for_variant(self, variant_name):
        return [p for p in self.catalog if p['variant'] == variant_name]

    def test_chess_variant(self):
        pieces = self.get_pieces_for_variant('chess')
        piece_names = {p['name'] for p in pieces}
        self.assertEqual(len(pieces), 6)
        self.assertEqual(piece_names, {'Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King'})

    def test_berolina_variant(self):
        pieces = self.get_pieces_for_variant('berolina')
        piece_names = {p['name'] for p in pieces}

        # Should have 6 pieces total
        self.assertEqual(len(pieces), 6)

        # Should not have the standard Pawn
        self.assertNotIn('Pawn', piece_names)

        # Should have the custom "Berolina Pawn"
        self.assertIn('Berolina Pawn', piece_names)

        # Check other standard pieces are present
        self.assertIn('Knight', piece_names)
        self.assertIn('Bishop', piece_names)
        self.assertIn('Rook', piece_names)
        self.assertIn('Queen', piece_names)
        self.assertIn('King', piece_names)

    def test_capablanca_variant(self):
        pieces = self.get_pieces_for_variant('capablanca')
        piece_names = {p['name'] for p in pieces}

        # Should have 8 pieces total (6 standard + Archbishop + Chancellor)
        self.assertEqual(len(pieces), 8)

        # Check for the two special pieces
        self.assertIn('Archbishop', piece_names)
        self.assertIn('Chancellor', piece_names)

        # Check that all standard pieces are also present
        self.assertTrue({'Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King'}.issubset(piece_names))

    def test_shogi_variant(self):
        pieces = self.get_pieces_for_variant('shogi')
        piece_names = {p['name'] for p in pieces}

        expected_pieces = {
            'Shogi Pawn', 'Lance', 'Shogi Knight', 'Silver', 'Gold', 'Bishop',
            'Rook', 'King', 'Dragon Horse', 'Dragon'
        }

        self.assertEqual(len(pieces), 10)
        self.assertEqual(piece_names, expected_pieces)

if __name__ == '__main__':
    unittest.main()
