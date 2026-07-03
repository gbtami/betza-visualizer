import configparser
from typing import List, Dict, Any, Tuple

class VariantIniParser:
    PREDEFINED_PIECES = {
        'p': ("Pawn", "fmWfceF"), 'n': ("Knight", "N"), 'b': ("Bishop", "B"), 'r': ("Rook", "R"),
        'q': ("Queen", "Q"), 'f': ("Fers", "F"), 'a': ("Alfil", "A"), 'h': ("Horse", "nN"),
        'e': ("Elephant", "nA"), 'w': ("Wazir", "W"), 'd': ("Dragon", "RF"), 'c': ("Cannon", "mRcpR"),
        'k': ("King", "K"), 'g': ("Gold", "WfF"), 's': ("Silver", "FfW"), 'l': ("Lance", "fR"),
        'z': ("Janggi Elephant", "nZ"), 'u': ("Janggi Cannon", "pR"), 't': ("Soldier", "fsW"),
        'v': ("Archbishop", "BN"), 'm': ("Chancellor", "RN")
    }

    def __init__(self, ini_content: str, piece_catalog: List[Dict[str, Any]], variant_properties: Dict[str, Any]):
        self.config = configparser.ConfigParser(interpolation=None, allow_no_value=True)
        self.config.optionxform = str
        cleaned_content = self._clean_ini_content(ini_content)
        self.config.read_string(cleaned_content)

        self.piece_catalog = piece_catalog
        self.variant_properties = variant_properties
        self.catalog_by_variant = {}
        for piece in self.piece_catalog:
            variant = piece['variant']
            if variant not in self.catalog_by_variant:
                self.catalog_by_variant[variant] = []
            self.catalog_by_variant[variant].append(piece)

        self.parsed_variants_cache = {}

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

    def parse_variant(self, section_name: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if section_name in self.parsed_variants_cache:
            return self.parsed_variants_cache[section_name]

        variant_name, _, parent_name = section_name.strip('[]').partition(':')

        parent_pieces = []
        parent_props = {'double_step': False}

        if parent_name:
            parent_section_found = False
            for s in self.config.sections():
                if s.strip('[]').split(':', 1)[0] == parent_name:
                    parent_pieces, parent_props = self.parse_variant(s)
                    parent_section_found = True
                    break
            if not parent_section_found:
                parent_pieces = self.catalog_by_variant.get(parent_name, [])
                parent_props = self.variant_properties.get(parent_name, {'double_step': False})
        else:
            parent_pieces = self.catalog_by_variant.get(variant_name, [])
            parent_props = self.variant_properties.get(variant_name, {'double_step': False})

        pieces = [p.copy() for p in parent_pieces]
        for p in pieces:
            p['variant'] = variant_name

        props = parent_props.copy()

        if section_name in self.config:
            settings = self.config[section_name]

            if 'doubleStep' in settings:
                props['double_step'] = settings['doubleStep'].lower() == 'true'

            removals = {k.lower().replace(' ', '') for k, v in settings.items() if v and v.strip() == '-'}
            pieces = [p for p in pieces if p['name'].lower().replace(' ', '') not in removals]

            for key, value in settings.items():
                if not value or value.strip() == '-' or key.lower() in ["promotedpiecetype", "doublestep"]:
                    continue

                if ':' in value:
                    piece_char, betza = value.split(':', 1)
                    piece_name_key = key.lower().replace(' ', '')
                    is_custom = key.startswith('customPiece')
                    piece_name = f"{variant_name.title()}-{piece_char}" if is_custom else key.title()

                    found = any(p['name'].lower().replace(' ', '') == piece_name_key and 'betza' in p for p in pieces)
                    if found:
                        for piece in pieces:
                            if piece['name'].lower().replace(' ', '') == piece_name_key:
                                piece['betza'] = betza
                    else:
                        pieces.append({"name": piece_name, "variant": variant_name, "betza": betza})
                else:
                    piece_char = value.strip()
                    if piece_char in self.PREDEFINED_PIECES:
                        official_name, betza = self.PREDEFINED_PIECES[piece_char]
                        found = any(p['name'].lower().replace(' ', '') == official_name.lower() for p in pieces)
                        if found:
                            for piece in pieces:
                                if piece['name'].lower().replace(' ', '') == official_name.lower():
                                    piece['betza'] = betza
                        else:
                            pieces.append({"name": official_name, "variant": variant_name, "betza": betza})

        if props.get('double_step'):
            for piece in pieces:
                if piece['name'].lower() == 'pawn' and 'ifmnD' not in piece['betza']:
                    piece['betza'] += 'ifmnD'

        self.parsed_variants_cache[section_name] = (pieces, props)
        return pieces, props

    def parse(self) -> List[Dict[str, Any]]:
        all_pieces = []
        for section_name in self.config.sections():
            pieces, _ = self.parse_variant(section_name)
            all_pieces.extend(pieces)

        unique_pieces = []
        seen = set()
        for piece in reversed(all_pieces):
            identifier = (piece['name'], piece['variant'])
            if identifier not in seen:
                unique_pieces.append(piece)
                seen.add(identifier)

        return sorted(unique_pieces, key=lambda p: (p['variant'], p['name']))
