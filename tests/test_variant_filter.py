import pytest
import json
from playwright.sync_api import Page, expect


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
def test_variant_filter_orthodox(page: Page):
    """
    Tests filtering by the 'Orthodox' variant.
    """
    page.goto("http://localhost:8080")
    variant_select = page.locator("#variant-select")
    variant_select.select_option("Orthodox")

    piece_catalog = page.locator("#piece-catalog-content")
    expected_count = get_piece_count_for_variant("Orthodox")
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
    variant_select.select_option("Orthodox")  # First filter
    variant_select.select_option("All")  # Then select all

    piece_catalog = page.locator("#piece-catalog-content")
    expected_count = get_piece_count_for_variant("All")
    expect(piece_catalog.locator(".piece-catalog-item")).to_have_count(expected_count)
