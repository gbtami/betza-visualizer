import re
from typing import Dict, List, Tuple, Set, Optional


class BetzaParser:
    """
    Parses a Betza notation string and returns a list of possible moves with their properties.
    """

    def __init__(self):
        self.atoms: Dict[str, Tuple[int, int]] = {
            "W": (1, 0),
            "F": (1, 1),
            "D": (2, 0),
            "N": (2, 1),
            "A": (2, 2),
            "H": (3, 0),
            "C": (3, 1),
            "Z": (3, 2),
            "G": (3, 3),
        }
        self.compound_aliases: Dict[str, str] = {
            "B": "F0",
            "R": "W0",
            "Q": "W0F0",
            "K": "W1F1",
            "E": "RN",
            "J": "AD",
            "M": "FC",
        }
        self.infinity_cap = 12
        self.jumping_atoms = {"N", "C", "Z"}

    def parse(
        self, notation: str, board_size: Optional[int] = None
    ) -> List[Dict]:
        """
        Parses notation. Returns a list of move dictionaries.
        """
        moves = []
        token_worklist = re.findall(r"[a-z]+|[A-Z]\d*", notation)
        current_mods = ""

        while token_worklist:
            token = token_worklist.pop(0)

            if token.islower():
                current_mods = token
                continue

            match = re.match(r"([A-Z])(\d*)", token)
            letter, suffix = match.groups()

            # Nightrider shorthand: 'NN' -> 'N0'
            if suffix == "" and token_worklist and token_worklist[0] == letter:
                token_worklist.pop(0)
                token_worklist.insert(0, f"{letter}0")
                continue

            if letter in self.compound_aliases:
                expansion = self.compound_aliases[letter]
                if suffix:
                    expansion = re.sub(r"([A-Z])\d*", rf"\g<1>{suffix}", expansion)

                new_tokens = re.findall(r"[A-Z]\d*", expansion)

                if current_mods:
                    prefixed_tokens = []
                    for t in new_tokens:
                        prefixed_tokens.append(current_mods)
                        prefixed_tokens.append(t)
                    new_tokens = prefixed_tokens

                token_worklist[0:0] = new_tokens
                current_mods = ""
                continue

            if letter not in self.atoms:
                continue

            mods_for_this_atom = current_mods
            current_mods = ""

            atom, count_str = letter, suffix

            # Determine move_type
            move_type = "move_capture"
            if "m" in mods_for_this_atom and "c" not in mods_for_this_atom:
                move_type = "move"
            elif "c" in mods_for_this_atom and "m" not in mods_for_this_atom:
                move_type = "capture"
            elif "m" in mods_for_this_atom and "c" in mods_for_this_atom:
                move_type = "capture" if mods_for_this_atom.rfind("c") > mods_for_this_atom.rfind("m") else "move"

            # Determine hop_type for riders
            hop_type = "p" if "p" in mods_for_this_atom else "g" if "g" in mods_for_this_atom else None

            # Determine jump_type based on whether it's a rider or a leaper
            is_rider = count_str == "0"
            if is_rider:
                # Rider type depends on the base atom
                if atom in self.jumping_atoms:
                    jump_type = "jumping"
                else:
                    jump_type = "non-jumping"
            else:
                # Leapers are jumping by default, unless they are lame (n)
                jump_type = "jumping"
                if "n" in mods_for_this_atom:
                    jump_type = "non-jumping"

            if count_str == "0":
                max_steps = board_size // 2 if board_size is not None else self.infinity_cap
            elif count_str == "":
                max_steps = 1
            else:
                max_steps = int(count_str)
            x_atom, y_atom = self.atoms[atom]
            base_directions = self._get_directions(x_atom, y_atom)
            allowed_directions = self._filter_directions(base_directions, mods_for_this_atom, atom)

            for i in range(1, max_steps + 1):
                for dx, dy in allowed_directions:
                    moves.append(
                        {
                            "x": dx * i,
                            "y": dy * i,
                            "move_type": move_type,
                            "hop_type": hop_type,
                            "jump_type": jump_type,
                            "atom": atom,
                            "atom_coords": {"x": x_atom, "y": y_atom},
                        }
                    )

        return moves

    def _get_directions(self, x: int, y: int) -> Set[Tuple[int, int]]:
        directions = set()
        for sx in [-1, 1]:
            for sy in [-1, 1]:
                directions.add((x * sx, y * sy))
                directions.add((y * sx, x * sy))
        return directions

    def _filter_directions(self, directions: Set[Tuple[int, int]], mods: str, atom: str) -> Set[Tuple[int, int]]:
        x_atom, y_atom = self.atoms[atom]
        is_hippogonal = x_atom != y_atom and x_atom * y_atom != 0
        if is_hippogonal:
            # For hippogonal pieces (N, C, Z), single-letter directional modifiers
            # are treated as if they were doubled, per Fairy-Stockfish's interpretation.
            # e.g., fN becomes ffN. This is not applied to quadrant modifiers like 'l' in 'ffl'.
            dir_mod_regex = r"ff|bb|ll|rr|f[lr]|b[lr]|l[fb]|r[fb]|[fblr]"
            dir_mods_found = re.findall(dir_mod_regex, mods)
            non_dir_mods = re.sub(dir_mod_regex, "", mods)

            # Detect if we have a combination of a double modifier and a single one (e.g., 'ff' and 'l' in 'ffl')
            is_quadrant_combo = False
            if len(dir_mods_found) > 1:
                has_double = any(len(m) == 2 and m[0] == m[1] for m in dir_mods_found)
                has_single = any(len(m) == 1 for m in dir_mods_found)
                if has_double and has_single:
                    is_quadrant_combo = True

            processed_dir_mods = ""
            for m in dir_mods_found:
                if len(m) == 1 and not is_quadrant_combo:
                    processed_dir_mods += m * 2
                else:
                    processed_dir_mods += m

            mods = processed_dir_mods + non_dir_mods

        # The Fibnif special case `fbN` is now generalized by the hippogonal logic above.

        if "s" in mods:
            mods += "lr"
        if "v" in mods:
            mods += "fb"

        dir_mods = "".join(c for c in mods if c in "fblr")
        is_orthogonal = x_atom * y_atom == 0

        if not dir_mods:
            filtered = directions
        else:
            filtered = set()
            has_v_mod = any(c in "fb" for c in dir_mods)
            has_h_mod = any(c in "lr" for c in dir_mods)

            for x, y in directions:
                v_valid = (not has_v_mod) or (("f" in dir_mods and y > 0) or ("b" in dir_mods and y < 0))
                h_valid = (not has_h_mod) or (("l" in dir_mods and x < 0) or ("r" in dir_mods and x > 0))

                is_union = is_orthogonal and has_v_mod and has_h_mod
                if is_union:
                    if v_valid or h_valid:
                        filtered.add((x, y))
                else:
                    if v_valid and h_valid:
                        filtered.add((x, y))

        constrain_double_vertical = "ff" in mods or "bb" in mods
        constrain_double_horizontal = "ll" in mods or "rr" in mods

        if not constrain_double_vertical and not constrain_double_horizontal:
            return filtered

        final_filtered = set()
        for x, y in filtered:
            is_valid = True
            if constrain_double_vertical and abs(y) <= abs(x):
                is_valid = False
            if constrain_double_horizontal and abs(x) <= abs(y):
                is_valid = False

            if is_valid:
                final_filtered.add((x, y))

        return final_filtered
