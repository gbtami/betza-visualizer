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

            is_initial_only = "i" in mods_for_this_atom

            for i in range(1, max_steps + 1):
                for dx, dy in allowed_directions:
                    move = {
                        "x": dx * i,
                        "y": dy * i,
                        "move_type": move_type,
                        "hop_type": hop_type,
                        "jump_type": jump_type,
                        "atom": atom,
                        "atom_coords": {"x": x_atom, "y": y_atom},
                    }
                    if is_initial_only:
                        move["initial_only"] = True
                    moves.append(move)

        return moves

    def _get_directions(self, x: int, y: int) -> Set[Tuple[int, int]]:
        directions = set()
        for sx in [-1, 1]:
            for sy in [-1, 1]:
                directions.add((x * sx, y * sy))
                directions.add((y * sx, x * sy))
        return directions

    def _filter_directions(self, directions: Set[Tuple[int, int]], mods: str, atom: str) -> Set[Tuple[int, int]]:
        # 1. Handle union-style modifiers recursively.
        # These modifiers expand into a union of moves, so they are handled
        # by recursively calling this function for each component of the union.

        # `v` (vertical) and `s` (sideways) shorthands.
        if 'v' in mods:
            other_mods = mods.replace('v', '', 1)
            f_dirs = self._filter_directions(directions, 'f' + other_mods, atom)
            b_dirs = self._filter_directions(directions, 'b' + other_mods, atom)
            return f_dirs.union(b_dirs)

        if 's' in mods:
            other_mods = mods.replace('s', '', 1)
            l_dirs = self._filter_directions(directions, 'l' + other_mods, atom)
            r_dirs = self._filter_directions(directions, 'r' + other_mods, atom)
            return l_dirs.union(r_dirs)

        # Union of multiple doubled modifiers (e.g., ffrrN).
        doubled_mods = re.findall(r"ff|bb|ll|rr", mods)
        if len(doubled_mods) > 1:
            total_dirs = set()
            for d_mod in doubled_mods:
                total_dirs.update(self._filter_directions(directions, d_mod, atom))
            return total_dirs

        # 2. Base case: process a modifier string without union-style modifiers.
        x_atom, y_atom = self.atoms[atom]
        is_hippogonal = x_atom != y_atom and x_atom * y_atom != 0

        # For hippogonal pieces, single-letter direction modifiers are doubled.
        if is_hippogonal:
            dir_mods_only = "".join(c for c in mods if c in "fblr")
            if len(dir_mods_only) == 1:
                mods = mods.replace(dir_mods_only, dir_mods_only * 2)

        # The 'h' (half) modifier expands a direction to all moves with that component.
        # This is handled by disabling the doubled-modifier constraint logic.
        has_h = 'h' in mods
        if has_h:
            mods = mods.replace('h', '')

        # The original `fbN` special case is now handled by the `v` recursion.
        if mods == "fb" and atom == "N":
            # This case is hit for `vN` -> `fbN`.
            f_dirs = self._filter_directions(directions, "f", atom)
            b_dirs = self._filter_directions(directions, "b", atom)
            return f_dirs.union(b_dirs)

        # The `s` and `v` modifiers are handled by recursion now,
        # so these expansions are no longer needed here.
        # if "s" in mods:
        #     mods += "lr"
        # if "v" in mods:
        #     mods += "fb"

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

        constrain_double_vertical = ("ff" in mods or "bb" in mods) and not has_h
        constrain_double_horizontal = ("ll" in mods or "rr" in mods) and not has_h

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
