import pytest
from textual.pilot import Pilot
from main import BetzaChessApp, BoardWidget


@pytest.fixture
async def pilot():
    app = BetzaChessApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
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


async def test_orthodox_knight_moves(pilot: Pilot):
    """
    Tests that the Orthodox Knight has 8 moves on an empty board.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select 3check Knight
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Knight" and item.piece_variant == "3check":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app) == 8


async def test_janggi_cannon_moves(pilot: Pilot):
    """
    Test move calculation for the Janggi Cannon with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Janggi Cannon
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Janggi Cannon":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app) == 0

    # Place a blocker 2 squares forward (y = 2)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=((center) * 8 + 4, (center - 2) * 4 + 2))
    await pilot.pause()

    assert count_moves_on_board(pilot.app) > 0


async def test_leaper_unblocked(pilot: Pilot):
    """
    Tests that a standard leaper (Knight) is not blocked by an adjacent piece.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select 3check Knight
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Knight" and item.piece_variant == "3check":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app) == 8

    # Place a blocker 1 square forward (y = 1)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=((center) * 8 + 4, (center - 1) * 4 + 2))
    await pilot.pause()

    # The knight should not be blocked, so there should still be 8 moves.
    assert count_moves_on_board(pilot.app) == 8


async def test_xiangqi_horse_moves(pilot: Pilot):
    """
    Test move calculation for the Xiangqi Horse with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Xiangqi Horse
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Horse" and item.piece_variant == "xiangqi":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app) == 8

    # Place a blocker 1 square forward (y = 1)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=(center * 8 + 4, (center - 1) * 4 + 2))
    await pilot.pause()

    assert count_moves_on_board(pilot.app) == 6


async def test_click_outside_board_does_nothing(pilot: Pilot):
    """
    Test that clicking outside the board does not add a blocker.
    """
    await pilot.pause()
    initial_blockers = pilot.app.blockers.copy()

    # Click on the legend, which is outside the board
    await pilot.click("#legend")
    await pilot.pause()

    assert pilot.app.blockers == initial_blockers


async def test_click_inside_board_toggles_blocker(pilot: Pilot):
    """
    Test that clicking inside the board adds and then removes a blocker.
    """
    await pilot.pause()
    initial_blocker_count = len(pilot.app.blockers)

    # Click on a cell to add a blocker
    center = pilot.app.board_size // 2
    click_offset = (center * 8 + 4, (center - 1) * 4 + 2)
    await pilot.click("#board", offset=click_offset)
    await pilot.pause()

    assert len(pilot.app.blockers) == initial_blocker_count + 1

    # Click on the same cell to remove the blocker
    await pilot.click("#board", offset=click_offset)
    await pilot.pause()

    assert len(pilot.app.blockers) == initial_blocker_count


async def test_xiangqi_cannon_cannot_jump_two_blockers(pilot: Pilot):
    """
    Tests that the Xiangqi Cannon cannot jump over two blockers.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Xiangqi Cannon
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Cannon" and item.piece_variant == "xiangqi":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    center = pilot.app.board_size // 2

    # Place blockers at (0, 2) and (0, 3)
    await pilot.click("#board", offset=(center * 8 + 4, (center - 2) * 4 + 2))
    await pilot.click("#board", offset=(center * 8 + 4, (center - 3) * 4 + 2))
    await pilot.pause()

    board_layout = pilot.app.query_one(BoardWidget).get_board_layout()

    # The cannon should not be able to jump over two blockers to capture at (0,4).
    # The character at that position should be an empty square '.'.
    assert board_layout[center - 4][center] == '.'


async def test_xiangqi_elephant_moves(pilot: Pilot):
    """
    Test move calculation for the Xiangqi Elephant with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Xiangqi Cannon
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Elephant" and item.piece_variant == "xiangqi":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert pilot.app.query_one("#betza_input").value == "nA"
    assert count_moves_on_board(pilot.app) == 4

    # Place a blocker at (1, 1)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=((center + 1) * 8 + 4, (center - 1) * 4 + 2))
    await pilot.pause()

    assert count_moves_on_board(pilot.app) == 3


async def test_janggi_elephant_moves(pilot: Pilot):
    """
    Test move calculation for the Janggi Elephant with blocker placement.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Janggi Elephant
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Janggi Elephant":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert pilot.app.query_one("#betza_input").value == "nZ"
    assert count_moves_on_board(pilot.app) == 8

    # Place a blocker at (1, 0)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=((center + 1) * 8 + 4, (center) * 4 + 2))
    await pilot.pause()

    # The two moves that step over (1,0) should be blocked: (3,2) and (3,-2)
    board_layout = pilot.app.query_one(BoardWidget).get_board_layout()
    assert board_layout[center - 2][center + 3] == '.'
    assert board_layout[center + 2][center + 3] == '.'

    # Place a blocker at (0, 1)
    await pilot.click("#board", offset=((center) * 8 + 4, (center - 1) * 4 + 2))
    await pilot.pause()

    # The two moves that step over (0,1) should be blocked: (2,3) and (-2,3)
    board_layout = pilot.app.query_one(BoardWidget).get_board_layout()
    assert board_layout[center - 3][center + 2] == '.'
    assert board_layout[center - 3][center - 2] == '.'


async def test_initial_move_character(pilot: Pilot):
    """
    Tests that an initial-only move is rendered with a special character.
    """
    await pilot.pause()
    input_widget = pilot.app.query_one("#betza_input")
    await pilot.click(input_widget)
    await pilot.press("i", "W")
    await pilot.pause()

    board_text = get_board_string(pilot.app)
    assert "I" in board_text
    assert "X" not in board_text
