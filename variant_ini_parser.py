"""Backward-compatible import shim.

Use ``betza_visualizer.variant_ini_parser`` for new code.
"""

from betza_visualizer.variant_ini_parser import VariantIniParser

__all__ = ["VariantIniParser"]
