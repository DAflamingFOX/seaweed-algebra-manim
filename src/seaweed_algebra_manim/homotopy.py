from __future__ import annotations

from manim import *
from seaweed_algebra import Meander

from ._scene import camera_frame, play_compact_and_fit, play_hold
from .winding import MeanderAnimator


def play_homotopy_extraction(animator: MeanderAnimator) -> list[int]:
    """Collapse each deleted component into its value, then insert it in H."""
    element, scene = animator.element, animator.scene
    values: list[int] = []
    label: VGroup | None = None
    frame = camera_frame(scene)

    def pin_to_viewport(mob: Mobject) -> None:
        scale = frame.width / config.frame_width
        mob.scale_to_fit_width(label_width * scale)
        mob.move_to(frame.get_top() - UP * (0.25 * scale + mob.height / 2))

    for move, deletion in animator._steps():
        # Only deletions contribute a value to H; other moves play as usual.
        if move != Meander.Move.COMPONENT_DELETION:
            animator._play_step(move)
            continue

        values.append(deletion)
        removing_arcs, removing_nodes = element._first_component_elements()
        deleting = VGroup(*removing_arcs, *removing_nodes)
        # Freeze arc redraws while Manim shrinks the component as one group.
        deleting.suspend_updating()
        number = MathTex(str(deletion)).set_z_index(100)
        number.scale(frame.width / config.frame_width)
        number.move_to(deleting.get_center())
        # Detach only the retiring children before Manim adds the shrink group.
        element.remove(*removing_arcs, *removing_nodes)
        scene.play(ShrinkToCenter(deleting), Write(number), run_time=2.0)
        animator._finish_component_deletion(removing_arcs, removing_nodes)
        scene.remove(deleting)

        # Typeset the full expression as a layout guide. Move the number just
        # written in the diagram into the slot before the closing parenthesis.
        tokens = ["H("]
        for index, value in enumerate(values):
            if index:
                tokens.append(",")
            tokens.append(str(value))
        tokens.append(")")
        target = MathTex(*tokens, arg_separator="").set_z_index(100)
        label_width = min(target.width, config.frame_width * 0.9)
        pin_to_viewport(target)
        destination = target[-2]
        animations: list[Animation] = [
            number.animate.match_width(destination).move_to(destination).build()
        ]
        if label is None:
            punctuation = [target[0], target[-1]]
            members = [target[0], number, target[-1]]
        else:
            # Pause viewport pinning while the individual glyphs move.
            label.clear_updaters()
            # Preserve every existing glyph; only its position and size change.
            for old, destination in zip(label[:-1], target[: len(label) - 1]):
                animations.append(
                    old.animate.match_width(destination).move_to(destination).build()
                )
            animations.append(
                label[-1].animate.match_width(target[-1]).move_to(target[-1]).build()
            )
            punctuation = [target[-3]]
            members = [*label[:-1], target[-3], number, label[-1]]
        scene.play(*animations, *(FadeIn(mob) for mob in punctuation), run_time=2.0)
        # Regroup the animated glyphs under one updater before the camera moves.
        scene.remove(number, *punctuation)
        if label is not None:
            scene.remove(label)
        label = VGroup(*members).set_z_index(100)
        scene.add(label)
        label.add_updater(pin_to_viewport)
        play_hold(scene, 0.5)
        if element.nodes:
            play_compact_and_fit(element, scene)

    return values
