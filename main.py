import math
from typing import List, Tuple, Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical
from betza_parser import BetzaParser

def sign(n):
    return int(math.copysign(1, n)) if n != 0 else 0

class BetzaChessApp(App):
    CSS_PATH = "style.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Vertical(
            Input(placeholder="Try Xiangqi Horse: nN", id="betza_input"),
            Static(self.render_board(), id="board"),
        )

    def on_mount(self) -> None:
        self.parser = BetzaParser()
        self.query_one(Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        moves = self.parser.parse(event.value)
        self.query_one("#board").update(self.render_board(moves))

    def render_board(self, moves: List[Tuple[int, int, str, Optional[str], str, str]] = []) -> str:
        board_size = 13
        center = board_size // 2
        board = [["." for _ in range(board_size)] for _ in range(board_size)]
        board[center][center] = "🧚"

        hurdles = set()
        special_moves = [m for m in moves if m[3] is not None or m[4] != 'normal']

        if special_moves:
            hopper_moves = [m for m in special_moves if m[3] is not None]
            if hopper_moves:
                unique_directions_set = {(sign(x), sign(y)) for x, y, _, _, _, _ in hopper_moves}
                unique_directions = sorted(list(unique_directions_set))
                if len(unique_directions) == 4 and any(d[0]==0 or d[1]==0 or d[0]==d[1] for d in unique_directions):
                    unique_directions.pop()
                for dx, dy in unique_directions:
                    hurdles.add((dx * 2, dy * 2))

            nj_leapers = [m for m in special_moves if m[4] != 'normal']
            if nj_leapers:
                hurdles.update([(0, 1), (-1, 0)])

            # --- FIX: Render hurdles to the board FIRST ---
            for hx, hy in hurdles:
                if 0 <= center - hy < board_size and 0 <= center + hx < board_size:
                    board[center - hy][center + hx] = "♙"

        move_map = {'move_capture': 'C', 'move': 'M', 'move_capture': 'X'}

        # --- FIX: Render moves SECOND, allowing them to overwrite hurdles if necessary ---
        for x, y, move_type, hop_type, jump_type, atom in moves:
            display_y, display_x = center - y, center + x
            if not (0 <= display_y < board_size and 0 <= display_x < board_size):
                continue

            is_valid = True
            if jump_type == 'non-jumping':
                block_x, block_y = 0, 0
                if abs(x) > abs(y): block_x = sign(x)
                elif abs(y) > abs(x): block_y = sign(y)

                if (block_x, block_y) in hurdles:
                    is_valid = False

            elif jump_type == 'jumping':
                is_valid = False
                block_x, block_y = 0, 0
                if abs(x) > abs(y): block_x = sign(x)
                elif abs(y) > abs(x): block_y = sign(y)

                if (block_x, block_y) in hurdles:
                    is_valid = True

            elif hop_type is not None:
                is_valid = False
                dx, dy = sign(x), sign(y)
                path = [(i * dx, i * dy) for i in range(1, max(abs(x), abs(y)))]
                hurdles_on_path = [p for p in path if p in hurdles]
                if len(hurdles_on_path) == 1:
                    if hop_type == 'p': is_valid = True
                    elif hop_type == 'g':
                        hurdle_pos = hurdles_on_path[0]
                        if x == hurdle_pos[0] + dx and y == hurdle_pos[1] + dy:
                            is_valid = True

            if is_valid:
                # This will now draw a move marker even if a hurdle was there before
                board[display_y][display_x] = move_map.get(move_type, '?')

        return "\n".join(" ".join(row) for row in board)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

if __name__ == "__main__":
    app = BetzaChessApp()
    app.run()
