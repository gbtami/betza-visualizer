import pytest
import json
from playwright.sync_api import Page, expect

XIANGQI_ELEPHANT_BETZA = "nA"


def test_xiangqi_elephant_empty_board(page: Page):
    """
    Tests that the Xiangqi Elephant has 4 moves on an empty board.
    """
    page.goto("http://localhost:8080")

    # Select the Xiangqi Elephant from the catalog
    page.locator("#left-column .piece-catalog-item", has=page.get_by_text("xiangqi")).get_by_text("Elephant", exact=True).click()

    # Verify the input is updated
    expect(page.locator("#betzaInput")).to_have_value(XIANGQI_ELEPHANT_BETZA)

    # The move indicators for 'move/capture' are composed of two path elements.
    # So, for 4 moves, we expect 8 path elements.
    expect(page.locator("g > path")).to_have_count(4 * 2)


def test_xiangqi_elephant_blocked(page: Page):
    """
    Tests that the Xiangqi Elephant's moves are correctly blocked.
    """
    # Listen for console logs
    page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))

    page.goto("http://localhost:8080")

    # Select the Xiangqi Elephant
    page.locator("#left-column .piece-catalog-item", has=page.get_by_text("xiangqi")).get_by_text("Elephant", exact=True).click()
    expect(page.locator("#betzaInput")).to_have_value(XIANGQI_ELEPHANT_BETZA)

    # Get board dimensions
    board = page.locator("#board-container svg")
    view_box_str = board.get_attribute("viewBox")
    _, _, width, _ = view_box_str.split(" ")

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
    expect(page.locator("g > path")).to_have_count(3 * 2)


def test_leaper_unblocked(page: Page):
    """
    Tests that a standard leaper (Knight) is not blocked by an adjacent piece.
    """
    page.goto("http://localhost:8080")

    # Select the Knight from the catalog
    page.locator("#left-column .piece-catalog-item", has=page.get_by_text("3check")).get_by_text("Knight", exact=True).click()

    # Verify the input is updated
    expect(page.locator("#betzaInput")).to_have_value("N")

    # A Knight has 8 moves, which are all move/capture.
    # Each move/capture indicator is composed of two path elements.
    expect(page.locator("g > path")).to_have_count(8 * 2)

    # Get board dimensions
    board = page.locator("#board-container svg")
    view_box_str = board.get_attribute("viewBox")
    _, _, width, _ = view_box_str.split(" ")

    board_size = int(width) / 40
    center = board_size // 2
    cell_size = 40

    # Place a blocker at (1, 0)
    target_c = center + 1
    target_r = center
    target_rect_x = int(target_c * cell_size)
    target_rect_y = int(target_r * cell_size)
    page.locator(f'rect[x="{target_rect_x}"][y="{target_rect_y}"]').click()

    # Wait for the blocker to appear
    expect(page.locator('text[fill="#606060"]')).to_have_count(1)

    # The knight should not be blocked, so there should still be 8 moves.
    expect(page.locator("g > path")).to_have_count(8 * 2)


def test_slider_moves_are_on_board(page: Page):
    """
    Tests that a slider piece (e.g., Nightrider N0) does not render moves
    that are off the board.
    """
    page.goto("http://localhost:8080")

    # Select a small board size to make it easy to have off-board moves
    page.locator("#boardSizeSelect").select_option("5")

    # Set the input to N0 (Nightrider)
    page.locator("#betzaInput").fill("N0")

    # On a 5x5 board, a Nightrider from the center has 8 on-board moves.
    # The parser will generate more moves that are off-board.
    # We expect that only the 8 on-board moves are rendered.
    # Nightrider moves are move/capture, so they are composed of two paths.
    expect(page.locator("g > path")).to_have_count(8 * 2)


def test_xiangqi_cannon_two_blockers(page: Page):
    """
    Tests that the Xiangqi Cannon cannot jump over two blockers.
    """
    page.goto("http://localhost:8080")

    # Select the Cannon from the catalog. We need to find the one for Xiangqi.
    # There are two "Cannon" pieces, one for Xiangqi and one for Janggi (Korean).
    # We can identify it by looking for its parent that contains the variant name.
    page.locator("#left-column .piece-catalog-item", has=page.get_by_text("xiangqi")).get_by_text("Cannon", exact=True).first.click()

    # Get board dimensions
    board = page.locator("#board-container svg")
    view_box_str = board.get_attribute("viewBox")
    _, _, width, _ = view_box_str.split(" ")

    board_size = int(width) / 40
    center = board_size // 2
    cell_size = 40

    # Place a blocker at (0, 2)
    target_c = center + 0
    target_r = center - 2
    target_rect_x = int(target_c * cell_size)
    target_rect_y = int(target_r * cell_size)
    page.locator(f'rect[x="{target_rect_x}"][y="{target_rect_y}"]').click()

    # Place another blocker at (0, 3)
    target_c = center + 0
    target_r = center - 3
    target_rect_x = int(target_c * cell_size)
    target_rect_y = int(target_r * cell_size)
    page.locator(f'rect[x="{target_rect_x}"][y="{target_rect_y}"]').click()

    # Wait for the blockers to appear
    expect(page.locator('text[fill="#606060"]')).to_have_count(2)

    # The cannon should not be able to jump over two blockers.
    # So there should be no move indicator at (0, 4).
    target_cx = (center + 0) * cell_size + cell_size / 2
    target_cy = (center - 4) * cell_size + cell_size / 2

    # There should be no move indicator group at this position.
    expect(page.locator(f'g[transform="translate({target_cx}, {target_cy})"]')).to_have_count(0)


def get_catalog_data():
    with open("fsf_built_in_variants_catalog.json", "r") as f:
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


@pytest.mark.e2e
def test_variant_filter_population(page: Page):
    """
    Tests that the variant filter dropdown is populated with the correct number of variants.
    """
    page.goto("http://localhost:8080")
    variant_select = page.locator("#variant-select")
    expected_count = get_variant_count() + 1  # +1 for "All"
    expect(variant_select.locator("option")).to_have_count(expected_count)


@pytest.mark.e2e
def test_variant_filter_3check(page: Page):
    """
    Tests filtering by the '3check' variant.
    """
    page.goto("http://localhost:8080")
    variant_select = page.locator("#variant-select")
    variant_select.select_option("3check")

    piece_catalog = page.locator("#left-column #piece-catalog-content")
    expected_count = get_piece_count_for_variant("3check")
    expect(piece_catalog.locator(".piece-catalog-item")).to_have_count(expected_count)

    # Check that the input is cleared
    expect(page.locator("#betzaInput")).to_have_value("")


@pytest.mark.e2e
def test_variant_filter_all(page: Page):
    """
    Tests that selecting 'All' shows all pieces.
    """
    page.goto("http://localhost:8080")
    variant_select = page.locator("#variant-select")
    variant_select.select_option("3check")  # First filter
    variant_select.select_option("All")  # Then select all

    piece_catalog = page.locator("#left-column #piece-catalog-content")
    expected_count = get_piece_count_for_variant("All")
    expect(piece_catalog.locator(".piece-catalog-item")).to_have_count(expected_count)


@pytest.mark.e2e
def test_load_variants_from_ini(page: Page):
    """
    Tests that loading a variants.ini file updates the catalog and variant filter.
    """
    page.goto("http://localhost:8080")

    # Set up a listener for the file chooser
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="Load Variants").click()

    file_chooser = fc_info.value
    file_chooser.set_files("tests/variants.ini")

    # Wait for the new variant to appear in the dropdown
    variant_select = page.locator("#variant-select")
    expect(variant_select.locator('option[value="minishogi"]')).to_have_count(1)

    # Select the new variant
    variant_select.select_option("minishogi")

    # Check that the piece catalog is updated correctly
    # The minishogi variant in the test file has 8 pieces.
    piece_catalog = page.locator("#left-column #piece-catalog-content")
    expect(piece_catalog.locator(".piece-catalog-item")).to_have_count(8)
