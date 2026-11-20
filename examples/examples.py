from typing import ClassVar

from manim import *
from seaweed_algebra import Meander

from seaweed_algebra_manim import (
    MeanderAnimator,
    MeanderElement,
    play_advanced_wind_down,
    play_homotopy_extraction,
    show_blocks,
)


class BaseMeanderScene(MovingCameraScene):
    top_blocks: tuple[int, ...] = ()
    bottom_blocks: tuple[int, ...] = ()
    move: ClassVar[Meander.Move | None] = None
    opening_hold: float = 1.0

    def construct(self):
        m = Meander(list(self.top_blocks), list(self.bottom_blocks))
        m_elem = MeanderElement(m)
        animator = MeanderAnimator(m_elem, self)
        self.add(m_elem)

        if self.opening_hold:
            animator.fit_camera()
            self.wait(self.opening_hold)

        self.play_meander(animator)

    def play_meander(self, animator: MeanderAnimator) -> None:
        if self.move is None:
            animator.wind_down()
        else:
            animator.play_move(self.move)


# Full Wind-Down
class FullWindDown(BaseMeanderScene):
    top_blocks = (17, 3)
    bottom_blocks = (10, 4, 6)


class AdvancedWindDown(BaseMeanderScene):
    top_blocks = (17, 3)
    bottom_blocks = (10, 4, 6)
    opening_hold = 0.0  # The animation sets up its own camera and overlay.

    def play_meander(self, animator: MeanderAnimator) -> None:
        play_advanced_wind_down(animator)


# Homotopy Extraction
class HomotopyExtraction(BaseMeanderScene):
    top_blocks = (7, 10, 6, 5)
    bottom_blocks = (7, 3, 4, 3, 1, 2, 2, 2, 1, 3)

    def play_meander(self, animator: MeanderAnimator) -> None:
        play_homotopy_extraction(animator)


# Rotation Contraction
class RotationContractionReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (5, 6, 2)
    move = Meander.Move.ROTATION_CONTRACTION


class RotationContractionSecondary(BaseMeanderScene):
    top_blocks = (17, 3)
    bottom_blocks = (10, 4, 6)
    move = Meander.Move.ROTATION_CONTRACTION


# Pure Contraction
class PureContractionReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (3, 6, 4)
    move = Meander.Move.PURE_CONTRACTION


class PureContractionSecondary(BaseMeanderScene):
    top_blocks = (10, 3)
    bottom_blocks = (3, 4, 6)
    move = Meander.Move.PURE_CONTRACTION


# Component Deletion
class ComponentDeletionReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (8, 2, 3)
    move = Meander.Move.COMPONENT_DELETION


class ComponentDeletionSecondary(BaseMeanderScene):
    top_blocks = (4, 3, 3)
    bottom_blocks = (4, 6)
    move = Meander.Move.COMPONENT_DELETION


# Flip
class FlipReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (10, 3)
    move = Meander.Move.FLIP


class FlipSecondary(BaseMeanderScene):
    top_blocks = (3, 3)
    bottom_blocks = (6,)
    move = Meander.Move.FLIP


# Block Elimination
class BlockEliminationReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (4, 6, 3)
    move = Meander.Move.BLOCK_ELIMINATION


class BlockEliminationSecondary(BaseMeanderScene):
    top_blocks = (6,)
    bottom_blocks = (3, 3)
    move = Meander.Move.BLOCK_ELIMINATION


class ShowBlocks(MovingCameraScene):
    """Identify every block in the reference meander, including singletons."""

    def construct(self):
        m_elem = MeanderElement(Meander([17, 3], [10, 4, 6]))
        self.add(m_elem)
        MeanderAnimator(m_elem, self).fit_camera()
        self.wait(0.5)
        show_blocks(m_elem, self)
        self.wait(0.5)
