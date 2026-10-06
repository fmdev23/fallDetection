"""Known image motion, not real-world fall accuracy."""
import unittest
import numpy as np
import cv2
from python_app.visual_motion import VisualMotion


class VisualMotionTests(unittest.TestCase):
    def sequence(self, kind, stride=1, allow_warning=True):
        rng = np.random.default_rng(2026)
        background = rng.integers(20, 80, (240, 320, 3), dtype=np.uint8)
        person = rng.integers(90, 240, (85, 45, 3), dtype=np.uint8)
        events = []
        tracker = VisualMotion()
        for i in range(18):
            if i % stride:
                continue
            frame = background.copy()
            base = 145 if kind == 'edge' else 45
            y = base + (max(0, i-3)*4 if kind in ('drop', 'edge') else 0)
            size = max(0, min(85, 240-y))
            frame[y:y+size, 140:185] = person[:size]
            if kind == 'pan':
                frame = cv2.warpAffine(frame, np.float32([[1, 0, 0], [0, 1, i*4]]),
                                      (320, 240), borderMode=cv2.BORDER_REFLECT)
            if kind == 'cut' and i >= 4:
                frame[:] = 220
            boxes = [[140, base, 185, base+85, .9]] if i < 4 else []
            events.append(tracker.update(frame, boxes, i/30, allow_warning=allow_warning)[1])
        return events

    def test_downward_motion_warns_despite_missing_detector_boxes(self):
        events = self.sequence('drop')
        self.assertEqual(sum(events), 1)
        self.assertTrue(any(events[4:12]))

    def test_static_lost_detection_camera_pan_and_scene_cut_do_not_warn(self):
        for kind in ('static', 'pan', 'cut', 'edge'):
            with self.subTest(kind=kind):
                self.assertFalse(any(self.sequence(kind)))

    def test_no_person_anchor_never_triggers(self):
        rng = np.random.default_rng(2)
        tracker = VisualMotion()
        for i in range(10):
            image = rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)
            self.assertEqual(tracker.update(image, [], i/30), (False, False))

    def test_larger_frame_gaps_and_disabled_bridge(self):
        for stride in (2, 3):
            self.assertTrue(any(self.sequence('drop', stride=stride)))
            self.assertFalse(any(self.sequence('pan', stride=stride)))
        self.assertFalse(any(self.sequence('drop', allow_warning=False)))


if __name__ == '__main__':
    unittest.main()
