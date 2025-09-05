import configparser
from typing import List, Dict, Any

class VariantIniParser:
    """
    Parses a variants.ini file to extract piece definitions.
    """

    PREDEFINED_PIECES = {
        'pawn': 'fmWfceF',
        'knight': 'N',
        'bishop': 'B',
        'rook': 'R',
        'queen': 'Q',
        'fers': 'F',
        'alfil': 'A',
        'fersAlfil': 'FA',
        'silver': 'FfW',
        'aiwok': 'RNF',
        'bers': 'RF',
        'archbishop': 'BN',
        'chancellor': 'RN',
        'amazon': 'QN',
        'knibis': 'mNcB',
        'biskni': 'mBcN',
        'kniroo': 'mNcR',
        'rookni': 'mRcN',
        'shogiPawn': 'fW',
        'lance': 'fR',
        'shogiKnight': 'fN',
        'gold': 'WfF',
        'dragonHorse': 'BW',
        'clobber': 'cW',
        'breakthrough': 'fmWfF',
        'immobile': '',
        'cannon': 'mRcpR',
        'janggiCannon': 'pR',
        'soldier': 'fsW',
        'horse': 'nN',
        'elephant': 'nA',
        'janggiElephant': 'nZ',
        'banner': 'RcpRnN',
        'wazir': 'W',
        'commoner': 'K',
        'centaur': 'KN',
        'king': 'K',
    }

    PIECE_KEYS = [
        'pawn', 'knight', 'bishop', 'rook', 'queen', 'king',
        'fers', 'alfil', 'fersAlfil', 'silver', 'aiwok', 'bers',
        'archbishop', 'chancellor', 'amazon', 'knibis', 'biskni',
        'kniroo', 'rookni', 'shogiPawn', 'lance', 'shogiKnight',
        'gold', 'dragonHorse', 'clobber', 'breakthrough', 'immobile',
        'cannon', 'janggiCannon', 'soldier', 'horse', 'elephant',
        'janggiElephant', 'banner', 'wazir', 'commoner', 'centaur'
    ] + [f'customPiece{i}' for i in range(1, 26)]

    def __init__(self, ini_content: str):
        self.config = configparser.ConfigParser(interpolation=None, allow_no_value=True)
        # configparser by default converts keys to lowercase. We need to preserve case.
        self.config.optionxform = str
        self.config.read_string(ini_content)

    def _get_all_variant_settings(self, variant_section_name: str) -> Dict[str, str]:
        """
        Recursively gets all settings for a variant, including from its parents.
        """
        if ':' in variant_section_name:
            child, parent = variant_section_name.split(':', 1)
            # Find the full section name for the parent, which might also have a parent
            parent_full_section = ""
            for sec in self.config.sections():
                if sec.startswith(parent) and (len(sec) == len(parent) or sec[len(parent)] == ':'):
                     parent_full_section = sec
                     break

            if not parent_full_section:
                 # This case handles if a parent is not found, e.g. [variant:chess] and chess is builtin
                 # A more robust solution would be to have the builtin variants also in the config
                 settings = {}
            else:
                settings = self._get_all_variant_settings(parent_full_section)

            settings.update(self.config[variant_section_name])
            return settings
        else:
            if variant_section_name in self.config:
                return dict(self.config[variant_section_name])
            else:
                return {}

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parses the loaded .ini content and returns a list of piece definitions.
        """
        all_pieces = []

        processed_variants = set()

        for section_name in self.config.sections():
            variant_name = section_name.split(':', 1)[0]

            if variant_name in processed_variants:
                continue

            settings = self._get_all_variant_settings(section_name)

            variant_pieces = {}

            for key, value in settings.items():
                if key in self.PIECE_KEYS:
                    piece_name_key = key

                    piece_name = piece_name_key.capitalize()
                    if piece_name_key.startswith('customPiece'):
                        piece_name = f"Custom Piece {piece_name_key.replace('customPiece', '')}"

                    betza = ""
                    if value is None:
                        continue

                    if ':' in value:
                        _, betza = value.split(':', 1)
                    else:
                        if piece_name_key in self.PREDEFINED_PIECES:
                            betza = self.PREDEFINED_PIECES[piece_name_key]

                    # Handle piece removal, e.g. king = -
                    if value.strip() == '-':
                        if piece_name in variant_pieces:
                            del variant_pieces[piece_name]
                        continue

                    if betza:
                        variant_pieces[piece_name] = {
                            "name": piece_name,
                            "variant": variant_name,
                            "betza": betza
                        }

            all_pieces.extend(list(variant_pieces.values()))
            processed_variants.add(variant_name)


        # Remove duplicates. The last one wins.
        # A variant might be defined multiple times (e.g. once as a parent, once standalone)
        # We process by section, so we get all pieces for a variant at once.
        # The logic above already handles overriding within a variant's inheritance chain.
        # Now we just need to handle full duplicates across all variants.
        unique_pieces = []
        seen = set()
        for piece in reversed(all_pieces): # Last one wins
            identifier = (piece['name'], piece['variant'])
            if identifier not in seen:
                unique_pieces.append(piece)
                seen.add(identifier)

        return unique_pieces[::-1] # return in original order
