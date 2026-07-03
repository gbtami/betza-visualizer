from betza_visualizer import BetzaSvgOptions, render_betza_svg


def test_render_betza_svg_contains_svg_and_title():
    svg = render_betza_svg("N", BetzaSvgOptions(piece_label="N", title="Knight test"))

    assert svg.startswith('<svg class="betza-diagram"')
    assert "<title>Knight test</title>" in svg
    assert ">N</text>" in svg


def test_render_betza_svg_escapes_user_content():
    svg = render_betza_svg(
        "W",
        BetzaSvgOptions(piece_label='<script>alert("x")</script>', title='Bad " title <x>'),
    )

    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg
    assert 'aria-label="Bad &quot; title &lt;x&gt;"' in svg
