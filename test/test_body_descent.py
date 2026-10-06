import unittest
from python_app.posture_analyzer import BodyDescent


def pose(drop, scale=1, pan=0, confidence=.9):
    points = [[0, 0, 0] for _ in range(17)]
    for indices, y in (((5, 6), 30+drop), ((11, 12), 110+drop*.8), ((15, 16), 230)):
        for index in indices:
            points[index] = [100*scale, (y+pan)*scale, confidence]
    return points


class BodyDescentTests(unittest.TestCase):
    def test_fast_drop_is_time_and_scale_based(self):
        for fps in (10, 15, 30):
            for scale in (.5, 1, 2):
                with self.subTest(fps=fps, scale=scale):
                    detector = BodyDescent()
                    events = [i/fps for i in range(fps)
                              if detector.update(pose(min(60, 120*i/fps), scale), i/fps)[1]]
                    self.assertTrue(events)
                    self.assertLessEqual(events[0], .6)

    def test_static_slow_pan_and_missing_keypoints_do_not_warn(self):
        for kind in ('static', 'slow', 'pan', 'missing'):
            detector = BodyDescent()
            for i in range(60):
                points = pose(i*.2 if kind == 'slow' else 0,
                              pan=i*4 if kind == 'pan' else 0,
                              confidence=.1 if kind == 'missing' else .9)
                self.assertFalse(detector.update(points, i/30)[1], kind)

    def test_missing_frames_cannot_connect_unrelated_poses(self):
        detector = BodyDescent()
        detector.update(pose(0), 0)
        detector.update(None, .1)
        self.assertFalse(detector.update(pose(60), .2)[1])
        self.assertFalse(detector.update(pose(60), .3)[1])

    def test_walking_translation_or_lifting_feet_is_not_body_descent(self):
        for mode in ('approach', 'feet_up'):
            detector = BodyDescent()
            for i in range(30):
                points = pose(i*3 if mode == 'approach' else 0)
                for j in (15, 16):
                    points[j][1] += i*3 if mode == 'approach' else -i*3
                self.assertFalse(detector.update(points, i/30)[1], mode)


if __name__ == '__main__':
    unittest.main()
