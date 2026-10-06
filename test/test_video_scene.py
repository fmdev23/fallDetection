import unittest
import numpy as np
from python_app.scene_analyzer import SceneAnalyzer
from python_app.main import build_parser
from python_app.sensor_reader import SensorSnapshot


def points(lying=False):
    result = [[0, 0, 0] for _ in range(17)]
    for index, distance in ((5, 30), (11, 75), (13, 120)):
        result[index] = [distance, 60, .9] if lying else [60, distance, .9]
    return result


class VideoSceneTests(unittest.TestCase):
    def test_webcam_and_video_share_pose_warning_timing(self):
        timings = []
        for clock_origin, sensor in ((0, None), (1000, SensorSnapshot())):
            scene = SceneAnalyzer(build_parser().parse_args([]))
            frame = np.zeros((240, 320, 3), np.uint8)
            warnings = []
            for i in range(20):
                _, final, _, _, _, _ = scene.update(frame, [[20, 40, 150, 100, .9]],
                                                   [points(True)], clock_origin+i*.1, sensor)
                if final.warning:
                    warnings.append(i)
            timings.append(warnings)
        self.assertEqual(timings, [[13], [13]])

    def test_one_imu_never_confirms_fall_for_multiple_people(self):
        scene = SceneAnalyzer(build_parser().parse_args([]))
        frame = np.zeros((240, 320, 3), np.uint8)
        for i in range(25):
            _, final, _, _, _, _ = scene.update(frame, [[20, 40, 130, 100, .9], [170, 40, 290, 100, .9]],
                                               [points(True), points(True)], i*.1,
                                               SensorSnapshot('IMPACT', 3, 200))
            self.assertFalse(final.alert)
            self.assertNotEqual(final.status, 'FALL_DETECTED')

    def test_person_order_changes_do_not_mix_lying_timers(self):
        scene = SceneAnalyzer(build_parser().parse_args([]))
        image = np.zeros((240, 320, 3), np.uint8)
        upright, lying = [20, 20, 90, 150, .9], [170, 70, 290, 120, .9]
        warnings = []
        for i in range(20):
            boxes, keypoints = [upright, lying], [points(), points(True)]
            if i % 2:
                boxes.reverse();keypoints.reverse()
            _, final, _, _, _, _ = scene.update(image, boxes, keypoints, i*.1)
            if final.warning:
                warnings.append((i, final.reason))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0][0], 13)
        self.assertIn('#2', warnings[0][1])

    def test_new_person_cannot_inherit_previous_lying_hold(self):
        scene = SceneAnalyzer(build_parser().parse_args([]))
        image = np.zeros((240, 320, 3), np.uint8)
        for i in range(10):
            scene.update(image, [[20, 40, 100, 100, .9]], [points(True)], i*.1)
        for i in range(10, 20):
            _, final, _, _, _, _ = scene.update(image, [[200, 40, 290, 100, .9]], [points(True)], i*.1)
            self.assertFalse(final.warning)


if __name__ == '__main__':
    unittest.main()
