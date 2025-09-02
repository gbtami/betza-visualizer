import pytest
from playwright.sync_api import Page, expect

XIANGQI_ELEPHANT_NAME = 'Elephant (Chinese)'
XIANGQI_ELEPHANT_BETZA = 'nA'

def test_xiangqi_elephant_empty_board(page: Page):
    """
    Tests that the Xiangqi Elephant has 4 moves on an empty board.
    """
    page.goto('http://localhost:8080')

    # Select the Xiangqi Elephant from the catalog
    page.get_by_text(XIANGQI_ELEPHANT_NAME).click()

    # Verify the input is updated
    expect(page.locator('#betzaInput')).to_have_value(XIANGQI_ELEPHANT_BETZA)

    # The move indicators for 'move/capture' are composed of two path elements.
    # So, for 4 moves, we expect 8 path elements.
    expect(page.locator('g > path')).to_have_count(4 * 2)

def test_xiangqi_elephant_blocked(page: Page):
    """
    Tests that the Xiangqi Elephant's moves are correctly blocked.
    """
    # Listen for console logs
    page.on('console', lambda msg: print(f"BROWSER LOG: {msg.text}"))

    page.goto('http://localhost:8080')

    # Select the Xiangqi Elephant
    page.get_by_text(XIANGQI_ELEPHANT_NAME).click()
    expect(page.locator('#betzaInput')).to_have_value(XIANGQI_ELEPHANT_BETZA)

    # Get board dimensions
    board = page.locator('#board-container svg')
    view_box_str = board.get_attribute('viewBox')
    _, _, width, _ = view_box_str.split(' ')

    board_size = int(width) / 40  # CELL_SIZE is 40
    center = board_size // 2
    cell_size = 40

    # Place a blocker at (1, 1)
    # Corresponding cell coordinates are c = center + 1, r = center - 1
    target_c = center + 1
    target_r = center - 1

    # Find the rect element for the target cell and click it
    target_rect_x = int(target_c * cell_size)
    target_rect_y = int(target_r * cell_size)
    page.locator(f'rect[x="{target_rect_x}"][y="{target_rect_y}"]').click()

    # Wait for the blocker to appear
    expect(page.locator('text[fill="#606060"]')).to_have_count(1)

    # After blocking, one move is removed. We expect 3 moves * 2 paths = 6 paths.
    expect(page.locator('g > path')).to_have_count(3 * 2)
