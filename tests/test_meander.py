from __future__ import annotations

import copy
import unittest

from manim import MovingCameraScene, tempconfig
from seaweed_algebra import Meander

from seaweed_algebra_manim import MeanderElement


class TestMeanderWinding(unittest.TestCase):
    def test_node_deepcopy_prevents_cyclic_explosion(self):
        """Verifies deepcopy of a node disconnects top_arc and btm_arc."""
        m = Meander([8, 5], [5, 6, 2])
        elem = MeanderElement(m)
        node = elem.nodes[0]
        self.assertIsNotNone(node.top_arc)
        self.assertIsNotNone(node.btm_arc)

        copied_node = copy.deepcopy(node)
        self.assertIsNone(copied_node.top_arc)
        self.assertIsNone(copied_node.btm_arc)
        self.assertNotEqual(id(copied_node), id(node))

    def test_slide_to_compact_does_not_recursively_explode(self):
        """Verifies slide_to_compact on 32 nodes creates animation targets instantly."""
        m = Meander([32], [4, 6, 10, 12])
        elem = MeanderElement(m)
        b1 = m.bottom_blocks[0]
        for node in elem.nodes[:b1]:
            arc = node.get_arc(True)
            if arc is not None:
                moving_left_to_right = node is arc.left_node
                path = arc.get_directed_path(left_to_right=moving_left_to_right)
                node.move_to(path.point_from_proportion(1.0))

        elem.cleanup_after_collapse()
        anim_group = elem.slide_to_compact()
        self.assertEqual(len(anim_group.animations), len(elem.nodes))

    def test_wind_down_large_meanders(self):
        """Verifies both problem meanders wind down fully without hanging or leaking."""
        cases = [
            ([4], [3, 1]),
            ([1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]),
            ([32], [4, 6, 10, 12]),
        ]

        with tempconfig({"dry_run": True, "verbosity": "ERROR"}):
            for top_b, btm_b in cases:
                meander_obj = Meander(top_b, btm_b)

                class WindDownScene(MovingCameraScene):
                    def __init__(self, target_meander=meander_obj, **kwargs):
                        super().__init__(**kwargs)
                        self.target_meander = target_meander

                    def construct(self_scene):  # type: ignore
                        elem = MeanderElement(self_scene.target_meander)
                        self_scene.add(elem)
                        elem.fit_camera(self_scene)
                        moves = elem.wind_down_animation(self_scene)
                        self.assertGreater(len(moves), 0)
                        self.assertEqual(len(elem.nodes), 0)
                        self.assertEqual(elem.meander.n, 0)
                        # Only camera frame remains
                        self.assertEqual(len(self_scene.mobjects), 1)

                scene = WindDownScene()
                scene.render()

    def test_rotation_contraction_rotate_in_place_for_odd_block(self):
        """Verifies rotation_contraction rotates center node in place for odd b1 block."""
        m = Meander([4], [3, 1])
        elem = MeanderElement(m)
        rc = elem.rotation_contraction()
        # a1=4, b1=3: num_collapsing=1
        # node 0 moves along top arc (1 animation)
        # node 1 has no bottom arc -> rotates in place (1 animation)
        # node 2 moves along bottom arc (1 animation)
        self.assertEqual(len(rc.animations), 3)


if __name__ == "__main__":
    unittest.main()
