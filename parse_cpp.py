import re
import json
import sys
import requests

def camel_to_title(name):
    """Converts a camelCase string to Title Case."""
    s = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    return s.title()

class CppParser:
    def __init__(self):
        self.piece_defs = {}
        self.raw_variant_defs = {}
        self.variant_map = {}
        self.char_to_name_map = {
            'p': 'pawn', 'n': 'knight', 'b': 'bishop', 'r': 'rook', 'q': 'queen', 'k': 'king',
            'a': 'archbishop', 'c': 'chancellor', 'f': 'fers', 's': 'silver', 'g': 'gold', 'l': 'lance',
            'e': 'elephant', 'h': 'horse', 'w': 'wazir', 'd': 'dragon', 'm': 'commoner'
        }

    def parse_piece_definitions(self, piece_cpp_content):
        pattern = re.compile(r'add\((?P<enum>\w+),\s*from_betza\("(?P<betza>[^"]*)",\s*"(?P<name>\w+)"\)\);')
        for match in pattern.finditer(piece_cpp_content):
            enum = match.group('enum')
            betza = match.group('betza')
            name = match.group('name')
            self.piece_defs[enum] = {'name': name, 'betza': betza}

        if 'add(JANGGI_ELEPHANT, janggi_elephant_piece());' in piece_cpp_content:
            self.piece_defs['JANGGI_ELEPHANT'] = {'name': 'janggiElephant', 'betza': 'nZ'}

        # Manually add aliases with their correct names, but copying the betza string.
        fers_betza = self.piece_defs.get('FERS', {}).get('betza')
        if fers_betza:
            self.piece_defs['MET'] = {'name': 'met', 'betza': fers_betza}

        silver_betza = self.piece_defs.get('SILVER', {}).get('betza')
        if silver_betza:
            self.piece_defs['KHON'] = {'name': 'khon', 'betza': silver_betza}

        bers_betza = self.piece_defs.get('BERS', {}).get('betza')
        if bers_betza:
            self.piece_defs['DRAGON'] = {'name': 'dragon', 'betza': bers_betza}

    def parse_variant_definitions(self, variant_cpp_content):
        pattern = re.compile(r'Variant\*\s+(\w+_variant\w*)\s*\(\)\s*\{([\s\S]*?)\}', re.DOTALL)
        for match in pattern.finditer(variant_cpp_content):
            func_name = match.group(1)
            body = match.group(2)
            parent_match = re.search(r'(\w+)\(\)->init\(\);', body)
            parent = parent_match.group(1) if parent_match else None
            if not parent and 'chess_variant_base' in func_name:
                parent = 'variant_base'
            elif not parent and 'variant_base' in func_name:
                 parent = None

            reset_pieces = 'v->reset_pieces();' in body
            removals = re.findall(r'v->remove_piece\((\w+)\);', body)
            king_type_match = re.search(r'v->kingType\s*=\s*(\w+);', body)
            king_type = king_type_match.group(1) if king_type_match else None
            double_step_match = re.search(r'v->doubleStep\s*=\s*(true|false);', body)
            double_step = double_step_match.group(1) == 'true' if double_step_match else None
            additions = []
            add_pattern = re.compile(r'v->add_piece\((\w+),\s*\'(\w)\'(?:,\s*[\'"]([^"\']*)[\'"])?\);')
            for add_match in add_pattern.finditer(body):
                additions.append({ 'enum': add_match.group(1), 'char': add_match.group(2), 'betza': add_match.group(3) if add_match.group(3) and add_match.group(1).startswith("CUSTOM_PIECE_") else None })
            self.raw_variant_defs[func_name] = { 'parent': parent, 'removals': removals, 'additions': additions, 'reset_pieces': reset_pieces, 'king_type': king_type, 'double_step': double_step }

        map_init_body_match = re.search(r'void\s+VariantMap::init\(\)\s*\{([\s\S]*?)\}', variant_cpp_content, re.DOTALL)
        if map_init_body_match:
            map_init_body = map_init_body_match.group(1)
            map_pattern = re.compile(r'add\("([^"]+)",\s*(\w+_variant\w*)\(\)\);')
            for map_match in map_pattern.finditer(map_init_body):
                self.variant_map[map_match.group(1)] = map_match.group(2)

        self.raw_variant_defs['variant_base'] = {'parent': None, 'removals': [], 'additions': []}

        all_parents = {info['parent'] for info in self.raw_variant_defs.values() if info['parent']}
        mapped_funcs = set(self.variant_map.values())

        for parent_func in all_parents:
            if parent_func not in mapped_funcs and parent_func in self.raw_variant_defs:
                variant_name = parent_func.replace('_variant', '')
                self.variant_map[variant_name] = parent_func

    def topological_sort(self):
        in_degree = {u: 0 for u in self.raw_variant_defs}
        adj = {u: [] for u in self.raw_variant_defs}
        for u, info in self.raw_variant_defs.items():
            parent = info.get('parent')
            if parent and parent in self.raw_variant_defs:
                in_degree[u] += 1
                adj[parent].append(u)

        queue = [u for u in self.raw_variant_defs if in_degree[u] == 0]
        sorted_order = []

        while queue:
            u = queue.pop(0)
            sorted_order.append(u)
            for v in adj.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(sorted_order) != len(self.raw_variant_defs):
            remaining = sorted(list(set(self.raw_variant_defs.keys()) - set(sorted_order)))
            sorted_order.extend(remaining)

        return sorted_order

    def run(self, piece_cpp_content, variant_cpp_content):
        self.parse_piece_definitions(piece_cpp_content)
        self.parse_variant_definitions(variant_cpp_content)

        sorted_variants = self.topological_sort()

        final_pieces_by_func = {}
        variant_properties = {}

        for func_name in sorted_variants:
            if func_name not in self.raw_variant_defs: continue

            variant_info = self.raw_variant_defs[func_name]
            parent_func = variant_info.get('parent')
            resets_pieces = variant_info.get('reset_pieces', False)

            pieces = {}
            if parent_func and parent_func in final_pieces_by_func and not resets_pieces:
                pieces = final_pieces_by_func[parent_func].copy()

            if func_name == 'chess_variant_base':
                standard_pieces = ["PAWN", "KNIGHT", "BISHOP", "ROOK", "QUEEN", "KING"]
                for piece_enum in standard_pieces:
                    if piece_enum in self.piece_defs:
                        pieces[piece_enum] = self.piece_defs[piece_enum]

            for removal_enum in variant_info['removals']:
                if removal_enum in pieces:
                    del pieces[removal_enum]

            for addition in variant_info['additions']:
                enum = addition['enum']
                betza = addition['betza']
                char = addition['char']

                if not betza:
                    betza = self.piece_defs.get(enum, {}).get('betza')

                if betza is not None:
                    name = self.piece_defs.get(enum, {}).get('name')
                    if not name and enum.startswith('CUSTOM_PIECE_'):
                        variant_name_base = func_name.replace('_variant', '')
                        name = f'{variant_name_base}-{char}'

                    if name:
                        pieces[enum] = {'name': name, 'betza': betza}

            final_pieces_by_func[func_name] = pieces

        output = []
        for variant_name, func_name in self.variant_map.items():
            if variant_name.endswith('_base'):
                continue
            if func_name in final_pieces_by_func:
                # Determine if the variant is descended from chess_variant_base
                is_chess_descendant = False
                curr = func_name
                while curr:
                    if curr == 'chess_variant_base':
                        is_chess_descendant = True
                        break
                    curr = self.raw_variant_defs.get(curr, {}).get('parent')

                double_step = is_chess_descendant

                # Find the effective double_step value by traversing the inheritance chain
                curr = func_name
                while curr:
                    current_variant_info = self.raw_variant_defs.get(curr, {})
                    if current_variant_info.get('double_step') is not None:
                        double_step = current_variant_info['double_step']
                        break
                    curr = current_variant_info.get('parent')

                variant_properties[variant_name] = {'double_step': double_step}

                # Find the effective king_type by traversing the inheritance chain
                current_func = func_name
                king_type_enum = None
                while current_func:
                    current_variant_info = self.raw_variant_defs.get(current_func, {})
                    if current_variant_info.get('king_type'):
                        king_type_enum = current_variant_info['king_type']
                        break
                    current_func = current_variant_info.get('parent')

                king_betza = None
                if king_type_enum and king_type_enum in self.piece_defs:
                    king_betza = self.piece_defs[king_type_enum]['betza']

                for enum, piece_info in final_pieces_by_func[func_name].items():
                    internal_name = piece_info['name']
                    betza = piece_info['betza']

                    if enum == 'KING' and king_betza is not None:
                        betza = king_betza

                    if enum == 'PAWN' and double_step:
                        betza += 'ifmnD'

                    if '_' in internal_name:
                        display_name = internal_name.replace('_', ' ').title()
                    elif '-' in internal_name:
                        parts = internal_name.split('-', 1)
                        display_name = parts[0].title() + '-' + parts[1]
                    else:
                        display_name = camel_to_title(internal_name)

                    output.append({
                        'name': display_name,
                        'variant': variant_name,
                        'betza': betza
                    })

        output.sort(key=lambda x: (x['variant'], x['name']))
        return json.dumps(output, indent=2), json.dumps(variant_properties, indent=2)

if __name__ == '__main__':
    PIECE_CPP_URL = 'https://raw.githubusercontent.com/fairy-stockfish/Fairy-Stockfish/master/src/piece.cpp'
    VARIANT_CPP_URL = 'https://raw.githubusercontent.com/fairy-stockfish/Fairy-Stockfish/master/src/variant.cpp'

    try:
        print("Downloading piece.cpp...")
        response = requests.get(PIECE_CPP_URL)
        response.raise_for_status()
        piece_cpp = response.text

        print("Downloading variant.cpp...")
        response = requests.get(VARIANT_CPP_URL)
        response.raise_for_status()
        variant_cpp = response.text

        parser = CppParser()
        json_output, properties_output = parser.run(piece_cpp, variant_cpp)

        with open('fsf_built_in_variants_catalog.json', 'w', encoding='utf-8') as f:
            f.write(json_output)

        print("Successfully generated fsf_built_in_variants_catalog.json")

        with open('fsf_built_in_variant_properties.json', 'w', encoding='utf-8') as f:
            f.write(properties_output)

        print("Successfully generated fsf_built_in_variant_properties.json")

    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"Error downloading file: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An error occurred: {e}\n")
        sys.exit(1)
