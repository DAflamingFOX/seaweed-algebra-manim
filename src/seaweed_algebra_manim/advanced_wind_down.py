from __future__ import annotations

import numpy as np
from manim import *
from seaweed_algebra import Meander

from ._scene import camera_frame, play_hold
from .winding import MeanderAnimator


def play_advanced_wind_down(animator: MeanderAnimator) -> None:
    """Wind down the meander while displaying its signature and homotopy."""
    element, scene = animator.element, animator.scene
    width_scale = 1.4
    animator.fit_camera(width_scale=width_scale)
    frame = camera_frame(scene)
    header_y = 3.15

    def viewport_point(x: float, y: float) -> np.ndarray:
        """Map default-frame coordinates into the current camera frame."""
        return frame.get_center() + np.array([x, y, 0.0]) * (
            frame.width / config.frame_width
        )

    def meander_label_for(meander: Meander) -> MathTex:
        if meander.n:
            top = "|".join(map(str, meander.top_blocks))
            bottom = "|".join(map(str, meander.bottom_blocks))
            tex = rf"M\!\left(\frac{{{top}}}{{{bottom}}}\right)"
        else:
            tex = r"M(\varnothing)"
        label = MathTex(tex, font_size=38, color=BLUE)
        if label.width > 8:
            label.scale_to_fit_width(8)
        label.scale(frame.width / config.frame_width)
        label.move_to(
            viewport_point(-config.frame_width / 2 + 0.5, header_y), aligned_edge=LEFT
        )
        return label

    def append_to_row(
        row: VGroup,
        entry: MathTex,
        y: float,
        source: Mobject,
        *,
        homotopy: bool = False,
    ) -> list[Animation]:
        """Reflow existing glyphs and slide an entry into the growing row."""
        scale = frame.width / config.frame_width
        comma = (
            MathTex(",", font_size=34).scale(scale)
            if homotopy and len(row) > 2
            else None
        )
        members = list(row[:-1] if homotopy else row)
        if comma is not None:
            members.append(comma)
        members.append(entry)
        if homotopy:
            members.append(row[-1])
        # Lay out the full row together for TeX spacing, then use the result
        # as a guide without replacing the glyphs already on screen.
        target = MathTex(
            # VGroup erases the TeX types of the row members.
            *(mob.tex_string for mob in members),  # pyright: ignore[reportArgumentType]
            arg_separator="",
            font_size=34,
        ).scale(scale)
        if target.width > 12.5 * scale:
            target.scale_to_fit_width(12.5 * scale)
        target.move_to(
            viewport_point(-config.frame_width / 2 + 0.5, y), aligned_edge=LEFT
        )

        animations: list[Animation] = []
        for mob, destination in zip(members, target):
            if mob is comma:
                mob.match_width(destination).move_to(destination)
                animations.append(FadeIn(mob))
            elif mob is entry:
                mob.match_width(destination).move_to(destination)
                animations.append(TransformFromCopy(source, mob))
            else:
                animations.append(
                    mob.animate.match_width(destination).move_to(destination).build()
                )
        row.remove(*row.submobjects)
        row.add(*members)
        return animations

    # The invisible frame gives the overlay stable bounds as its text changes.
    hud = VGroup(
        Rectangle(
            width=config.frame_width,
            height=config.frame_height,
            stroke_opacity=0,
            fill_opacity=0,
        )
    )
    meander_label = meander_label_for(element.meander)
    signature_row = VGroup(MathTex(r"\text{Signature: }\;", font_size=34))
    homotopy_row = VGroup(
        *MathTex(r"\text{Homotopy: }\;H(", ")", arg_separator="", font_size=34)
    )
    for row, y in ((signature_row, -2.85), (homotopy_row, -3.5)):
        row.move_to((-config.frame_width / 2 + 0.5, y, 0), aligned_edge=LEFT)
    hud.add(signature_row, homotopy_row)
    hud.scale(frame.width / config.frame_width)
    hud.move_to(frame.get_center())
    hud.add(meander_label)
    hud.set_z_index(100)

    # Use the invisible rectangle, not the changing text bounds, to measure
    # how far to scale and shift the HUD each time the camera moves.
    def pin_to_viewport(mob: Mobject) -> None:
        mob.scale(frame.width / mob[0].width)
        mob.shift(frame.get_center() - mob[0].get_center())

    hud.add_updater(pin_to_viewport)
    scene.add(hud)

    # Use the same algebra step for the caption, the drawing, and the history.
    for move, deletion in animator._steps():
        name = move.name.replace("_", " ").title()
        suffix = rf"\;({deletion})" if deletion else ""
        current_move = MathTex(rf"\text{{{name}}}{suffix}", font_size=38, color=YELLOW)
        current_move.scale(frame.width / config.frame_width)
        current_move.move_to(
            viewport_point(config.frame_width / 2 - 0.5, header_y), aligned_edge=RIGHT
        )
        current_move.set_z_index(100)
        hud.add(current_move)
        scene.play(FadeIn(current_move), run_time=0.5)
        play_hold(scene, 0.4)
        animator._play_step(move, width_scale=width_scale)

        # The caption stayed pinned during the move. Detach it before using it
        # as the source for the history transforms and fading it out.
        hud.remove(current_move)
        scene.add(current_move)
        symbol = rf"C({deletion})" if deletion else rf"\mathrm{{{move.value}}}"
        entry = MathTex(symbol, font_size=34, color=YELLOW).set_z_index(100)
        animations = append_to_row(signature_row, entry, -2.85, current_move)
        if deletion:
            value = MathTex(str(deletion), font_size=34, color=YELLOW).set_z_index(100)
            animations.extend(
                append_to_row(homotopy_row, value, -3.5, current_move, homotopy=True)
            )
        animations.append(FadeOut(current_move))
        scene.play(*animations, run_time=1.3)

        next_label = meander_label_for(element.meander).set_z_index(100)
        scene.play(ReplacementTransform(meander_label, next_label), run_time=0.9)
        meander_label = next_label
        play_hold(scene, 0.5)

    complete = MathTex(r"\text{Complete}", font_size=30)
    complete.scale(frame.width / config.frame_width)
    complete.move_to(
        viewport_point(config.frame_width / 2 - 0.5, header_y), aligned_edge=RIGHT
    )
    complete.set_z_index(100)
    hud.add(complete)
    scene.play(FadeIn(complete), run_time=0.5)
    play_hold(scene, 2)
