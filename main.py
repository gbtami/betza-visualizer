import math
import json
from textual import work
from rich.segment import Segment
from rich.style import Style
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label, Select
from textual.widget import Widget
from textual.containers import Container, GridLayout
from textual.reactive import reactive
from textual.strip import Strip
from textual.events import Click
from textual.message import Message

from betza_parser import BetzaParser
from textual_fspicker import FileOpen
from variant_ini_parser import VariantIniParser


class PieceListItem(ListItem):
    def __init__(self, piece_name: str, piece_variant: str, piece_betza: str) -> None:
        super().__init__()
        self.piece_name = piece_name
        self.piece_variant = piece_variant
        self.piece_betza = piece_betza

    def compose(self) -> ComposeResult:
        yield Label(self.piece_name, classes="name")
        yield Label(self.piece_variant, classes="variant")


def sign(n):
    return int(math.copysign(1, n)) if n != 0 else 0


DEFAULT_BOARD_SIZE = 15
LEGEND_TEXT = "m: Move | x: Capture | X: Move/Capture | i: Initial | ♙: Blocker | H: Capture on Blocker | #: Move/Capture on Blocker"

SPRITES = {
    ".": ["        ", "        ", "        ", "        "],
    "🧚": ["  .::.  ", " (o^^o) ", " /|  |\\ ", "  /\\/\\  "],
    "♙": ["        ", "  (..)  ", "  <||>  ", "  _||_  "],
    "m": ["   __   ", "  /  \\  ", "  \\__/  ", "   ->   "],
    "x": ["        ", "  \\/    ", "  /\\    ", "        "],
    "X": ["   __   ", "  /  \\  ", "  \\__/  ", "  <->   "],
    "i": ["        ", "  .--.  ", " |i  | ", "  '--'  "],
    "c": ["  \\/    ", "  /\\    ", " (cap)  ", "        "],
    "I": ["   __   ", "  /  \\  ", " | I |  ", "  '--'  "],
    "H": ["        ", "  \\/    ", "  /\\    ", " (H)    "],
    "#": ["   __   ", "  /##\\  ", "  \\##/  ", "  <->   "],
}

CHAR_TO_STYLE_MAP = {
    "🧚": "piece",
    "♙": "blocker",
    "m": "move",
    "x": "capture",
    "X": "move-capture",
    "i": "initial",
    "c": "initial",
    "I": "initial",
    "H": "capture",
    "#": "move-capture",
}


class Square(Widget):
    piece = reactive(".")

    class Clicked(Message):
        pass

    def render_line(self, y: int) -> Strip:
        sprite = SPRITES.get(self.piece, SPRITES["."])
        sprite_line = sprite[y % 4]

        is_odd_col = ord(self.id[0]) % 2
        is_odd_row = int(self.id[1:]) % 2
        bg_style_name = "black-square" if (is_odd_row + is_odd_col) % 2 else "white-square"
        bg_style = self.get_component_rich_style(f"board--{bg_style_name}")

        fg_style_name = CHAR_TO_STYLE_MAP.get(self.piece)
        fg_style = self.get_component_rich_style(f"board--{fg_style_name}") if fg_style_name else Style()

        return Strip([Segment(sprite_line, bg_style + fg_style)])

    def on_click(self, event: Click) -> None:
        self.post_message(self.Clicked())


class BoardWidget(Container):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.board_size = DEFAULT_BOARD_SIZE

    def on_mount(self) -> None:
        self.styles.layout = "grid"

    def setup_board(self):
        self.remove_children()
        self.styles.grid_size_columns = self.board_size
        self.styles.grid_size_rows = self.board_size
        for y in range(self.board_size):
            for x in range(self.board_size):
                square_id = f"{chr(ord('a') + x)}{self.board_size - y}"
                square = Square(id=square_id)
                self.mount(square)

    def get_board_layout(self) -> list[list[str]]:
        squares = self.query(Square)
        board = [["" for _ in range(self.board_size)] for _ in range(self.board_size)]
        for square in squares:
            x_char = square.id[0]
            y_char = square.id[1:]
            x = ord(x_char) - ord('a')
            try:
                y_val = int(y_char)
            except ValueError:
                continue
            y = self.board_size - y_val
            if 0 <= y < self.board_size and 0 <= x < self.board_size:
                board[y][x] = square.piece
        return board

    def update_board(self, board_layout: list[list[str]]):
        for y, row in enumerate(board_layout):
            for x, piece in enumerate(row):
                square_id = f"{chr(ord('a') + x)}{self.board_size - y}"
                try:
                    square = self.query_one(f"#{square_id}", Square)
                    square.piece = piece
                except Exception:
                    pass


class BetzaChessApp(App):
    CSS_PATH = "style.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+l", "load_variants", "Load Variants"),
    ]

    board_size = reactive(DEFAULT_BOARD_SIZE)
    moves = reactive([])
    blockers = reactive(set())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container(id="main-container"):
            yield Input(placeholder="Try Xiangqi Horse: nN", id="betza_input")
            yield Select(
                [
                    ("5x5", 5), ("7x7", 7), ("9x9", 9),
                    ("11x11", 11), ("13x13", 13), ("15x15", 15),
                ],
                value=DEFAULT_BOARD_SIZE, id="board_size_select",
            )
            yield ListView(id="piece_catalog_list")
            yield BoardWidget(id="board")
            yield Select([], id="variant_select")
            yield Static(LEGEND_TEXT, id="legend")

    def on_mount(self) -> None:
        self.parser = BetzaParser()
        with open("fsf_built_in_variants_catalog.json", "r") as f:
            self.fsf_catalog = json.load(f)
        with open("fsf_built_in_variant_properties.json", "r") as f:
            self.fsf_variant_properties = json.load(f)
        self.piece_catalog = self.fsf_catalog
        self.query_one(Input).focus()
        self.populate_variant_select()
        self.populate_piece_list()
        self.update_board()

    def get_board_layout(self) -> list[list[str]]:
        board_size = self.board_size
        moves = self.moves
        center = board_size // 2
        board = [["." for _ in range(board_size)] for _ in range(board_size)]
        board[center][center] = "🧚"

        for bx, by in self.blockers:
            if 0 <= center - by < board_size and 0 <= center + bx < board_size:
                board[center - by][center + bx] = "♙"

        move_map = {"move_capture": "X", "move": "m", "capture": "x"}

        for move in moves:
            x = move["x"]
            y = move["y"]
            move_type = move["move_type"]
            hop_type = move["hop_type"]
            jump_type = move["jump_type"]
            atom_coords = move["atom_coords"]

            display_y, display_x = center - y, center + x
            if not (0 <= display_y < board_size and 0 <= display_x < board_size):
                continue

            is_valid = None
            if hop_type is not None:
                is_valid = False
                is_linear_move = x == 0 or y == 0 or abs(x) == abs(y)

                if is_linear_move:
                    common_divisor = math.gcd(abs(x), abs(y))
                    dx = x // common_divisor if common_divisor != 0 else 0
                    dy = y // common_divisor if common_divisor != 0 else 0
                else:
                    atom_x, atom_y = atom_coords["x"], atom_coords["y"]
                    possible_steps = [
                        (atom_x, atom_y), (-atom_x, atom_y), (atom_x, -atom_y), (-atom_x, -atom_y),
                        (atom_y, atom_x), (-atom_y, atom_x), (atom_y, -atom_x), (-atom_y, -atom_x),
                    ]
                    step = next((s for s in possible_steps if s[0] != 0 and s[1] != 0 and x % s[0] == 0 and y % s[1] == 0 and x // s[0] == y // s[1]), None)
                    if step:
                        dx, dy = step
                    else:
                        dx, dy = 0, 0

                if dx == 0 and dy == 0: path_len = 0
                elif dx != 0: path_len = abs(x // dx)
                else: path_len = abs(y // dy)

                path = [(i * dx, i * dy) for i in range(1, path_len)]
                blockers_on_path = [p for p in path if p in self.blockers]

                if hop_type == "p":
                    if len(blockers_on_path) == 1:
                        blocker_pos = blockers_on_path[0]
                        if abs(x) > abs(blocker_pos[0]) or abs(y) > abs(blocker_pos[1]):
                            is_valid = True
                elif hop_type == "g":
                    if len(blockers_on_path) == 1:
                        blocker_pos = blockers_on_path[0]
                        if x == blocker_pos[0] + dx and y == blocker_pos[1] + dy:
                            is_valid = True
            elif jump_type == "jumping":
                is_valid = True
            elif jump_type == "non-jumping":
                is_linear_move = (x == 0) or (y == 0) or (abs(x) == abs(y))
                if is_linear_move:
                    is_valid = True
                    dx, dy = sign(x), sign(y)
                    path = [(i * dx, i * dy) for i in range(1, max(abs(x), abs(y)))]
                    if any(p in self.blockers for p in path):
                        is_valid = False
                else:
                    is_valid = True
                    block_x, block_y = 0, 0
                    if abs(x) > abs(y): block_x = sign(x)
                    elif abs(y) > abs(x): block_y = sign(y)
                    if (block_x, block_y) in self.blockers:
                        is_valid = False
            else:
                is_valid = True
                dx, dy = sign(x), sign(y)
                path = [(i * dx, i * dy) for i in range(1, max(abs(x), abs(y)))]
                if any(p in self.blockers for p in path):
                    is_valid = False

            if is_valid and (x, y) in self.blockers and move_type == "move":
                is_valid = False

            if is_valid:
                is_on_blocker = (x, y) in self.blockers
                is_initial = move.get("initial_only", False)
                char = move_map.get(move_type, "?")
                if is_initial:
                    if char == "m": char = "i"
                    elif char == "x": char = "c"
                    elif char == "X": char = "I"
                if is_on_blocker:
                    if char == "m": char = "M"
                    elif char == "x": char = "H"
                    elif char == "X": char = "#"
                board[display_y][display_x] = char
        return board

    def update_board(self):
        board_widget = self.query_one(BoardWidget)
        board_layout = self.get_board_layout()
        board_widget.update_board(board_layout)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, PieceListItem):
            self.query_one("#betza_input").value = event.item.piece_betza
            self.blockers = set()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.moves = self.parser.parse(event.value, board_size=self.board_size)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "board_size_select":
            self.board_size = event.value
        elif event.select.id == "variant_select":
            self.query_one("#betza_input").value = ""
            self.blockers = set()
            self.populate_piece_list(str(event.value))

    def on_square_clicked(self, message: Square.Clicked) -> None:
        square_id = message.sender.id
        x_char = square_id[0]
        y_char = square_id[1:]

        x = ord(x_char) - ord('a')
        y = self.board_size - int(y_char)

        center = self.board_size // 2
        blocker_x = x - center
        blocker_y = center - y

        if (blocker_x, blocker_y) == (0,0):
            return

        blocker_coord = (blocker_x, blocker_y)
        new_blockers = self.blockers.copy()
        if blocker_coord in new_blockers:
            new_blockers.remove(blocker_coord)
        else:
            new_blockers.add(blocker_coord)
        self.blockers = new_blockers

    def watch_board_size(self, new_size: int) -> None:
        board = self.query_one(BoardWidget)
        board.board_size = new_size
        board.setup_board()
        self.blockers = set()
        self.update_board()

    def watch_moves(self, new_moves: list) -> None:
        self.update_board()

    def watch_blockers(self, new_blockers: set) -> None:
        self.update_board()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    @work
    async def action_load_variants(self) -> None:
        """Load a variants.ini file."""
        path = await self.push_screen_wait(FileOpen())
        if path:
            try:
                with open(path, "r") as f:
                    ini_content = f.read()
                ini_parser = VariantIniParser(ini_content, self.fsf_catalog, self.fsf_variant_properties)
                ini_pieces = ini_parser.parse()
                self.piece_catalog = self.fsf_catalog + ini_pieces
                self.populate_variant_select()
                self.populate_piece_list()
            except Exception as e:
                self.log(f"Error loading variants file: {e}")

    def populate_variant_select(self) -> None:
        variants = set(p["variant"] for p in self.piece_catalog)
        variant_select = self.query_one("#variant_select", Select)
        variant_select.set_options([("All", "All")] + [(v, v) for v in sorted(list(variants))])

    def populate_piece_list(self, filter_variant: str = "All") -> None:
        list_view = self.query_one(ListView)
        list_view.clear()
        piece_catalog = self.piece_catalog
        if filter_variant != "All":
            piece_catalog = [p for p in self.piece_catalog if p["variant"] == filter_variant]
        for piece in piece_catalog:
            list_view.append(PieceListItem(piece_name=piece["name"], piece_variant=piece["variant"], piece_betza=piece["betza"]))

if __name__ == "__main__":
    app = BetzaChessApp()
    app.run()
