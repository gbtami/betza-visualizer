import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from betza_parser import BetzaParser


class TestOriginalCases(unittest.TestCase):
    """Contains the previous test suite to ensure no regressions."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_simple_piece_with_suffix(self):
        moves = self.parser.parse("W3")
        self.assertEqual(len(moves), 12)

    def test_abbreviation_with_suffix_B3(self):
        moves = self.parser.parse("B3")
        self.assertEqual(len(moves), 12)

    def test_compound_abbreviation_with_suffix_Q2(self):
        moves = self.parser.parse("Q2")
        self.assertEqual(len(moves), 16)

    def test_stateful_modifiers_on_compound_piece(self):
        moves = self.parser.parse("mRcN")
        rook_move = next(m for m in moves if m[:2] == (0, 5))
        self.assertEqual(rook_move[2], "move")
        knight_move = next(m for m in moves if m[:2] == (2, 1))
        self.assertEqual(knight_move[2], "capture")


class TestFairyStockfishPieces(unittest.TestCase):
    """Comprehensive test suite for Fairy-Stockfish pieces using unambiguous notation."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_pawn(self):
        moves = self.parser.parse("fmWfceF")
        self.assertEqual(len(moves), 3)

    def test_knight(self):
        self.assertEqual(len(self.parser.parse("N")), 8)

    def test_bishop(self):
        self.assertEqual(len(self.parser.parse("B")), 4 * self.parser.infinity_cap)

    def test_rook(self):
        self.assertEqual(len(self.parser.parse("R")), 4 * self.parser.infinity_cap)

    def test_queen(self):
        self.assertEqual(len(self.parser.parse("Q")), 8 * self.parser.infinity_cap)

    def test_king(self):
        self.assertEqual(len(self.parser.parse("K")), 8)

    def test_archbishop(self):
        moves = self.parser.parse("BN")
        self.assertEqual(len(moves), (4 * self.parser.infinity_cap) + 8)

    def test_empress(self):
        self.assertEqual(len(self.parser.parse("E")), (4 * self.parser.infinity_cap) + 8)

    def test_ferz(self):
        self.assertEqual(len(self.parser.parse("F")), 4)

    def test_wazir(self):
        self.assertEqual(len(self.parser.parse("W")), 4)

    def test_camel(self):
        self.assertEqual(len(self.parser.parse("C")), 8)

    def test_zebra(self):
        self.assertEqual(len(self.parser.parse("Z")), 8)

    def test_tripper(self):
        self.assertEqual(len(self.parser.parse("G")), 4)

    def test_alibaba(self):
        moves = self.parser.parse("J")
        self.assertEqual(len(moves), 8)

    def test_berolina_pawn(self):
        moves = self.parser.parse("fmFfceW")
        self.assertEqual(len(moves), 3)

    def test_spider_pawn(self):
        moves = self.parser.parse("mFmcW")
        self.assertEqual(len(moves), 8)

    def test_champion(self):
        moves = self.parser.parse("WAD")
        self.assertEqual(len(moves), 12)

    def test_wizard(self):
        moves = self.parser.parse("M")
        self.assertEqual(len(moves), 12)


class TestAdvancedModifiers(unittest.TestCase):
    """Tests for nuanced modifier rules like quadrants and doubled letters."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_quadrant_modifier_flN(self):
        moves = self.parser.parse("flN")
        move_coords = {m[:2] for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (-2, 1)})

    def test_doubled_modifier_ffN_shogi_knight(self):
        moves = self.parser.parse("ffN")
        move_coords = {m[:2] for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (1, 2)})

    def test_doubled_modifier_srrC_sideways_camel(self):
        moves = self.parser.parse("srrC")
        move_coords = {m[:2] for m in moves}
        self.assertSetEqual(move_coords, {(3, 1), (3, -1), (-3, 1), (-3, -1)})

    def test_combined_doubled_and_quadrant_fflN(self):
        moves = self.parser.parse("fflN")
        move_coords = {m[:2] for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2)})

    # --- NEW TESTS FOR n AND j MODIFIERS ---
    def test_non_jumping_modifier_nN(self):
        """Tests that the 'n' modifier correctly flags moves as non-jumping."""
        moves = self.parser.parse("nN")
        self.assertEqual(len(moves), 8)
        # move[4] is the jump_type
        self.assertTrue(all(move[4] == "non-jumping" for move in moves))

    def test_jumping_modifier_jD(self):
        """Tests that the 'j' modifier correctly flags moves as jumping."""
        moves = self.parser.parse("jD")
        self.assertEqual(len(moves), 4)
        # move[4] is the jump_type
        self.assertTrue(all(move[4] == "jumping" for move in moves))


if __name__ == "__main__":
    unittest.main()
