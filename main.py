import math
import json
from textual import work
from rich.segment import Segment
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label, Select
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
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


DEFAULT_BOARD_SIZE = 11
CELL_WIDTH = 8
CELL_HEIGHT = 4
SPRITE_WIDTH = 4
SPRITE_HEIGHT = 2
BOARD_FRAME_WIDTH = 0
BOARD_FRAME_HEIGHT = 0
HELP_LEGEND_ITEMS = [
    ("m", "Move marker"),
    ("x", "Capture marker"),
    ("X", "Move or capture marker"),
    ("i", "Initial-only marker"),
    ("♙", "Blocker"),
    ("M", "Move onto blocker"),
    ("H", "Capture on blocker"),
    ("#", "Move or capture on blocker"),
]

SPRITES = {
    ".": ["    ", "    "],
    "🧚": ["o^^o", "/||\\"],
    "♙": ["    ", "    "],
    "m": ["    ", "    "],
    "x": ["    ", "    "],
    "X": ["    ", "    "],
    "i": ["    ", "    "],
    "c": ["    ", "    "],
    "I": ["    ", "    "],
    "M": ["    ", "    "],
    "H": ["    ", "    "],
    "#": ["    ", "    "],
}

GLYPH_TO_STYLE_MAP = {
    "🧚": "piece",
}

SPRITE_FILL_MAP = {
    "♙": [["blocker"] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)],
    "m": [["move"] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)],
    "x": [["capture"] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)],
    "X": [["move", "move", "capture", "capture"] for _ in range(SPRITE_HEIGHT)],
    "i": [["initial"] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)],
    "c": [["initial"] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)],
    "I": [["initial"] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)],
    "M": [["move"] * SPRITE_WIDTH, ["blocker"] * SPRITE_WIDTH],
    "H": [["capture"] * SPRITE_WIDTH, ["blocker"] * SPRITE_WIDTH],
    "#": [["move", "move", "capture", "capture"], ["blocker"] * SPRITE_WIDTH],
}


class Square(Widget):
    COMPONENT_CLASSES = {
        "board--white-square",
        "board--black-square",
        "board--piece",
        "board--blocker",
        "board--move",
        "board--capture",
        "board--move-capture",
        "board--initial",
    }

    piece = reactive(".")

    class Clicked(Message):
        def __init__(self, square: "Square") -> None:
            super().__init__()
            self.square = square

    def render_line(self, y: int) -> Strip:
        y = y % CELL_HEIGHT
        sprite_line = get_cell_lines(self.piece)[y]

        is_odd_col = ord(self.id[0]) % 2
        is_odd_row = int(self.id[1:]) % 2
        bg_style_name = "black-square" if (is_odd_row + is_odd_col) % 2 else "white-square"
        bg_style = self.get_component_rich_style(f"board--{bg_style_name}")

        segments: list[Segment] = []
        current_text = ""
        current_style = None
        for x, char in enumerate(sprite_line):
            fill_style_name = get_sprite_fill_style_name(self.piece, x, y)
            glyph_style_name = GLYPH_TO_STYLE_MAP.get(self.piece) if char != " " else None

            if fill_style_name:
                char_style = self.get_component_rich_style(f"board--{fill_style_name}")
            elif glyph_style_name:
                glyph_style = self.get_component_rich_style(f"board--{glyph_style_name}")
                char_style = bg_style + glyph_style
            else:
                char_style = bg_style
            if current_style is None or char_style == current_style:
                current_text += char
                current_style = char_style
                continue
            segments.append(Segment(current_text, current_style))
            current_text = char
            current_style = char_style

        if current_text:
            segments.append(Segment(current_text, current_style))

        return Strip(segments)

    def on_click(self, event: Click) -> None:
        event.stop()
        self.post_message(self.Clicked(self))


def get_cell_lines(piece: str) -> list[str]:
    sprite = SPRITES.get(piece, SPRITES["."])
    blank_row = " " * CELL_WIDTH
    left_padding = (CELL_WIDTH - SPRITE_WIDTH) // 2
    right_padding = CELL_WIDTH - SPRITE_WIDTH - left_padding
    top_padding = (CELL_HEIGHT - SPRITE_HEIGHT) // 2
    bottom_padding = CELL_HEIGHT - SPRITE_HEIGHT - top_padding

    return (
        [blank_row] * top_padding
        + [(" " * left_padding) + row + (" " * right_padding) for row in sprite]
        + [blank_row] * bottom_padding
    )


def is_within_sprite_box(x: int, y: int) -> bool:
    left_padding = (CELL_WIDTH - SPRITE_WIDTH) // 2
    top_padding = (CELL_HEIGHT - SPRITE_HEIGHT) // 2
    return (
        left_padding <= x < left_padding + SPRITE_WIDTH
        and top_padding <= y < top_padding + SPRITE_HEIGHT
    )


def get_sprite_fill_style_name(piece: str, x: int, y: int) -> str | None:
    if not is_within_sprite_box(x, y):
        return None

    fills = SPRITE_FILL_MAP.get(piece)
    if fills is None:
        return None

    left_padding = (CELL_WIDTH - SPRITE_WIDTH) // 2
    top_padding = (CELL_HEIGHT - SPRITE_HEIGHT) // 2
    sprite_x = x - left_padding
    sprite_y = y - top_padding
    return fills[sprite_y][sprite_x]


class HelpLegendSprite(Widget):
    COMPONENT_CLASSES = {
        "board--piece",
        "board--blocker",
        "board--move",
        "board--capture",
        "board--move-capture",
        "board--initial",
    }

    def __init__(self, piece: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.piece = piece

    def render_line(self, y: int) -> Strip:
        y = y % SPRITE_HEIGHT
        segments: list[Segment] = []
        current_text = ""
        current_style = None
        sprite_line = SPRITES.get(self.piece, SPRITES["."])[y]

        for x, char in enumerate(sprite_line):
            fill_style_name = SPRITE_FILL_MAP.get(self.piece, [[None] * SPRITE_WIDTH] * SPRITE_HEIGHT)[y][x]
            glyph_style_name = GLYPH_TO_STYLE_MAP.get(self.piece) if char != " " else None

            if fill_style_name:
                char_style = self.get_component_rich_style(f"board--{fill_style_name}")
            elif glyph_style_name:
                char_style = self.get_component_rich_style(f"board--{glyph_style_name}")
            else:
                char_style = None

            if current_style is None or char_style == current_style:
                current_text += char
                current_style = char_style
                continue
            segments.append(Segment(current_text, current_style))
            current_text = char
            current_style = char_style

        if current_text:
            segments.append(Segment(current_text, current_style))

        return Strip(segments)


class BoardWidget(Container):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.board_size = DEFAULT_BOARD_SIZE

    def on_mount(self) -> None:
        self.styles.layout = "grid"

    async def setup_board(self):
        await self.remove_children()
        self.styles.width = self.board_size * CELL_WIDTH + BOARD_FRAME_WIDTH
        self.styles.height = self.board_size * CELL_HEIGHT + BOARD_FRAME_HEIGHT
        self.styles.grid_size_columns = self.board_size
        self.styles.grid_size_rows = self.board_size
        self.styles.grid_columns = [CELL_WIDTH]
        self.styles.grid_rows = [CELL_HEIGHT]
        squares = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                square_id = f"{chr(ord('a') + x)}{self.board_size - y}"
                squares.append(Square(id=square_id))
        await self.mount_all(squares)

    def on_click(self, event: Click) -> None:
        if event.button != 1:
            return

        col = event.x // CELL_WIDTH
        row = event.y // CELL_HEIGHT
        if not (0 <= col < self.board_size and 0 <= row < self.board_size):
            return

        center = self.board_size // 2
        blocker_coord = (col - center, center - row)
        if blocker_coord == (0, 0):
            return

        new_blockers = self.app.blockers.copy()
        if blocker_coord in new_blockers:
            new_blockers.remove(blocker_coord)
        else:
            new_blockers.add(blocker_coord)
        self.app.blockers = new_blockers

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


class HelpScreen(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("f1", "close", "Close", priority=True),
        Binding("enter", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-dialog"):
            yield Static("Betza Visualizer Help", id="help-title")
            with Vertical(id="help-legend"):
                for index, (piece, label) in enumerate(HELP_LEGEND_ITEMS):
                    with Horizontal(classes="help-legend-item"):
                        yield HelpLegendSprite(piece=piece, id=f"help-legend-sprite-{index}")
                        yield Label(label, classes="help-legend-label")
            yield Static("Click board squares to toggle blockers. Press F1 or Esc to close.", id="help-shortcuts")

    def action_close(self) -> None:
        self.dismiss()


class BetzaChessApp(App):
    CSS_PATH = "style.tcss"
    BINDINGS = [
        Binding("f2", "toggle_dark", "Dark Mode", priority=True),
        ("ctrl+l", "load_variants", "Load Variants"),
        Binding("f1", "show_help", "Help", priority=True),
    ]

    board_size = reactive(DEFAULT_BOARD_SIZE)
    moves = reactive([])
    blockers = reactive(set())

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="app-layout"):
                with Horizontal(id="controls-row"):
                    yield Select([], id="variant_select")
                    yield Input(placeholder="Try Xiangqi Horse: nN", id="betza_input")
                    yield Select(
                        [
                            ("5x5", 5),
                            ("7x7", 7),
                            ("9x9", 9),
                            ("11x11", 11),
                            ("13x13", 13),
                            ("15x15", 15),
                        ],
                        value=DEFAULT_BOARD_SIZE,
                        id="board_size_select",
                    )

                with Horizontal(id="workspace-row"):
                    yield ListView(id="piece_catalog_list")
                    with Container(id="board-panel"):
                        yield BoardWidget(id="board")
        yield Footer()

    async def on_mount(self) -> None:
        self.parser = BetzaParser()
        with open("fsf_built_in_variants_catalog.json", "r") as f:
            self.fsf_catalog = json.load(f)
        with open("fsf_built_in_variant_properties.json", "r") as f:
            self.fsf_variant_properties = json.load(f)
        self.piece_catalog = self.fsf_catalog
        self.query_one(Input).focus()
        self.populate_variant_select()
        self.populate_piece_list()
        board = self.query_one(BoardWidget)
        board.board_size = self.board_size
        await board.setup_board()
        self.call_next(self.update_board)

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
                        (atom_x, atom_y),
                        (-atom_x, atom_y),
                        (atom_x, -atom_y),
                        (-atom_x, -atom_y),
                        (atom_y, atom_x),
                        (-atom_y, atom_x),
                        (atom_y, -atom_x),
                        (-atom_y, -atom_x),
                    ]
                    step = next(
                        (
                            s
                            for s in possible_steps
                            if s[0] != 0
                            and s[1] != 0
                            and x % s[0] == 0
                            and y % s[1] == 0
                            and x // s[0] == y // s[1]
                        ),
                        None,
                    )
                    if step:
                        dx, dy = step
                    else:
                        dx, dy = 0, 0

                if dx == 0 and dy == 0:
                    path_len = 0
                elif dx != 0:
                    path_len = abs(x // dx)
                else:
                    path_len = abs(y // dy)

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
                    if abs(x) > abs(y):
                        block_x = sign(x)
                    elif abs(y) > abs(x):
                        block_y = sign(y)
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
                    if char == "m":
                        char = "i"
                    elif char == "x":
                        char = "c"
                    elif char == "X":
                        char = "I"
                if is_on_blocker:
                    if char == "m":
                        char = "M"
                    elif char == "x":
                        char = "H"
                    elif char == "X":
                        char = "#"
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
        square_id = message.square.id
        x_char = square_id[0]
        y_char = square_id[1:]

        x = ord(x_char) - ord('a')
        y = self.board_size - int(y_char)

        center = self.board_size // 2
        blocker_x = x - center
        blocker_y = center - y

        if (blocker_x, blocker_y) == (0, 0):
            return

        blocker_coord = (blocker_x, blocker_y)
        new_blockers = self.blockers.copy()
        if blocker_coord in new_blockers:
            new_blockers.remove(blocker_coord)
        else:
            new_blockers.add(blocker_coord)
        self.blockers = new_blockers

    async def watch_board_size(self, new_size: int) -> None:
        if not self.is_mounted:
            return
        board = self.query_one(BoardWidget)
        board.board_size = new_size
        await board.setup_board()
        self.blockers = set()
        betza = self.query_one("#betza_input", Input).value
        self.moves = self.parser.parse(betza, board_size=new_size)

    def watch_moves(self, new_moves: list) -> None:
        self.update_board()

    def watch_blockers(self, new_blockers: set) -> None:
        self.update_board()

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

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

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
            list_view.append(
                PieceListItem(piece_name=piece["name"], piece_variant=piece["variant"], piece_betza=piece["betza"])
            )

if __name__ == "__main__":
    app = BetzaChessApp()
    app.run()
