import unittest
from python_app.posture_analyzer import analyze_posture


def points(shoulder=(100, 100), hip=(100, 200), knee=(100, 300)):
    result = [[0, 0, 0] for _ in range(17)]
    for i, xy in ((5, shoulder), (11, hip), (13, knee)):
        result[i] = [*xy, 0.9]
    return result


class PostureTests(unittest.TestCase):
    def test_upright_and_horizontal(self):
        self.assertEqual(analyze_posture(points()).status, "UPRIGHT")
        lying = points((100, 100), (200, 110), (300, 120))
        self.assertEqual(analyze_posture(lying).status, "LYING")

    def test_bending_is_not_lying(self):
        self.assertEqual(analyze_posture(points((100, 100), (200, 100),
                                               (200, 200))).status, "UNKNOWN")

    def test_occlusion_degenerate_and_invalid(self):
        for value in (None, [], [[0, 0, 0]] * 17, points((100, 100), (100, 100))):
            self.assertEqual(analyze_posture(value).status, "UNKNOWN")
        value = points()
        value[5][2] = 0.1
        self.assertEqual(analyze_posture(value).status, "UNKNOWN")
        value[5] = [float('nan'), 100, 0.9]
        self.assertEqual(analyze_posture(value).status, "UNKNOWN")

    def test_lying_requires_lower_body(self):
        value = points((100, 100), (200, 100))
        value[13][2] = 0
        self.assertEqual(analyze_posture(value).status, "UNKNOWN")

    def test_other_visible_leg_can_support_lying(self):
        value = points((100, 100), (200, 100))
        value[13][2] = 0
        for index, xy in ((6, (100, 110)), (12, (200, 110)), (14, (300, 110))):
            value[index] = [*xy, .8]
        self.assertEqual(analyze_posture(value).status, "LYING")


if __name__ == "__main__":
    unittest.main()
