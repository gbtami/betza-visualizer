import pytest
from textual.pilot import Pilot
from main import BetzaChessApp

@pytest.fixture
async def pilot():
    app = BetzaChessApp()
    async with app.run_test() as pilot:
        yield pilot

async def test_piece_catalog_selection(pilot: Pilot):
    """
    Test that selecting a piece from the catalog updates the input field.
    """
    await pilot.pause()

    # Find the ListView
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Ensure the list has items
    assert len(list_view.children) > 0

    # Press down arrow 3 times to highlight the third item (Amazon)
    await pilot.press("down", "down", "down")
    await pilot.press("enter")
    await pilot.pause()

    # Check that the input field has been updated
    input_widget = pilot.app.query_one("#betza_input")
    assert input_widget.value == "QN"

    # Press down arrow 2 more times to highlight the fifth item (Berolina Pawn)
    await pilot.press("down", "down")
    await pilot.press("enter")
    await pilot.pause()
    assert input_widget.value == "mfFcefWimfnA"


def count_moves_on_board(board_text: str) -> int:
    """
    Counts the number of move indicators on the board.
    """
    move_chars = {"m", "x", "X", "H", "#"}
    return sum(1 for char in board_text if char in move_chars)


async def test_janggi_cannon_moves(pilot: Pilot):
    """
    Test move calculation for the Janggi Cannon with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Select Janggi Cannon (index 6)
    for _ in range(7):
        await pilot.press("down")
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app.render_board()) == 0

    # Place a blocker 2 squares forward (y = 2)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=(center * 2 + 1, center - 2 + 2))
    await pilot.pause()

    assert count_moves_on_board(pilot.app.render_board()) > 0


async def test_xiangqi_horse_moves(pilot: Pilot):
    """
    Test move calculation for the Xiangqi Horse with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Select Xiangqi Horse (index 27)
    for _ in range(28):
        await pilot.press("down")
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app.render_board()) == 8

    # Place a blocker 1 square forward (y = 1)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=(center * 2 + 1, center - 1 + 2))
    await pilot.pause()

    assert count_moves_on_board(pilot.app.render_board()) == 6
