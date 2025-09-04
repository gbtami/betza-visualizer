import pytest
from textual.pilot import Pilot
from main import BetzaChessApp


@pytest.fixture
async def pilot():
    app = BetzaChessApp()
    async with app.run_test() as pilot:
        yield pilot


def count_moves_on_board(board_text: str) -> int:
    """
    Counts the number of move indicators on the board.
    """
    move_chars = {"m", "x", "X", "H", "#"}
    return sum(1 for char in board_text if char in move_chars)


async def test_xiangqi_elephant_moves(pilot: Pilot):
    """
    Test move calculation for the Xiangqi Elephant with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Select Xiangqi Elephant (index 17)
    for _ in range(18):
        await pilot.press("down")
    await pilot.press("enter")
    await pilot.pause()

    assert pilot.app.query_one("#betza_input").value == "nA"
    assert count_moves_on_board(pilot.app.render_board()) == 4

    # Place a blocker at (1, 1)
    center = pilot.app.board_size // 2
    # Click at col = center + 1, row = center - 1
    # event.x = (center + 1) * 2 + 1
    # event.y = (center - 1) + 2
    await pilot.click("#board", offset=((center + 1) * 2 + 1, center - 1 + 2))
    await pilot.pause()

    assert count_moves_on_board(pilot.app.render_board()) == 3
