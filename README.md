[![PyPI version](https://img.shields.io/pypi/v/betza-visualizer)](https://pypi.org/project/betza-visualizer/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/betza-visualizer)](https://pypi.org/project/betza-visualizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![TUI Tests](https://github.com/gbtami/betza-visualizer/actions/workflows/tui_tests.yml/badge.svg)](https://github.com/gbtami/betza-visualizer/actions/workflows/tui_tests.yml)
[![Web App Tests](https://github.com/gbtami/betza-visualizer/actions/workflows/web_tests.yml/badge.svg)](https://github.com/gbtami/betza-visualizer/actions/workflows/web_tests.yml)

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

## Try the web app

The browser frontend is available online:

<https://betza-visualizer.vercel.app/>

## Run the TUI locally

The Textual TUI frontend currently lives in the repository-level `main.py`, so clone the
repository frst:

```bash
git clone https://github.com/gbtami/betza-visualizer.git
cd betza-visualizer
```

Then install the optional TUI dependencies and start the app:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[tui]'
python main.py
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

If you use `uv`, the shorter equivalent is:

```
uv run --extra tui python main.py
```

Inside the TUI, type a Betza expression, pick a built-in piece from the list, change the
board size from the selector, or click board squares to toggle blockers. Press `F1` for
the in-app help and `Ctrl+L` to load pieces from a local `variants.ini` file.

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

Almost everything in this repository made by using Google and OpanAI tools.

Google AI Studio, gemini-cli, Google Labs Jules using gemini-2.5-pro, gemini2.5-flash

codex-cli using gpt-5.4-codex, gpt-5.5-codex

## TypeScript package

The repository also publishes the DOM-free `@gbtami/betza` package. It keeps
Betza parsing separate from visual rendering and provides a conservative
premove movement envelope suitable for chessground-style clients.

```ts
import { createBetzaPremove } from '@gbtami/betza';

const compiled = createBetzaPremove('fRffN');
if (compiled.ok) {
  const destinations = compiled.value({
    origin: [3, 3],
    color: 'white',
    board: { width: 8, height: 8 },
  });
}
```

Premove envelopes intentionally ignore occupancy, capture-only/move-only
modifiers, blockers, hopper screens, initial-only restrictions, check, and
variant-level legality. The opponent may change those facts before execution;
the game server remains authoritative.

`parseBetza()` mirrors Fairy-Stockfish's lenient, stateful parser: characters
that Fairy-Stockfish ignores are reported as warnings, but the understood
movement is still returned and used by `createBetzaPremove()`. Authoring tools
that want to reject ignored fragments can use `parseBetzaStrict()` instead.
The existing browser visualizer keeps its legacy parser behavior unchanged.
