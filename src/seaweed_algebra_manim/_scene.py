from __future__ import annotations

from typing import cast

from manim import *

from .meander_element import MeanderElement


def camera_frame(scene: MovingCameraScene) -> Mobject:
    return cast(MovingCamera, scene.camera).frame


def _camera_width(element: MeanderElement, width_scale: float) -> float:
    meander = element.meander
    max_block = max(
        max(meander.top_blocks, default=1), max(meander.bottom_blocks, default=1)
    )
    return width_scale * max(2 * max_block, meander.n + 2)


def fit_camera(
    element: MeanderElement, scene: MovingCameraScene, *, width_scale: float = 1.0
) -> None:
    frame = camera_frame(scene)
    frame.move_to(element.get_center())
    frame.width = _camera_width(element, width_scale)


def play_camera_fit(
    element: MeanderElement, scene: MovingCameraScene, *, width_scale: float = 1.0
) -> None:
    scene.play(
        camera_frame(scene)
        .animate.move_to(element.get_center())
        .set(width=_camera_width(element, width_scale))
    )


def play_compact_and_fit(
    element: MeanderElement,
    scene: MovingCameraScene,
    *,
    run_time: float = 1.5,
    width_scale: float = 1.0,
) -> None:
    nodes = element.nodes
    slides = [
        node.animate.move_to((index, 0, 0)).build()
        for index, node in enumerate(nodes)
        if abs(node.get_x() - index) > 1e-4
    ]
    center = ((len(nodes) - 1) / 2, 0.0, 0.0) if nodes else ORIGIN
    camera = (
        camera_frame(scene)
        .animate.move_to(center)
        .set(width=_camera_width(element, width_scale))
        .build()
    )
    # Play the children directly: adding a temporary animation group to the
    # scene would pull its nodes out of the meander's scene hierarchy.
    scene.play(*slides, camera, run_time=run_time)


def play_hold(scene: Scene, duration: float) -> None:
    """Wait without leaving Manim's temporary, point-free target in the scene."""
    wait = Wait(duration)
    scene.play(wait)
    scene.remove(wait.mobject)
