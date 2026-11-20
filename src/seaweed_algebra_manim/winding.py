from __future__ import annotations

from collections.abc import Iterator

from manim import *
from seaweed_algebra import Meander

from . import _scene
from .meander_arc import MeanderArc, MeanderNode
from .meander_element import MeanderElement


class _MeanderFlip(Rotate):
    def __init__(self, element: MeanderElement, *, run_time: float) -> None:
        super().__init__(
            element, angle=PI, axis=RIGHT, about_point=ORIGIN, run_time=run_time
        )
        self.element = element
        self.suspend_mobject_updating = False

    def begin(self) -> None:
        # The arc updaters would redraw the curves from their endpoints during
        # the rotation. Freeze them until the geometry swaps top and bottom.
        for arc in (*self.element.top_arcs, *self.element.btm_arcs):
            arc.suspend_updating()
        super().begin()


class MeanderAnimator:
    """Play winding moves on a live meander already added to a moving-camera scene."""

    def __init__(self, element: MeanderElement, scene: MovingCameraScene) -> None:
        self.element = element
        self.scene = scene

    def fit_camera(self, *, width_scale: float = 1.0) -> None:
        """Frame the current meander without animating the camera."""
        _scene.fit_camera(self.element, self.scene, width_scale=width_scale)

    def play_move(
        self, move: Meander.Move, *, run_time: float = 2.0, wait_time: float = 0.5
    ) -> None:
        """Play the requested move if it is the next valid winding move."""
        step = next(self._steps(), None)
        if step is None or move != step[0]:
            expected = "none" if step is None else step[0].name
            raise ValueError(
                f"Cannot play {move.name}; next winding move is {expected}"
            )
        self._play_step(move, run_time=run_time, wait_time=wait_time)

    def wind_step(self) -> Meander.Move | None:
        """Play and return the next winding move, or return None if empty."""
        step = next(self._steps(), None)
        if step is None:
            return None
        move, _ = step
        self._play_step(move)
        return move

    def wind_down(self) -> list[Meander.Move]:
        """Play and return all remaining winding moves in order."""
        moves: list[Meander.Move] = []
        for move, _ in self._steps():
            self._play_step(move)
            moves.append(move)
        return moves

    def _steps(self) -> Iterator[tuple[Meander.Move, int]]:
        """Yield algebra moves and deletion sizes (zero for other moves).

        The algebra iterator advances its own model; playback advances the
        element's live model only after the corresponding geometry changes.
        """
        return self.element.meander._wind_down()

    def _play_step(
        self,
        move: Meander.Move,
        *,
        run_time: float = 2.0,
        wait_time: float = 0.5,
        width_scale: float = 1.0,
    ) -> None:
        match move:
            case Meander.Move.FLIP:
                self._play_flip(run_time, width_scale)
            case Meander.Move.COMPONENT_DELETION:
                self._play_component_deletion(run_time, wait_time, width_scale)
            case Meander.Move.ROTATION_CONTRACTION:
                self._play_rotation_contraction(run_time, wait_time, width_scale)
            case Meander.Move.PURE_CONTRACTION:
                self._play_pure_contraction(run_time, wait_time, width_scale)
            case Meander.Move.BLOCK_ELIMINATION:
                self._play_block_elimination(run_time, wait_time, width_scale)
            case _:
                raise ValueError(f"Unsupported winding move: {move!r}")

    def _play_flip(self, run_time: float, width_scale: float) -> None:
        element, scene = self.element, self.scene
        scene.play(_MeanderFlip(element, run_time=run_time))
        element.meander = element.meander._flip()
        element._flip_geometry()
        _scene.play_camera_fit(element, scene, width_scale=width_scale)

    def _play_component_deletion(
        self, run_time: float, wait_time: float, width_scale: float
    ) -> None:
        element = self.element
        arcs, nodes = element._first_component_elements()
        fades = [FadeOut(mob) for mob in (*arcs, *nodes)]
        # Let the element retire its children after the fade. Manim's default
        # FadeOut cleanup would remove them from the scene and split the group.
        for fade in fades:
            fade.remover = False
        animation = AnimationGroup(*fades, run_time=run_time)
        self._play_then_hold(animation, wait_time)
        self._finish_component_deletion(arcs, nodes)
        if element.nodes:
            _scene.play_compact_and_fit(element, self.scene, width_scale=width_scale)

    def _play_rotation_contraction(
        self, run_time: float, wait_time: float, width_scale: float
    ) -> None:
        element = self.element
        meander = element.meander
        a1, b1 = meander.top_blocks[0], meander.bottom_blocks[0]
        num_collapsing = a1 - b1
        center = (b1 - 1) / 2
        nodes = element.nodes
        # First pull the excess top-block nodes onto their partners.
        animations = [
            node.move_along_arc(is_top=True) for node in nodes[:num_collapsing]
        ]
        # Swing the remaining nodes around the bottom block's midpoint.
        # An odd block has a center node that turns without moving.
        for index in range(num_collapsing, b1):
            node = nodes[index]
            if index == center:
                animations.append(node.rotate_in_place())
            else:
                animations.append(node.move_along_arc(is_top=index < center))
        self._play_collapse(
            AnimationGroup(*animations, run_time=run_time),
            meander._rotation_contraction(),
            wait_time,
            width_scale,
        )

    def _play_pure_contraction(
        self, run_time: float, wait_time: float, width_scale: float
    ) -> None:
        element = self.element
        b1 = element.meander.bottom_blocks[0]
        collapse = AnimationGroup(
            *(node.move_along_arc(is_top=True) for node in element.nodes[:b1]),
            run_time=run_time,
        )
        self._play_collapse(
            collapse, element.meander._pure_contraction(), wait_time, width_scale
        )

    def _play_block_elimination(
        self, run_time: float, wait_time: float, width_scale: float
    ) -> None:
        element = self.element
        b1 = element.meander.bottom_blocks[0]
        collapse = AnimationGroup(
            *(node.move_along_arc(is_top=True) for node in element.nodes[:b1]),
            run_time=run_time,
        )
        self._play_collapse(
            collapse, element.meander._block_elimination(), wait_time, width_scale
        )

    def _play_then_hold(self, animation: Animation, wait_time: float) -> None:
        # Use the existing element as the scene-facing animation target;
        # otherwise Succession adds a new group containing some of its nodes.
        hold = (Wait(wait_time),) if wait_time else ()
        self.scene.play(Succession(animation, *hold, group=self.element))

    def _play_collapse(
        self,
        animation: AnimationGroup,
        next_meander: Meander,
        wait_time: float,
        width_scale: float,
    ) -> None:
        element, scene = self.element, self.scene
        self._play_then_hold(animation, wait_time)
        # Merge endpoints only after they meet. Install the new block sizes
        # before refitting so the camera frames the surviving diagram.
        element._merge_collapsed_geometry()
        element.meander = next_meander
        if element.nodes:
            _scene.play_compact_and_fit(
                element, scene, run_time=animation.run_time, width_scale=width_scale
            )

    def _finish_component_deletion(
        self, arcs: list[MeanderArc], nodes: list[MeanderNode]
    ) -> None:
        """Commit a deletion after either the fade or the homotopy shrink."""
        element = self.element
        element._retire_component(arcs, nodes)
        element.meander, _ = element.meander._component_deletion()
