from manim import MovingCameraScene
from seaweed_algebra import Meander

from seaweed_algebra_manim import MeanderElement


class BaseMeanderScene(MovingCameraScene):
    top_blocks: tuple[int, ...] = ()
    bottom_blocks: tuple[int, ...] = ()
    action: str = ""

    def construct(self):
        m = Meander(list(self.top_blocks), list(self.bottom_blocks))
        m_elem = MeanderElement(m)
        self.add(m_elem)

        m_elem.fit_camera(self)
        self.wait(1)

        # Abuse python a bit, this calls m_elem.action_animation, where "action"
        # is the start of the name of the function to call, postfixed with "_animation".
        getattr(m_elem, f"{self.action}_animation")(self)


# Full Wind-Down
class FullWindDown(BaseMeanderScene):
    top_blocks = (17, 3)
    bottom_blocks = (10, 4, 6)
    action = "wind_down"


# Homotopy Extraction
class HomotopyExtraction(BaseMeanderScene):
    top_blocks = (7, 10, 6, 5)
    bottom_blocks = (7, 3, 4, 3, 1, 2, 2, 2, 1, 3)
    action = "homotopy_extraction"


# Rotation Contraction
class RotationContractionReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (5, 6, 2)
    action = "rotation_contraction"


class RotationContractionSecondary(BaseMeanderScene):
    top_blocks = (17, 3)
    bottom_blocks = (10, 4, 6)
    action = "rotation_contraction"


# Pure Contraction
class PureContractionReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (3, 6, 4)
    action = "pure_contraction"


class PureContractionSecondary(BaseMeanderScene):
    top_blocks = (10, 3)
    bottom_blocks = (3, 4, 6)
    action = "pure_contraction"


# Component Deletion
class ComponentDeletionReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (8, 2, 3)
    action = "component_deletion"


class ComponentDeletionSecondary(BaseMeanderScene):
    top_blocks = (4, 3, 3)
    bottom_blocks = (4, 6)
    action = "component_deletion"


# Flip
class FlipReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (10, 3)
    action = "flip"


class FlipSecondary(BaseMeanderScene):
    top_blocks = (3, 3)
    bottom_blocks = (6,)
    action = "flip"


# Block Elimination
class BlockEliminationReference(BaseMeanderScene):
    top_blocks = (8, 5)
    bottom_blocks = (4, 6, 3)
    action = "block_elimination"


class BlockEliminationSecondary(BaseMeanderScene):
    top_blocks = (6,)
    bottom_blocks = (3, 3)
    action = "block_elimination"


class ShowBlocks(MovingCameraScene):
    """Identify every block in the reference meander, including singletons."""

    def construct(self):
        m_elem = MeanderElement(Meander([17, 3], [10, 4, 6]))
        self.add(m_elem)
        m_elem.fit_camera(self)
        self.wait(0.5)
        m_elem.show_blocks_animation(self)
        self.wait(0.5)
