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

    def parse(self, notation: str) -> List[Tuple[int, int, str, Optional[str], str, str]]:
        """
        Parses notation. Returns a list of 6-element tuples:
        (x, y, move_type, hop_type, jump_type, base_atom)
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

            if letter in self.compound_aliases:
                expansion = self.compound_aliases[letter]
                if suffix:
                    expansion = re.sub(r"([A-Z])\d*", rf"\g<1>{suffix}", expansion)
                new_tokens = re.findall(r"[A-Z]\d*", expansion)
                token_worklist[0:0] = new_tokens
                continue

            if letter not in self.atoms:
                continue

            atom, count_str = letter, suffix

            # Determine move_type
            move_type = "move_capture"
            if "m" in current_mods and "c" not in current_mods:
                move_type = "move"
            elif "c" in current_mods and "m" not in current_mods:
                move_type = "capture"
            elif "m" in current_mods and "c" in current_mods:
                move_type = "capture" if current_mods.rfind("c") > current_mods.rfind("m") else "move"

            # Determine hop_type for riders
            hop_type = "p" if "p" in current_mods else "g" if "g" in current_mods else None

            # --- NEW: Determine jump_type for leapers ---
            jump_type = "normal"
            if "n" in current_mods:
                jump_type = "non-jumping"
            elif "j" in current_mods:
                jump_type = "jumping"

            max_steps = 1 if count_str == "" else self.infinity_cap if count_str == "0" else int(count_str)
            x_atom, y_atom = self.atoms[atom]
            base_directions = self._get_directions(x_atom, y_atom)
            allowed_directions = self._filter_directions(base_directions, current_mods)

            for i in range(1, max_steps + 1):
                for dx, dy in allowed_directions:
                    moves.append((dx * i, dy * i, move_type, hop_type, jump_type, atom))

        return moves

    def _get_directions(self, x: int, y: int) -> Set[Tuple[int, int]]:
        directions = set()
        for sx in [-1, 1]:
            for sy in [-1, 1]:
                directions.add((x * sx, y * sy))
                directions.add((y * sx, x * sy))
        return directions

    def _filter_directions(self, directions: Set[Tuple[int, int]], mods: str) -> Set[Tuple[int, int]]:
        if "s" in mods:
            mods += "lr"
        if "v" in mods:
            mods += "fb"

        dir_mods = "".join(c for c in mods if c in "fblr")
        if not dir_mods:
            return directions

        constrain_forward = "f" in dir_mods and "b" not in dir_mods
        constrain_backward = "b" in dir_mods and "f" not in dir_mods
        constrain_left = "l" in dir_mods and "r" not in dir_mods
        constrain_right = "r" in dir_mods and "l" not in dir_mods

        constrain_double_vertical = "ff" in mods or "bb" in mods
        constrain_double_horizontal = "ll" in mods or "rr" in mods

        filtered = set()
        for x, y in directions:
            is_valid = True

            if constrain_forward and y <= 0:
                is_valid = False
            if constrain_backward and y >= 0:
                is_valid = False
            if constrain_left and x >= 0:
                is_valid = False
            if constrain_right and x <= 0:
                is_valid = False
            if constrain_double_vertical and abs(y) <= abs(x):
                is_valid = False
            if constrain_double_horizontal and abs(x) <= abs(y):
                is_valid = False

            if is_valid:
                filtered.add((x, y))

        return filtered
