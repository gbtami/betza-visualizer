import pytest
import json
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


def get_catalog_data():
    with open("piece_catalog.json", "r") as f:
        return json.load(f)

def get_variant_count():
    catalog = get_catalog_data()
    variants = set()
    for p in catalog:
        for v in p["variant"].split(","):
            variants.add(v.strip())
    return len(variants)

def get_piece_count_for_variant(variant):
    catalog = get_catalog_data()
    if variant == "All":
        return len(catalog)
    count = 0
    for p in catalog:
        if variant in [v.strip() for v in p["variant"].split(",")]:
            count += 1
    return count

async def test_orthodox_knight_moves(pilot: Pilot):
    """
    Tests that the Orthodox Knight has 8 moves on an empty board.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Orthodox Knight
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Knight" and item.piece_variant == "Orthodox":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app.query_one("#board").render()) == 8


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
        if item.piece_name == "Cannon (Korean)":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app.query_one("#board").render()) == 0

    # Place a blocker 2 squares forward (y = 2)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=(center * 2 + 1, center - 1))
    await pilot.pause()

    assert count_moves_on_board(pilot.app.query_one("#board").render()) > 0


async def test_leaper_unblocked(pilot: Pilot):
    """
    Tests that a standard leaper (Knight) is not blocked by an adjacent piece.
    """
    await pilot.pause()
    list_view = pilot.app.query_one("#piece_catalog_list")
    list_view.focus()
    await pilot.pause()

    # Find and select Orthodox Knight
    for i, item in enumerate(list_view.children):
        if item.piece_name == "Knight" and item.piece_variant == "Orthodox":
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app.query_one("#board").render()) == 8

    # Place a blocker 1 square forward (y = 1)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=(center * 2 + 1, center + 1))
    await pilot.pause()

    # The knight should not be blocked, so there should still be 8 moves.
    assert count_moves_on_board(pilot.app.query_one("#board").render()) == 8


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
        if item.piece_name == "Horse" and "Xiangqi" in item.piece_variant:
            list_view.index = i
            break
    await pilot.press("enter")
    await pilot.pause()

    assert count_moves_on_board(pilot.app.query_one("#board").render()) == 8

    # Place a blocker 1 square forward (y = 1)
    center = pilot.app.board_size // 2
    await pilot.click("#board", offset=(center * 2 + 1, center + 1))
    await pilot.pause()

    assert count_moves_on_board(pilot.app.query_one("#board").render()) == 6
