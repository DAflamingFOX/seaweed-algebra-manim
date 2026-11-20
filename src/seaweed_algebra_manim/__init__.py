"""Manim animations for seaweed algebra meander winding moves."""

from .advanced_wind_down import play_advanced_wind_down
from .block_annotations import show_blocks
from .homotopy import play_homotopy_extraction
from .meander_arc import MeanderArc, MeanderNode
from .meander_element import MeanderElement
from .winding import MeanderAnimator

__version__ = "0.1.0"

__all__ = [
    "MeanderAnimator",
    "MeanderArc",
    "MeanderElement",
    "MeanderNode",
    "play_advanced_wind_down",
    "play_homotopy_extraction",
    "show_blocks",
]
