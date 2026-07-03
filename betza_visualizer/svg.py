"""Small dependency-free SVG renderer for Betza movement diagrams."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any, Iterable

from .betza_parser import BetzaParser


@dataclass(frozen=True)
class BetzaSvgOptions:
    """Rendering options for :func:`render_betza_svg`.

    The default 11×11 board gives rider pieces enough room while keeping the
    generated diagram compact enough for documentation pages.
    """

    board_width: int = 11
    board_height: int = 11
    cell_size: int = 28
    piece_label: str = "✦"
    css_class: str = "betza-diagram"
    title: str | None = None
    show_coordinates: bool = False


_MOVE_COLOR = "#f2c94c"
_CAPTURE_COLOR = "#eb5757"
_INITIAL_COLOR = "#56ccf2"
_HOP_COLOR = "#9b51e0"
_LIGHT_SQUARE = "#f0d9b5"
_DARK_SQUARE = "#b58863"
_GRID_COLOR = "#6f543b"
_PIECE_COLOR = "#222222"


def render_betza_svg(betza: str, options: BetzaSvgOptions | None = None) -> str:
    """Return an inline SVG movement diagram for a Betza definition.

    The diagram is intentionally static: it shows the basic target squares from
    White's perspective. Hopper-style pieces are shown with a distinct dashed
    marker because their legal targets depend on intervening pieces.
    """

    opts = options or BetzaSvgOptions()
    board_width = max(3, opts.board_width)
    board_height = max(3, opts.board_height)
    cell_size = max(12, opts.cell_size)
    width = board_width * cell_size
    height = board_height * cell_size
    center_x = board_width // 2
    center_y = board_height // 2
    title = opts.title or f"Movement diagram for {betza}"

    parser = BetzaParser()
    moves = parser.parse(betza, board_size=max(board_width, board_height))
    targets = _merge_targets(moves, center_x, center_y, board_width, board_height)

    parts: list[str] = [
        (
            f'<svg class="{escape(opts.css_class, quote=True)}" xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'role="img" aria-label="{escape(title, quote=True)}">'
        ),
        f"<title>{escape(title)}</title>",
    ]

    for rank in range(board_height):
        for file_ in range(board_width):
            fill = _LIGHT_SQUARE if (rank + file_) % 2 == 0 else _DARK_SQUARE
            x = file_ * cell_size
            y = rank * cell_size
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}" />'
            )

    for target in targets:
        board_x = center_x + target["x"]
        board_y = center_y - target["y"]
        cx = board_x * cell_size + cell_size / 2
        cy = board_y * cell_size + cell_size / 2
        parts.append(_target_marker(cx, cy, cell_size, target))

    piece_cx = center_x * cell_size + cell_size / 2
    piece_cy = center_y * cell_size + cell_size / 2
    piece_r = cell_size * 0.34
    parts.append(
        f'<circle cx="{piece_cx:g}" cy="{piece_cy:g}" r="{piece_r:g}" fill="#ffffff" '
        f'stroke="{_PIECE_COLOR}" stroke-width="2" />'
    )
    parts.append(
        f'<text x="{piece_cx:g}" y="{piece_cy:g}" text-anchor="middle" dominant-baseline="central" '
        f'font-size="{cell_size * 0.48:g}" font-family="sans-serif" fill="{_PIECE_COLOR}">'
        f"{escape(opts.piece_label)}</text>"
    )

    if opts.show_coordinates:
        parts.extend(_coordinates(board_width, board_height, cell_size))

    parts.append(
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'fill="none" stroke="{_GRID_COLOR}" stroke-width="1" />'
    )
    parts.append("</svg>")
    return "".join(parts)


def _merge_targets(
    moves: Iterable[dict[str, Any]],
    center_x: int,
    center_y: int,
    board_width: int,
    board_height: int,
) -> list[dict[str, Any]]:
    merged: dict[tuple[int, int], dict[str, Any]] = {}
    for move in moves:
        x = int(move.get("x", 0))
        y = int(move.get("y", 0))
        if x == 0 and y == 0:
            continue
        board_x = center_x + x
        board_y = center_y - y
        if board_x < 0 or board_x >= board_width or board_y < 0 or board_y >= board_height:
            continue

        key = (x, y)
        target = merged.setdefault(
            key,
            {
                "x": x,
                "y": y,
                "move_type": move.get("move_type", "move_capture"),
                "initial_only": bool(move.get("initial_only")),
                "hop_type": move.get("hop_type"),
            },
        )
        target["move_type"] = _combine_move_types(str(target["move_type"]), str(move.get("move_type", "move_capture")))
        target["initial_only"] = bool(target["initial_only"]) or bool(move.get("initial_only"))
        target["hop_type"] = target.get("hop_type") or move.get("hop_type")

    return sorted(merged.values(), key=lambda item: (item["y"], item["x"]))


def _combine_move_types(left: str, right: str) -> str:
    if left == right:
        return left
    if "move_capture" in {left, right}:
        return "move_capture"
    if {left, right} == {"move", "capture"}:
        return "move_capture"
    return right


def _target_marker(cx: float, cy: float, cell_size: int, target: dict[str, Any]) -> str:
    radius = cell_size * 0.28
    stroke_width = max(2, cell_size * 0.09)
    move_type = target.get("move_type", "move_capture")
    color_move = _INITIAL_COLOR if target.get("initial_only") else _MOVE_COLOR
    color_capture = _INITIAL_COLOR if target.get("initial_only") else _CAPTURE_COLOR
    is_hopper = target.get("hop_type") is not None
    dash = f' stroke-dasharray="{stroke_width:g} {stroke_width:g}"' if is_hopper else ""
    opacity = "0.95"

    if is_hopper:
        return (
            f'<circle cx="{cx:g}" cy="{cy:g}" r="{radius:g}" fill="none" stroke="{_HOP_COLOR}" '
            f'stroke-width="{stroke_width:g}"{dash} opacity="{opacity}" />'
        )
    if move_type == "move":
        return (
            f'<circle cx="{cx:g}" cy="{cy:g}" r="{radius:g}" fill="none" stroke="{color_move}" '
            f'stroke-width="{stroke_width:g}" opacity="{opacity}" />'
        )
    if move_type == "capture":
        return (
            f'<circle cx="{cx:g}" cy="{cy:g}" r="{radius:g}" fill="none" stroke="{color_capture}" '
            f'stroke-width="{stroke_width:g}" opacity="{opacity}" />'
        )

    top = cy - radius
    bottom = cy + radius
    return (
        f'<path d="M {cx:g},{top:g} A {radius:g},{radius:g} 0 0 0 {cx:g},{bottom:g}" '
        f'stroke="{color_move}" stroke-width="{stroke_width:g}" fill="none" opacity="{opacity}" />'
        f'<path d="M {cx:g},{top:g} A {radius:g},{radius:g} 0 0 1 {cx:g},{bottom:g}" '
        f'stroke="{color_capture}" stroke-width="{stroke_width:g}" fill="none" opacity="{opacity}" />'
    )


def _coordinates(board_width: int, board_height: int, cell_size: int) -> list[str]:
    labels: list[str] = []
    font_size = max(7, cell_size * 0.28)
    for file_ in range(board_width):
        label = chr(ord("a") + file_)
        labels.append(
            f'<text x="{file_ * cell_size + 3:g}" y="{board_height * cell_size - 3:g}" '
            f'font-size="{font_size:g}" font-family="sans-serif" fill="#000000" opacity="0.45">'
            f"{label}</text>"
        )
    for rank in range(board_height):
        label = str(board_height - rank)
        labels.append(
            f'<text x="3" y="{rank * cell_size + font_size:g}" font-size="{font_size:g}" '
            f'font-family="sans-serif" fill="#000000" opacity="0.45">{label}</text>'
        )
    return labels
