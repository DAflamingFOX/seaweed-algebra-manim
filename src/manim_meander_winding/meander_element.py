from __future__ import annotations

import numpy as np
from manim import *  # pyright: ignore[reportWildcardImportFromLibrary]
from seaweed_algebra import Meander

from .meander_arc import MeanderArc, MeanderNode


class MeanderFlip(Rotate):
    def __init__(self, mobject: MeanderElement, **kwargs):
        kwargs.setdefault("angle", PI)
        kwargs.setdefault("axis", RIGHT)
        kwargs.setdefault("about_point", ORIGIN)
        super().__init__(mobject, **kwargs)
        self.suspend_mobject_updating = False

    def begin(self) -> None:
        mobj: MeanderElement = self.mobject  # type: ignore
        for arc in mobj.top_arcs + mobj.btm_arcs:
            arc.suspend_updating()
        super().begin()


class MeanderElement(VGroup):
    def __init__(self, meander: Meander, **kwargs):
        super().__init__(**kwargs)

        self.meander = meander
        total_nodes = sum(self.meander.top_blocks)

        # Create single source-of-truth nodes (0-indexed internally)
        self.nodes: list[MeanderNode] = [MeanderNode(i) for i in range(total_nodes)]

        # Create top and bottom arcs linked to self.nodes
        self.top_arcs = self._gen_arcs(self.meander.top_blocks, is_top=True)
        self.btm_arcs = self._gen_arcs(self.meander.bottom_blocks, is_top=False)

        # Add arcs first, then nodes on top so dots render cleanly over arc tips
        self.add(*self.btm_arcs, *self.top_arcs, *self.nodes)

    def _gen_arcs(self, blocks: list[int], is_top: bool = True) -> list[MeanderArc]:
        start_offset = 0
        arcs = []

        for block in blocks:
            size = block - 1
            arc_offset = 0

            while size >= 1:
                left = start_offset + arc_offset
                right = start_offset + arc_offset + size

                arcs.append(
                    MeanderArc(
                        left_node=self.nodes[left],
                        right_node=self.nodes[right],
                        is_top=is_top,
                        arc_color=BLUE,
                    )
                )

                size -= 2
                arc_offset += 1
            start_offset += block

        return arcs

    def _retire_mobject(self, mob: Mobject):
        """
        Safely removes a mobject from this VGroup AND hides it completely in case
        Manim's Scene promoted it to a top-level mobject during self.play().
        """
        mob.clear_updaters()
        mob.set_opacity(0)
        mob.clear_points()
        self.remove(mob)

    def cleanup_after_collapse(self, tol: float = 1e-2):
        """
        Call right after self.play(...) of a collapse/rotation move.
        1. Retires all collapsed arcs with coincident endpoints.
        2. Merges overlapping nodes and re-links surviving arcs.
        3. Retires any arcs that collapsed due to node merging.
        4. Resets node tangents to vertical (PI/2) and clears old arc pointers.
        5. Normalizes flipped arcs and re-registers them with their nodes.
        6. Sorts surviving nodes left-to-right and re-indexes 0..N-1.
        """
        # 1. Retire collapsed arcs (endpoints coincident)
        all_arcs = self.top_arcs + self.btm_arcs
        surviving_arcs: list[MeanderArc] = []
        for arc in all_arcs:
            dist = float(
                np.linalg.norm(arc.left_node.get_center() - arc.right_node.get_center())
            )
            if dist < tol:
                self._retire_mobject(arc)
            else:
                surviving_arcs.append(arc)

        # 2. Merge overlapping nodes
        surviving_nodes: list[MeanderNode] = []
        for node in self.nodes:
            merged_target = None
            for target in surviving_nodes:
                if np.linalg.norm(node.get_center() - target.get_center()) < tol:
                    merged_target = target
                    break

            if merged_target is not None:
                for arc in surviving_arcs:
                    arc.replace_node(node, merged_target)
                self._retire_mobject(node)
            else:
                surviving_nodes.append(node)

        # 3. Retire any arcs that collapsed due to node merging
        active_arcs: list[MeanderArc] = []
        for arc in surviving_arcs:
            dist = float(
                np.linalg.norm(arc.left_node.get_center() - arc.right_node.get_center())
            )
            if arc.left_node is arc.right_node or dist < tol:
                self._retire_mobject(arc)
            else:
                active_arcs.append(arc)
        surviving_arcs = active_arcs

        # 4. Reset node tangents to vertical (PI/2) and clear old arc pointers
        for node in surviving_nodes:
            node.reset_tangent()
            node.top_arc = None
            node.btm_arc = None

        # 5. Normalize flipped arcs and re-register with their nodes
        self.top_arcs = []
        self.btm_arcs = []
        for arc in surviving_arcs:
            arc.normalize_orientation()
            arc.left_node.set_arc(arc.is_top, arc)
            arc.right_node.set_arc(arc.is_top, arc)
            if arc.is_top:
                self.top_arcs.append(arc)
            else:
                self.btm_arcs.append(arc)

        # 6. Sort surviving nodes left-to-right and re-index 0..N-1
        surviving_nodes.sort(key=lambda n: n.get_center()[0])
        for new_idx, node in enumerate(surviving_nodes):
            node.idx = new_idx
        self.nodes = surviving_nodes

        # Force one immediate update on surviving arcs so their Bezier handles
        # reflect the normalized orientation and reset tangents seamlessly
        for arc in surviving_arcs:
            arc.update()

    def slide_to_compact(self, start_x: float = 0.0, **kwargs) -> AnimationGroup:
        """
        Slides all surviving nodes horizontally to contiguous integer coordinates
        (start_x, start_x + 1, ...), eliminating any gaps.
        """
        anims = []
        for i, node in enumerate(self.nodes):
            target_x = start_x + i
            if abs(node.get_center()[0] - target_x) > 1e-4:
                anims.append(node.animate.move_to((target_x, 0, 0)))
        return AnimationGroup(*anims, **kwargs)

    def rotation_contraction(self, **kwargs) -> AnimationGroup:
        a1 = self.meander.top_blocks[0]
        b1 = self.meander.bottom_blocks[0]
        num_collapsing = a1 - b1

        return AnimationGroup(
            *(node.move_along_arc(is_top=True) for node in self.nodes[:num_collapsing]),
            *(
                node.move_along_arc(is_top=False)
                for node in self.nodes[num_collapsing:b1]
            ),
            **kwargs,
        )

    def pure_contraction(self, **kwargs) -> AnimationGroup:
        b1 = self.meander.bottom_blocks[0]
        return AnimationGroup(
            *(node.move_along_arc(is_top=True) for node in self.nodes[:b1]),
            **kwargs,
        )

    def get_first_component_elements(
        self,
    ) -> tuple[list[MeanderArc], list[MeanderNode]]:
        """
        Returns (arcs, nodes) belonging to the first a1/b1 component.
        Requires a1 == b1.
        """
        a1 = self.meander.top_blocks[0]
        b1 = self.meander.bottom_blocks[0]
        if a1 != b1:
            raise ValueError(
                f"Component deletion is only valid when a1 == b1, got a1={a1}, b1={b1}"
            )
        removing_nodes = self.nodes[:a1]
        removing_set = set(removing_nodes)
        removing_arcs = [
            arc
            for arc in (self.top_arcs + self.btm_arcs)
            if arc.left_node in removing_set
        ]
        return removing_arcs, removing_nodes

    def component_deletion(self, **kwargs) -> AnimationGroup:
        removing_arcs, removing_nodes = self.get_first_component_elements()
        return AnimationGroup(
            *(FadeOut(mob) for mob in (*removing_arcs, *removing_nodes)),
            **kwargs,
        )

    def cleanup_after_component_deletion(self) -> None:
        """
        Retires the deleted first a1/b1 nodes and arcs, adjusts internal lists,
        and re-indexes surviving nodes.
        """
        removing_arcs, removing_nodes = self.get_first_component_elements()
        removing_arc_set = set(removing_arcs)

        for mob in list(removing_arcs) + list(removing_nodes):
            self._retire_mobject(mob)

        self.nodes = self.nodes[len(removing_nodes) :]
        self.top_arcs = [arc for arc in self.top_arcs if arc not in removing_arc_set]
        self.btm_arcs = [arc for arc in self.btm_arcs if arc not in removing_arc_set]

        for new_idx, node in enumerate(self.nodes):
            node.idx = new_idx

    def flip(self, **kwargs) -> Animation:  # pyright: ignore[reportIncompatibleMethodOverride]
        return MeanderFlip(self, **kwargs)

    def cleanup_after_flip(self) -> None:
        """
        Swaps internal top/bottom arc references, inverts arc.is_top flags,
        swaps node top/btm arc pointers, and resumes arc updaters.
        """
        for arc in self.top_arcs + self.btm_arcs:
            arc.is_top = not arc.is_top

        for node in self.nodes:
            node.top_arc, node.btm_arc = node.btm_arc, node.top_arc

        self.top_arcs, self.btm_arcs = self.btm_arcs, self.top_arcs

        for arc in self.top_arcs + self.btm_arcs:
            arc.resume_updating()
            arc.update()

    def block_elimination(self, **kwargs) -> AnimationGroup:
        num_eliminating = self.meander.bottom_blocks[0]
        return AnimationGroup(
            *(
                node.move_along_arc(is_top=True)
                for node in self.nodes[:num_eliminating]
            ),
            **kwargs,
        )

    def _get_camera_width(self) -> float:
        top_max = max(self.meander.top_blocks, default=1)
        btm_max = max(self.meander.bottom_blocks, default=1)
        return max(top_max, btm_max) * 2.0

    def fit_camera(self, scene: Scene) -> None:
        scene.camera.frame.move_to(self.get_center())  # type: ignore
        scene.camera.frame.width = self._get_camera_width()  # type: ignore

    def fit_camera_animation(
        self,
        scene: Scene,
        target_center: np.ndarray | None = None,
        **kwargs,
    ) -> Animation:
        center = self.get_center() if target_center is None else target_center
        return (
            scene.camera.frame.animate(**kwargs)  # type: ignore
            .move_to(center)
            .set(width=self._get_camera_width())
        )

    def compact_and_fit_camera_animation(
        self,
        scene: Scene,
        start_x: float = 0.0,
        run_time: float = 1.5,
        **kwargs,
    ) -> Animation:
        """
        Simultaneously slides all surviving nodes to contiguous integer positions
        (start_x, start_x + 1, ...) and recenters/zooms the camera in a single smooth motion.
        """
        slide_anim = self.slide_to_compact(start_x=start_x, run_time=run_time, **kwargs)
        target_center = (
            np.array([start_x + (len(self.nodes) - 1) / 2.0, 0.0, 0.0])
            if self.nodes
            else ORIGIN
        )
        cam_anim = self.fit_camera_animation(
            scene, target_center=target_center, run_time=run_time, **kwargs
        )
        if not slide_anim.animations:
            return cam_anim
        return AnimationGroup(slide_anim, cam_anim)

    def _play_collapse_animation(
        self,
        scene: Scene,
        action_anim: AnimationGroup,
        next_meander: Meander,
        run_time: float = 2.0,
        wait_time: float = 0.5,
    ) -> None:
        scene.play(Succession(action_anim, Wait(wait_time)))
        self.cleanup_after_collapse()
        self.meander = next_meander
        if self.nodes:
            scene.play(self.compact_and_fit_camera_animation(scene, run_time=run_time))

    def rotation_contraction_animation(
        self,
        scene: Scene,
        run_time: float = 2.0,
        wait_time: float = 0.5,
    ) -> None:
        self._play_collapse_animation(
            scene,
            self.rotation_contraction(run_time=run_time),
            self.meander._rotation_contraction(),
            run_time=run_time,
            wait_time=wait_time,
        )

    def pure_contraction_animation(
        self,
        scene: Scene,
        run_time: float = 2.0,
        wait_time: float = 0.5,
    ) -> None:
        self._play_collapse_animation(
            scene,
            self.pure_contraction(run_time=run_time),
            self.meander._pure_contraction(),
            run_time=run_time,
            wait_time=wait_time,
        )

    def component_deletion_animation(
        self,
        scene: Scene,
        run_time: float = 2.0,
        wait_time: float = 0.5,
    ) -> None:
        scene.play(
            Succession(self.component_deletion(run_time=run_time), Wait(wait_time))
        )
        self.cleanup_after_component_deletion()
        self.meander, _ = self.meander._component_deletion()
        if self.nodes:
            scene.play(self.compact_and_fit_camera_animation(scene, run_time=1.5))

    def flip_animation(
        self,
        scene: Scene,
        run_time: float = 2.0,
    ) -> None:
        scene.play(self.flip(run_time=run_time))
        self.meander = self.meander._flip()
        self.cleanup_after_flip()
        scene.play(self.fit_camera_animation(scene))

    def block_elimination_animation(
        self,
        scene: Scene,
        run_time: float = 2.0,
        wait_time: float = 0.5,
    ) -> None:
        self._play_collapse_animation(
            scene,
            self.block_elimination(run_time=run_time),
            self.meander._block_elimination(),
            run_time=run_time,
            wait_time=wait_time,
        )

    def wind_step_animation(self, scene: Scene) -> Meander.Move | None:
        """
        Executes the next winding algorithm move on this meander.
        Returns the Meander.Move executed, or None if the meander is empty.
        """
        if self.meander.n == 0:
            return None

        a1, b1 = self.meander.top_blocks[0], self.meander.bottom_blocks[0]
        if a1 == b1:
            self.component_deletion_animation(scene)
            return Meander.Move.COMPONENT_DELETION
        elif a1 < b1:
            self.flip_animation(scene)
            return Meander.Move.FLIP
        elif a1 == 2 * b1:
            self.block_elimination_animation(scene)
            return Meander.Move.BLOCK_ELIMINATION
        elif b1 < a1 < 2 * b1:
            self.rotation_contraction_animation(scene)
            return Meander.Move.ROTATION_CONTRACTION
        elif a1 > 2 * b1:
            self.pure_contraction_animation(scene)
            return Meander.Move.PURE_CONTRACTION
        else:
            raise RuntimeError(f"No valid winding move for a1={a1}, b1={b1}")

    def wind_down_animation(self, scene: Scene) -> list[Meander.Move]:
        """
        Continuously animates winding moves until the meander is completely wound down.
        """
        moves: list[Meander.Move] = []
        while self.meander.n > 0:
            move = self.wind_step_animation(scene)
            if move is None:
                break
            moves.append(move)
        return moves
