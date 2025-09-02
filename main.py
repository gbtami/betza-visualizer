import math
import json
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label, Select
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.events import Click
from betza_parser import BetzaParser


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

LEGEND_TEXT = "m: Move | x: Capture | X: Move/Capture | ♙: Blocker | H: Capture on Blocker | #: Move/Capture on Blocker"


class BetzaChessApp(App):
    CSS_PATH = "style.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    board_size = reactive(DEFAULT_BOARD_SIZE)
    moves = reactive([])
    blockers = reactive(set())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with open("piece_catalog.json", "r") as f:
            piece_catalog = json.load(f)

        yield Vertical(
            Input(placeholder="Try Xiangqi Horse: nN", id="betza_input"),
            Select(
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
            ),
            Horizontal(
                ListView(id="piece_catalog_list"),
                Static(id="board"),
            ),
            Static(LEGEND_TEXT, id="legend"),
        )

    def on_mount(self) -> None:
        self.parser = BetzaParser()
        self.query_one("#board").update(self.render_board())
        self.query_one(Input).focus()

        list_view = self.query_one(ListView)
        with open("piece_catalog.json", "r") as f:
            piece_catalog = json.load(f)
        for piece in piece_catalog:
            list_view.append(
                PieceListItem(
                    piece_name=piece["name"],
                    piece_variant=piece["variant"],
                    piece_betza=piece["betza"],
                )
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, PieceListItem):
            self.query_one("#betza_input").value = event.item.piece_betza
            self.blockers = set()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.moves = self.parser.parse(event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "board_size_select":
            self.board_size = event.value

    def on_click(self, event: Click) -> None:
        if event.button != 1:
            return
        if self.query_one("#board").id != "board":
            return

        center = self.board_size // 2
        # The board characters are space-separated, and we need to account for
        # padding/border offsets.
        col = (event.x - 1) // 2
        row = event.y - 2

        blocker_x = col - center
        blocker_y = center - row

        if blocker_x == 0 and blocker_y == 0:
            return

        blocker_coord = (blocker_x, blocker_y)
        new_blockers = self.blockers.copy()
        if blocker_coord in new_blockers:
            new_blockers.remove(blocker_coord)
        else:
            new_blockers.add(blocker_coord)
        self.blockers = new_blockers

    def watch_board_size(self, new_size: int) -> None:
        self.blockers = set()
        self.query_one("#board").update(self.render_board())

    def watch_moves(self, new_moves: list) -> None:
        self.query_one("#board").update(self.render_board())

    def watch_blockers(self, new_blockers: set) -> None:
        self.query_one("#board").update(self.render_board())

    def render_board(self) -> str:
        board_size = self.board_size
        moves = self.moves
        center = board_size // 2
        board = [["." for _ in range(board_size)] for _ in range(board_size)]
        board[center][center] = "🧚"

        for bx, by in self.blockers:
            if 0 <= center - by < board_size and 0 <= center + bx < board_size:
                board[center - by][center + bx] = "♙"

        move_map = {"move_capture": "X", "move": "m", "capture": "x"}

        for x, y, move_type, hop_type, jump_type, atom in moves:
            display_y, display_x = center - y, center + x
            if not (0 <= display_y < board_size and 0 <= display_x < board_size):
                continue

            is_valid = None
            if hop_type is not None:
                is_valid = False
                dx, dy = sign(x), sign(y)
                path = [(i * dx, i * dy) for i in range(1, max(abs(x), abs(y)))]
                blockers_on_path = [p for p in path if p in self.blockers]
                if len(blockers_on_path) == 1:
                    if hop_type == "p":
                        is_valid = True
                    elif hop_type == "g":
                        blocker_pos = blockers_on_path[0]
                        if x == blocker_pos[0] + dx and y == blocker_pos[1] + dy:
                            is_valid = True
            elif jump_type == "jumping":
                is_valid = False
                block_x, block_y = 0, 0
                if abs(x) > abs(y):
                    block_x = sign(x)
                elif abs(y) > abs(x):
                    block_y = sign(y)
                if (block_x, block_y) in self.blockers:
                    is_valid = True
            elif jump_type == "non-jumping":
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
                char = move_map.get(move_type, "?")
                if is_on_blocker:
                    if char == "m":
                        char = "M"
                    elif char == "x":
                        char = "H"
                    elif char == "X":
                        char = "#"
                board[display_y][display_x] = char

        rendered_rows = []
        for row in board:
            row_str = " ".join(row)
            if "🧚" in row_str:
                row_str = row_str.replace(" 🧚", "🧚")
            rendered_rows.append(row_str)
        return "\n".join(rendered_rows)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


if __name__ == "__main__":
    app = BetzaChessApp()
    app.run()
