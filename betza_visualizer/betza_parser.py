import re
from typing import Dict, List, Optional, Set, Tuple


class BetzaParser:
    """Parse Betza notation into possible moves and their properties."""

    def __init__(self):
        # (forward, sideways) vectors.  L/C and J/Z are accepted aliases for
        # the same Fairy-Stockfish leapers.
        self.atoms: Dict[str, Tuple[int, int]] = {
            "W": (1, 0),
            "F": (1, 1),
            "D": (2, 0),
            "N": (2, 1),
            "A": (2, 2),
            "H": (3, 0),
            "L": (3, 1),
            "C": (3, 1),
            "J": (3, 2),
            "Z": (3, 2),
            "G": (3, 3),
        }
        # Compound aliases which expand to more than one independently parsed
        # Betza atom.  R/B/Q/K are represented below as built-in definitions so
        # directional modifiers can use the same rules as the TypeScript parser.
        self.compound_aliases: Dict[str, str] = {
            "E": "RN",
            "M": "FC",
        }
        self.compound_atoms: Dict[str, Tuple[Tuple[Tuple[str, int, int], ...], bool]] = {
            "K": (
                (
                    ("W", 1, 0),
                    ("F", 1, 1),
                ),
                False,
            ),
            "R": ((("W", 1, 0),), True),
            "B": ((("F", 1, 1),), True),
            "Q": (
                (
                    ("W", 1, 0),
                    ("F", 1, 1),
                ),
                True,
            ),
        }
        self.infinity_cap = 12
        self.jumping_atoms = {"N", "C", "L", "Z", "J"}

    def parse(self, notation: str, board_size: Optional[int] = None) -> List[Dict]:
        """Parse notation and return a list of move dictionaries."""

        moves: List[Dict] = []
        token_worklist = re.findall(r"[a-z]+|[A-Z]\d*", notation)
        current_mods = ""

        while token_worklist:
            token = token_worklist.pop(0)

            if token.islower():
                current_mods = token
                continue

            match = re.match(r"([A-Z])(\d*)", token)
            if match is None:
                continue
            letter, suffix = match.groups()

            # Original Betza doubled-atom notation denotes an unlimited rider.
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
                    for expanded_token in new_tokens:
                        prefixed_tokens.append(current_mods)
                        prefixed_tokens.append(expanded_token)
                    new_tokens = prefixed_tokens

                token_worklist[0:0] = new_tokens
                current_mods = ""
                continue

            definition = self._atom_definition(letter)
            if definition is None:
                # Keep pending modifiers, matching the permissive TS parser.
                continue

            vectors, base_rider = definition
            mods_for_this_atom = current_mods
            current_mods = ""

            explicitly_repeated = suffix != ""
            is_rider = base_rider or explicitly_repeated
            if is_rider:
                if suffix and suffix != "0":
                    max_steps = max(1, int(suffix))
                else:
                    max_steps = board_size // 2 if board_size is not None else self.infinity_cap
            else:
                max_steps = 1

            move_type = self._move_type(mods_for_this_atom)
            hop_type = "p" if "p" in mods_for_this_atom else "g" if "g" in mods_for_this_atom else None
            directional_tokens = self._directional_tokens(mods_for_this_atom)
            is_initial_only = "i" in mods_for_this_atom

            for atom, forward, sideways in vectors:
                split_orthogonal_directions = len(vectors) == 1 and sideways == 0
                allowed_directions = self._directions_for_vector(
                    forward,
                    sideways,
                    directional_tokens,
                    split_orthogonal_directions,
                )

                if "n" in mods_for_this_atom:
                    jump_type = "non-jumping"
                elif atom in self.jumping_atoms:
                    jump_type = "jumping"
                elif is_rider:
                    jump_type = "non-jumping"
                else:
                    jump_type = "jumping"

                for step in range(1, max_steps + 1):
                    for dx, dy in allowed_directions:
                        move = {
                            "x": dx * step,
                            "y": dy * step,
                            "move_type": move_type,
                            "hop_type": hop_type,
                            "jump_type": jump_type,
                            "atom": atom,
                            "atom_coords": {"x": forward, "y": sideways},
                        }
                        if is_initial_only:
                            move["initial_only"] = True
                        moves.append(move)

        return moves

    def _atom_definition(self, letter: str) -> Optional[Tuple[Tuple[Tuple[str, int, int], ...], bool]]:
        compound = self.compound_atoms.get(letter)
        if compound is not None:
            return compound

        coords = self.atoms.get(letter)
        if coords is None:
            return None
        forward, sideways = coords
        return (((letter, forward, sideways),), False)

    @staticmethod
    def _move_type(mods: str) -> str:
        quiet = "m" in mods
        capture = "c" in mods
        if quiet and not capture:
            return "move"
        if capture and not quiet:
            return "capture"
        return "move_capture"

    @staticmethod
    def _directional_tokens(mods: str) -> List[str]:
        """Split original Betza directional modifiers using FSF semantics."""

        vertical_modifiers = "fbvh"
        horizontal_modifiers = "rlsh"
        result: List[str] = []
        index = 0

        while index < len(mods):
            character = mods[index]
            vertical = character in vertical_modifiers
            horizontal = character in horizontal_modifiers
            if not vertical and not horizontal:
                index += 1
                continue

            next_character = mods[index + 1] if index + 1 < len(mods) else None
            next_vertical = next_character is not None and next_character in vertical_modifiers
            next_horizontal = next_character is not None and next_character in horizontal_modifiers
            can_combine = next_character is not None and (
                next_character == character or (vertical and next_horizontal) or (horizontal and next_vertical)
            )

            if can_combine:
                result.append(character + next_character)
                index += 2
            else:
                result.append(character * 2)
                index += 1

        return result

    @staticmethod
    def _directions_for_vector(
        forward: int,
        sideways: int,
        source_directions: List[str],
        split_orthogonal_directions: bool,
    ) -> Set[Tuple[int, int]]:
        if split_orthogonal_directions:
            directions = []
            for value in source_directions:
                if value[0] != value[1]:
                    directions.extend((value[0] * 2, value[1] * 2))
                else:
                    directions.append(value)
        else:
            directions = list(source_directions)

        direction_set = set(directions)
        unrestricted = not directions
        result: Set[Tuple[int, int]] = set()

        def has_any(*values: str) -> bool:
            return any(value in direction_set for value in values)

        if unrestricted or has_any("ff", "vv", "rf", "rv", "fh", "rh", "hr"):
            result.add((sideways, forward))
        if unrestricted or has_any("bb", "vv", "lb", "lv", "bh", "lh", "hr"):
            result.add((-sideways, -forward))
        if unrestricted or has_any("rr", "ss", "br", "bs", "bh", "rh", "hr"):
            result.add((forward, -sideways))
        if unrestricted or has_any("ll", "ss", "fl", "fs", "fh", "lh", "hr"):
            result.add((-forward, sideways))
        if unrestricted or has_any("rr", "ss", "fr", "fs", "fh", "rh", "hl"):
            result.add((forward, sideways))
        if unrestricted or has_any("ll", "ss", "bl", "bs", "bh", "lh", "hl"):
            result.add((-forward, -sideways))
        if unrestricted or has_any("bb", "vv", "rb", "rv", "bh", "rh", "hl"):
            result.add((sideways, -forward))
        if unrestricted or has_any("ff", "vv", "lf", "lv", "fh", "lh", "hl"):
            result.add((-sideways, forward))

        return result
