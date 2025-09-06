import configparser
from typing import List, Dict, Any

class VariantIniParser:
    PREDEFINED_PIECES = {
        'p': ("Pawn", "fmWfceF"), 'n': ("Knight", "N"), 'b': ("Bishop", "B"), 'r': ("Rook", "R"),
        'q': ("Queen", "Q"), 'f': ("Fers", "F"), 'a': ("Alfil", "A"), 'h': ("Horse", "nN"),
        'e': ("Elephant", "nA"), 'w': ("Wazir", "W"), 'd': ("Dragon", "RF"), 'c': ("Cannon", "mRcpR"),
        'k': ("King", "K"), 'g': ("Gold", "WfF"), 's': ("Silver", "FfW"), 'l': ("Lance", "fR"),
        'z': ("Janggi Elephant", "nZ"), 'u': ("Janggi Cannon", "pR"), 't': ("Soldier", "fsW"),
        'v': ("Archbishop", "BN"), 'm': ("Chancellor", "RN")
    }

    def __init__(self, ini_content: str, piece_catalog: List[Dict[str, Any]]):
        self.config = configparser.ConfigParser(interpolation=None, allow_no_value=True)
        self.config.optionxform = str
        cleaned_content = self._clean_ini_content(ini_content)
        self.config.read_string(cleaned_content)

        self.piece_catalog = piece_catalog
        self.catalog_by_variant = {}
        for piece in self.piece_catalog:
            variant = piece['variant']
            if variant not in self.catalog_by_variant:
                self.catalog_by_variant[variant] = []
            self.catalog_by_variant[variant].append(piece)

    def _clean_ini_content(self, ini_content: str) -> str:
        lines = ini_content.split('\n')
        first_section_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('[') and line.strip().endswith(']'):
                first_section_index = i
                break

        if first_section_index == -1:
            return ""

        return '\n'.join(lines[first_section_index:])

    def _get_inherited_pieces(self, parent_variant_name: str) -> List[Dict[str, Any]]:
        # Check if the parent is in the current INI file
        for section in self.config.sections():
            if section.split(':', 1)[0] == parent_variant_name:
                # If it is, we need to parse it recursively
                return self.parse_variant(section)

        # If not, it must be a built-in variant from the catalog
        return self.catalog_by_variant.get(parent_variant_name, [])

    def parse_variant(self, section_name: str) -> List[Dict[str, Any]]:
        variant_name, _, parent_name = section_name.replace(']', '').replace('[', '').partition(':')

        if parent_name:
            pieces = self._get_inherited_pieces(parent_name)
        else:
            pieces = self.catalog_by_variant.get(variant_name, [])

        # Make a copy to avoid modifying the catalog
        pieces = [p.copy() for p in pieces]
        for p in pieces:
            p['variant'] = variant_name

        if section_name in self.config:
            settings = self.config[section_name]

            # Handle removals
            removals = {k.lower().replace(' ', '') for k, v in settings.items() if v and v.strip() == '-'}
            pieces = [p for p in pieces if p['name'].lower().replace(' ', '') not in removals]

            # Handle additions/modifications
            for key, value in settings.items():
                if not value or value.strip() == '-':
                    continue

                if ':' in value:
                    piece_char, betza = value.split(':', 1)
                    piece_name_key = key.lower().replace(' ', '')

                    is_custom = key.startswith('customPiece')
                    if is_custom:
                        piece_name = f"Custom Piece {key.replace('customPiece', '')}"
                    else:
                        piece_name = key

                    found = False
                    for piece in pieces:
                        if piece['name'].lower().replace(' ', '') == piece_name_key:
                            piece['betza'] = betza
                            found = True
                            break

                    if not found:
                        pieces.append({
                            "name": piece_name,
                            "variant": variant_name,
                            "betza": betza
                        })
                else:
                    # Predefined piece
                    piece_char = value.strip()
                    if piece_char in self.PREDEFINED_PIECES:
                        official_name, betza = self.PREDEFINED_PIECES[piece_char]
                        piece_name = official_name

                        found = False
                        for piece in pieces:
                            if piece['name'].lower().replace(' ', '') == piece_name.lower().replace(' ', ''):
                                piece['betza'] = betza
                                found = True
                                break

                        if not found:
                            pieces.append({
                                "name": piece_name,
                                "variant": variant_name,
                                "betza": betza
                            })

        return pieces

    def parse(self) -> List[Dict[str, Any]]:
        all_pieces = []
        for section_name in self.config.sections():
            pieces = self.parse_variant(section_name)
            all_pieces.extend(pieces)

        unique_pieces = []
        seen = set()
        for piece in reversed(all_pieces):
            identifier = (piece['name'], piece['variant'])
            if identifier not in seen:
                unique_pieces.append(piece)
                seen.add(identifier)

        return unique_pieces[::-1]
