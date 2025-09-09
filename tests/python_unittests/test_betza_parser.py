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
        rook_move = next(m for m in moves if (m['x'], m['y']) == (0, 5))
        self.assertEqual(rook_move["move_type"], "move")
        knight_move = next(m for m in moves if (m['x'], m['y']) == (2, 1))
        self.assertEqual(knight_move["move_type"], "capture")


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

    def test_nightrider_shorthand_NN(self):
        """Tests that 'NN' is parsed as a Nightrider (N0)."""
        moves = self.parser.parse("NN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertEqual(len(moves), 8 * self.parser.infinity_cap)
        self.assertIn((4, 2), move_coords)
        self.assertIn((-4, -2), move_coords)


class TestAdvancedModifiers(unittest.TestCase):
    """Tests for nuanced modifier rules like quadrants and doubled letters."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_quadrant_modifier_flN(self):
        moves = self.parser.parse("flN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (-2, 1)})

    def test_shogi_knight_fN(self):
        """Tests that 'fN' produces the forward-only Shogi Knight moves."""
        moves = self.parser.parse("fN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (1, 2)})

    def test_doubled_modifier_ffN_is_equivalent_to_fN(self):
        """Tests that 'ffN' is parsed the same as 'fN' for compatibility."""
        moves_fN = self.parser.parse("fN")
        moves_ffN = self.parser.parse("ffN")
        self.assertSetEqual(
            {(m['x'], m['y']) for m in moves_fN},
            {(m['x'], m['y']) for m in moves_ffN},
        )

    def test_half_modifier_fhN(self):
        """Tests that 'fhN' produces all 4 forward Knight moves."""
        moves = self.parser.parse("fhN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (1, 2), (-2, 1), (2, 1)})

    def test_union_of_doubled_modifiers_ffrrN(self):
        """Tests that 'ffrrN' produces a union of forward and right moves."""
        moves = self.parser.parse("ffrrN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (1, 2), (2, 1), (2, -1)})

    def test_doubled_modifier_srrC_sideways_camel(self):
        moves = self.parser.parse("srrC")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(3, 1), (3, -1), (-3, 1), (-3, -1)})

    def test_combined_doubled_and_quadrant_fflN(self):
        moves = self.parser.parse("fflN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2)})

    # --- NEW TESTS FOR n AND j MODIFIERS ---
    def test_non_jumping_modifier_nN(self):
        """Tests that the 'n' modifier correctly flags moves as non-jumping."""
        moves = self.parser.parse("nN")
        self.assertEqual(len(moves), 8)
        self.assertTrue(all(m['jump_type'] == "non-jumping" for m in moves))

    def test_jumping_modifier_jD(self):
        """Tests that the 'j' modifier correctly flags moves as jumping."""
        moves = self.parser.parse("jD")
        self.assertEqual(len(moves), 4)
        self.assertTrue(all(m['jump_type'] == "jumping" for m in moves))

    def test_default_leaper_is_jumping(self):
        """Tests that a leaper with no modifiers defaults to jumping."""
        moves = self.parser.parse("N")
        self.assertEqual(len(moves), 8)
        self.assertTrue(all(m['jump_type'] == "jumping" for m in moves))

    def test_default_sliding_rider_is_non_jumping(self):
        """Tests that a sliding rider (e.g., Rook) defaults to non-jumping."""
        moves = self.parser.parse("R")  # R is an alias for W0
        self.assertGreater(len(moves), 0)
        self.assertTrue(all(m['jump_type'] == "non-jumping" for m in moves))

    def test_default_jumping_rider_is_jumping(self):
        """Tests that a jumping rider (e.g., Nightrider) defaults to jumping."""
        moves = self.parser.parse("NN")  # NN is an alias for N0
        self.assertGreater(len(moves), 0)
        self.assertTrue(all(m['jump_type'] == "jumping" for m in moves))

    def test_pawn_modifier_pNN(self):
        """Tests that the 'p' modifier works correctly on a Nightrider."""
        moves = self.parser.parse("pNN")
        self.assertGreater(len(moves), 0)
        # For 'p', the move type is conditional on blockers, so the parser
        # should return the default 'move_capture', and the rendering logic
        # will handle the rest.
        self.assertTrue(all(m['move_type'] == "move_capture" for m in moves))
        self.assertTrue(all(m['hop_type'] == "p" for m in moves))


class TestDirectionalShorthand(unittest.TestCase):
    """Tests for the 'v' (vertical) and 's' (sideways) shorthand modifiers."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_vertical_modifier_vN_on_hippogonal(self):
        """Tests that 'vN' produces vertical-only knight moves."""
        moves = self.parser.parse("vN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-1, 2), (1, 2), (-1, -2), (1, -2)})

    def test_sideways_modifier_sN_on_hippogonal(self):
        """Tests that 'sN' produces sideways-only knight moves."""
        moves = self.parser.parse("sN")
        move_coords = {(m['x'], m['y']) for m in moves}
        self.assertSetEqual(move_coords, {(-2, 1), (2, 1), (-2, -1), (2, -1)})

    def test_vertical_modifier_vR(self):
        """Tests that 'vR' produces only vertical moves for a Rook."""
        moves = self.parser.parse("vR")
        move_coords = {(m['x'], m['y']) for m in moves}
        expected_coords = set()
        for i in range(1, self.parser.infinity_cap + 1):
            expected_coords.add((0, i))
            expected_coords.add((0, -i))
        self.assertSetEqual(move_coords, expected_coords)

    def test_sideways_modifier_sR(self):
        """Tests that 'sR' produces only horizontal moves for a Rook."""
        moves = self.parser.parse("sR")
        move_coords = {(m['x'], m['y']) for m in moves}
        expected_coords = set()
        for i in range(1, self.parser.infinity_cap + 1):
            expected_coords.add((i, 0))
            expected_coords.add((-i, 0))
        self.assertSetEqual(move_coords, expected_coords)


if __name__ == "__main__":
    unittest.main()


class TestModifierScope(unittest.TestCase):
    """Tests that modifiers are correctly scoped to their respective atoms."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_modifier_does_not_leak_to_next_atom(self):
        """
        Tests that a modifier for one atom does not affect a subsequent, unmodified atom.
        In 'fBW', the 'f' should only apply to 'B', not to 'W'.
        """
        moves = self.parser.parse("fBW")
        move_coords = {(m['x'], m['y']) for m in moves}

        # Check that 'W' moves are not restricted by the 'f' modifier
        self.assertIn((0, -1), move_coords)  # Backward Wazir move
        self.assertIn((1, 0), move_coords)  # Sideways Wazir move
        self.assertIn((-1, 0), move_coords)  # Sideways Wazir move

        # Check that 'B' moves are restricted by taking a sample
        self.assertNotIn((1, -1), move_coords)  # Backward Bishop move

    def test_modifiers_apply_to_all_parts_of_compound_piece(self):
        """
        Tests that a modifier preceding a compound piece (like 'K') applies
        to all of its components (W and F).
        """
        moves = self.parser.parse("fK")
        move_coords = {(m['x'], m['y']) for m in moves}

        # King moves: (0,1), (1,1), (-1,1)
        expected = {(0, 1), (1, 1), (-1, 1)}
        self.assertSetEqual(move_coords, expected)


class TestMultiDirectionalModifiers(unittest.TestCase):
    """Tests for multiple, non-intersecting directional modifiers."""

    def setUp(self):
        self.parser = BetzaParser()

    def test_janggi_pawn_sfW(self):
        """Tests the Janggi pawn 'sfW', which should move forward or sideways."""
        moves = self.parser.parse("sfW")
        move_coords = {(m['x'], m['y']) for m in moves}
        # Should have forward (0,1), left (-1,0), and right (1,0) moves.
        self.assertSetEqual(move_coords, {(0, 1), (-1, 0), (1, 0)})

    def test_charging_rook_frlR(self):
        """Tests 'frlR', forward and sideways Rook moves."""
        moves = self.parser.parse("frlR")
        move_coords = {(m['x'], m['y']) for m in moves}
        expected = set()
        for i in range(1, self.parser.infinity_cap + 1):
            expected.add((0, i))  # Forward
            expected.add((i, 0))  # Right
            expected.add((-i, 0))  # Left
        self.assertSetEqual(move_coords, expected)

    def test_fibnif_fbNF(self):
        """Tests the Fibnif 'fbNF', which moves as a Ferz or the 4 most vertical Knight moves."""
        moves = self.parser.parse("fbNF")
        move_coords = {(m['x'], m['y']) for m in moves}
        expected = {
            # Ferz moves
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
            # Vertically longest Knight moves (ffN + bbN)
            (1, 2),
            (-1, 2),
            (1, -2),
            (-1, -2),
        }
        self.assertEqual(len(move_coords), 8)
        self.assertSetEqual(move_coords, expected)

    def test_charging_rook_part_2_rlbK(self):
        """Tests 'rlbK', sideways and backward King moves."""
        moves = self.parser.parse("rlbK")
        move_coords = {(m['x'], m['y']) for m in moves}
        expected = {
            # Sideways King
            (1, 0),
            (-1, 0),
            (1, -1),
            (-1, -1),
            # Backward King
            (0, -1),
            (1, -1),
            (-1, -1),
        }
        self.assertSetEqual(move_coords, expected)
