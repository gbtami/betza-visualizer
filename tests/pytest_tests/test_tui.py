import pytest
from textual.pilot import Pilot
from main import BetzaChessApp, BoardWidget, CELL_HEIGHT, CELL_WIDTH, SPRITES, Square


@pytest.fixture
async def pilot():
    app = BetzaChessApp()
    async with app.run_test(size=(180, 80)) as pilot:
        await pilot.pause()
        yield pilot


async def test_piece_catalog_selection(pilot: Pilot):
    """
    Test that selecting a piece from the catalog updates the input field.
    """
    # Find the ListView
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Ensure the list has items
    assert len(list_view.children) > 0

    # Press down arrow 3 times to highlight the third item (3check Knight)
    await pilot.press("down", "down", "down")
    await pilot.press("enter")
    await pilot.pause()

    # Check that the input field has been updated
    input_widget = pilot.app.query_one("#betza_input")
    assert input_widget.value == "N"

    # Press down arrow 1 more times to highlight the 4. item (3check Pawn)
    await pilot.press("down")
    await pilot.press("enter")
    await pilot.pause()
    assert input_widget.value == "fmWfceF" + "ifmnD"


def get_board_string(app: BetzaChessApp) -> str:
    """
    Gets the board layout from the BoardWidget and formats it as a string.
    """
    board_widget = app.query_one("#board")
    board_layout = board_widget.get_board_layout()
    return "\n".join("".join(row) for row in board_layout)


def count_moves_on_board(app: BetzaChessApp) -> int:
    """
    Counts the number of move indicators on the board.
    """
    board_text = get_board_string(app)
    move_chars = {"m", "x", "X", "H", "#", "i", "I", "c"}
    return sum(1 for char in board_text if char in move_chars)


async def test_board_uses_4_by_8_sprite_squares(pilot: Pilot):
    """
    Tests that the TUI board exposes the requested 4x8 sprite cell geometry.
    """
    center = pilot.app.board_size // 2
    square_id = f"#{chr(ord('a') + center)}{center + 1}"
    center_square = pilot.app.query_one(square_id, Square)

    assert center_square.size.width == CELL_WIDTH
    assert center_square.size.height == CELL_HEIGHT

    rendered_rows = [center_square.render_line(y) for y in range(CELL_HEIGHT)]
    assert [row.text for row in rendered_rows] == SPRITES["🧚"]
    assert [row.cell_length for row in rendered_rows] == [CELL_WIDTH] * CELL_HEIGHT


async def test_board_size_select_rebuilds_sprite_board(pilot: Pilot):
    """
    Tests that selecting smaller board sizes rebuilds squares without duplicate IDs.
    """
    board = pilot.app.query_one(BoardWidget)
    size_select = pilot.app.query_one("#board_size_select")

    for board_size in [13, 11, 9, 7, 5]:
        size_select.value = board_size
        await pilot.pause()

        assert pilot.app.board_size == board_size
        assert board.board_size == board_size
        assert len(board.query(Square)) == board_size * board_size
        assert pilot.app.query_one(f"#a{board_size}", Square)
        assert not pilot.app.query(f"#a{board_size + 2}")


async def set_betza(pilot: Pilot, betza: str) -> None:
    input_widget = pilot.app.query_one("#betza_input")
    pilot.app.blockers = set()
    input_widget.value = ""
    await pilot.pause()
    input_widget.value = betza
    await pilot.pause()


def catalog_betza(app: BetzaChessApp, name: str, variant: str | None = None) -> str:
    for piece in app.piece_catalog:
        if piece["name"] == name and (variant is None or piece["variant"] == variant):
            return piece["betza"]
    raise AssertionError(f"Missing catalog piece {name!r} variant {variant!r}")


async def test_board_move_and_blocker_behaviors(pilot: Pilot):
    """
    Tests board move rendering and blocker interactions in a single app session.
    """
    center = pilot.app.board_size // 2

    await set_betza(pilot, catalog_betza(pilot.app, "Knight", "3check"))
    assert count_moves_on_board(pilot.app) == 8

    initial_blockers = pilot.app.blockers.copy()
    await pilot.click("#legend")
    await pilot.pause()
    assert pilot.app.blockers == initial_blockers

    click_offset = (center * CELL_WIDTH + CELL_WIDTH // 2, (center - 1) * CELL_HEIGHT + CELL_HEIGHT // 2)
    await pilot.click("#board", offset=click_offset)
    await pilot.pause()
    assert len(pilot.app.blockers) == 1
    await pilot.click("#board", offset=click_offset)
    await pilot.pause()
    assert not pilot.app.blockers

    await set_betza(pilot, catalog_betza(pilot.app, "Janggi Cannon"))
    assert count_moves_on_board(pilot.app) == 0
    await pilot.click("#board", offset=(center * CELL_WIDTH + CELL_WIDTH // 2, (center - 2) * CELL_HEIGHT + 2))
    await pilot.pause()
    assert count_moves_on_board(pilot.app) > 0

    await set_betza(pilot, catalog_betza(pilot.app, "Knight", "3check"))
    await pilot.click("#board", offset=click_offset)
    await pilot.pause()
    assert count_moves_on_board(pilot.app) == 8

    await set_betza(pilot, catalog_betza(pilot.app, "Horse", "xiangqi"))
    assert count_moves_on_board(pilot.app) == 8
    await pilot.click("#board", offset=click_offset)
    await pilot.pause()
    assert count_moves_on_board(pilot.app) == 6

    await set_betza(pilot, catalog_betza(pilot.app, "Cannon", "xiangqi"))
    await pilot.click("#board", offset=(center * CELL_WIDTH + CELL_WIDTH // 2, (center - 2) * CELL_HEIGHT + 2))
    await pilot.click("#board", offset=(center * CELL_WIDTH + CELL_WIDTH // 2, (center - 3) * CELL_HEIGHT + 2))
    await pilot.pause()
    board_layout = pilot.app.query_one(BoardWidget).get_board_layout()
    assert board_layout[center - 4][center] == "."

    await set_betza(pilot, catalog_betza(pilot.app, "Elephant", "xiangqi"))
    assert pilot.app.query_one("#betza_input").value == "nA"
    assert count_moves_on_board(pilot.app) == 4
    await pilot.click(
        "#board",
        offset=((center + 1) * CELL_WIDTH + CELL_WIDTH // 2, (center - 1) * CELL_HEIGHT + CELL_HEIGHT // 2),
    )
    await pilot.pause()
    assert count_moves_on_board(pilot.app) == 3

    await set_betza(pilot, catalog_betza(pilot.app, "Janggi Elephant"))
    assert pilot.app.query_one("#betza_input").value == "nZ"
    assert count_moves_on_board(pilot.app) == 8
    await pilot.click(
        "#board",
        offset=((center + 1) * CELL_WIDTH + CELL_WIDTH // 2, center * CELL_HEIGHT + CELL_HEIGHT // 2),
    )
    await pilot.pause()
    board_layout = pilot.app.query_one(BoardWidget).get_board_layout()
    assert board_layout[center - 2][center + 3] == "."
    assert board_layout[center + 2][center + 3] == "."

    await pilot.click("#board", offset=(center * CELL_WIDTH + CELL_WIDTH // 2, (center - 1) * CELL_HEIGHT + 2))
    await pilot.pause()
    board_layout = pilot.app.query_one(BoardWidget).get_board_layout()
    assert board_layout[center - 3][center + 2] == "."
    assert board_layout[center - 3][center - 2] == "."

    await set_betza(pilot, "iW")
    board_text = get_board_string(pilot.app)
    assert "I" in board_text
    assert "X" not in board_text
