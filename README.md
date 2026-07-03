# betza-visualizer

Visualizes [fairy chess piece](https://en.wikipedia.org/wiki/List_of_fairy_chess_pieces) movements from their [Betza notation](https://en.wikipedia.org/wiki/Betza%27s_funny_notation).

The project contains:

- a reusable dependency-free Python package, importable as `betza_visualizer`
- a Python Textual TUI frontend
- a browser frontend using TypeScript, HTML, CSS, and SVG

## Python library usage

The core parser and SVG renderer have no runtime dependencies:

```python
from betza_visualizer import BetzaParser, BetzaSvgOptions, render_betza_svg

moves = BetzaParser().parse("BN", board_size=11)
svg = render_betza_svg("BN", BetzaSvgOptions(piece_label="A", title="Archbishop movement"))
```

The generated SVG string is intended to be embedded directly into documentation pages.

## Optional TUI dependencies

The Textual frontend needs optional dependencies:

```bash
pip install 'betza-visualizer[tui]'
python main.py
```

## Development

```bash
pip install -e '.[dev]'
python -m pytest tests/python_unittests
```

## Publishing

The package metadata is defined in `pyproject.toml`. A local wheel can be built with:

```bash
python -m build
```

Almost everything in this repository made by using Google AI tools.

Google AI Studio, gemini-cli, Google Labs Jules using gemini-2.5-pro, gemini2.5-flash

codex-cli using gpt-5.4-codex, gpt-5.5-codex
