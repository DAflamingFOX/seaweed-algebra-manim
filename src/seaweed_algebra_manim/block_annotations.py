from __future__ import annotations

import numpy as np
from manim import *

from ._scene import play_hold
from .meander_element import MeanderElement


def show_blocks(
    element: MeanderElement,
    scene: Scene,
    run_time: float = 1.0,
    wait_time: float = 1.0,
    *,
    show_annotations: bool = True,
) -> None:
    """Show block bars, optionally with braces and labels, then fade them out."""
    bars = VGroup()
    annotations = VGroup()
    nodes = element.nodes
    spacing = (
        (nodes[-1].get_x() - nodes[0].get_x()) / (len(nodes) - 1)
        if len(nodes) > 1
        else 1.0
    )

    for blocks, arcs, direction, symbol in (
        (element.meander.top_blocks, element.top_arcs, UP, "a"),
        (element.meander.bottom_blocks, element.btm_arcs, DOWN, "b"),
    ):
        if not blocks:
            continue
        if show_annotations:
            heights = [node.get_critical_point(direction)[1] for node in nodes]
            # Symmetric meander arcs reach their visible apex halfway along.
            heights.extend(arc.point_from_proportion(0.5)[1] for arc in arcs)
            edge_y = float(max(heights) if direction[1] > 0 else min(heights))
            offset = 0
            for index, size in enumerate(blocks, start=1):
                first = nodes[offset].get_center()
                last = nodes[offset + size - 1].get_center()
                left = np.array([first[0] - 0.4 * spacing, edge_y, 0.0])
                right = np.array([last[0] + 0.4 * spacing, edge_y, 0.0])
                brace = Brace(
                    Line(left, right),
                    direction=direction,
                    buff=0.15 * spacing,
                    color=WHITE,
                )
                label = MathTex(
                    rf"{symbol}_{{{index}}}={size}", color=WHITE, font_size=56
                )
                label.scale(spacing)
                # Keep labels inside disjoint block spans, even for singletons.
                if label.width > right[0] - left[0]:
                    label.scale_to_fit_width(right[0] - left[0])
                label.next_to(brace, direction, buff=0.12 * spacing)
                annotations.add(brace, label)
                offset += size

        offset = 0
        for size in blocks:
            offset += size
            if offset < len(nodes):
                boundary = (
                    nodes[offset - 1].get_center() + nodes[offset].get_center()
                ) / 2
                bars.add(
                    Line(
                        boundary + direction * 0.18 * spacing,
                        boundary + direction * 1.05 * spacing,
                        color=WHITE,
                        stroke_width=4,
                    )
                )

    scene.play(FadeIn(bars), run_time=run_time)
    if show_annotations:
        scene.play(FadeIn(annotations), run_time=run_time)
    play_hold(scene, wait_time)
    scene.play(FadeOut(VGroup(bars, annotations)), run_time=run_time)
