from manim import *  # pyright: ignore[reportWildcardImportFromLibrary]
from seaweed_algebra import Meander

from seaweed_algebra_manim import MeanderElement


class MeanderWindDown(MovingCameraScene):
    """
    Demonstrates winding down a meander step-by-step until empty.
    """

    def construct(self):
        m = Meander([6], [3, 3])
        m_elem = MeanderElement(m)
        self.add(m_elem)

        m_elem.fit_camera(self)
        self.wait(1)

        m_elem.wind_down_animation(self)
        self.wait(1)


class SingleMoveExample(MovingCameraScene):
    """
    Demonstrates a single winding move (e.g. block elimination).
    """

    def construct(self):
        m = Meander([8, 5], [4, 6, 3])
        m_elem = MeanderElement(m)
        self.add(m_elem)

        m_elem.fit_camera(self)
        self.wait(1)

        m_elem.block_elimination_animation(self)
        self.wait(1)
