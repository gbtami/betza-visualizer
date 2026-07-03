"""Backward-compatible import shim.

Use ``betza_visualizer.betza_parser`` for new code.
"""

from betza_visualizer.betza_parser import BetzaParser

__all__ = ["BetzaParser"]
