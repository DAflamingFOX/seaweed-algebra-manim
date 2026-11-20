from __future__ import annotations

import numpy as np
from manim import *
from seaweed_algebra import Meander

from .meander_arc import MeanderArc, MeanderNode


class MeanderElement(VGroup):
    """Live Manim geometry and topology for a meander."""

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

    def _retire_mobject(self, mob: Mobject) -> None:
        mob.clear_updaters()
        mob.set_opacity(0)
        mob.clear_points()
        self.remove(mob)

    def _merge_collapsed_geometry(self, *, tol: float = 1e-2) -> None:
        """Merge coincident nodes and restore the topology of surviving arcs."""
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
            node.target = None  # type: ignore[assignment]
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

    def _first_component_elements(self) -> tuple[list[MeanderArc], list[MeanderNode]]:
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

    def _retire_component(
        self, removing_arcs: list[MeanderArc], removing_nodes: list[MeanderNode]
    ) -> None:
        removing_arc_set = set(removing_arcs)

        for mob in (*removing_arcs, *removing_nodes):
            self._retire_mobject(mob)
        self.nodes = self.nodes[len(removing_nodes) :]
        self.top_arcs = [arc for arc in self.top_arcs if arc not in removing_arc_set]
        self.btm_arcs = [arc for arc in self.btm_arcs if arc not in removing_arc_set]

        for new_idx, node in enumerate(self.nodes):
            node.idx = new_idx

    def _flip_geometry(self) -> None:
        """Swap arc sides and resume the updaters suspended by the flip."""
        for arc in self.top_arcs + self.btm_arcs:
            arc.is_top = not arc.is_top

        for node in self.nodes:
            node.top_arc, node.btm_arc = node.btm_arc, node.top_arc

        self.top_arcs, self.btm_arcs = self.btm_arcs, self.top_arcs

        for arc in self.top_arcs + self.btm_arcs:
            arc.resume_updating()
            arc.update()
