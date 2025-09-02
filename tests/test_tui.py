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
