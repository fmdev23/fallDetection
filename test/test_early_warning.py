"""Timing/negative regressions, not measured prediction accuracy."""
import unittest
from python_app.sensor_analyzer import MotionRisk
from python_app.posture_analyzer import PoseMotion, PostureAnalysis
from python_app.fall_fusion import FallFusion


class EarlyWarningTests(unittest.TestCase):
    def test_normal_noise_and_slow_change_do_not_warn(self):
        risk = MotionRisk()
        for i in range(100):
            self.assertFalse(risk.update((0, 0, 1+.02*(i % 2), 2, 0, 0), i*.02)[1])

    def test_fast_gyro_warns_without_lying_and_rearms(self):
        risk = MotionRisk()
        events = [risk.update((0, 0, 1, 120, 0, 0), i*.02)[1] for i in range(25)]
        self.assertEqual(events.index(True), 4)
        self.assertEqual(sum(events), 1)
        for i in range(25, 90):
            risk.update((0, 0, 1, 0, 0, 0), i*.02)
        self.assertTrue(risk.update((0, 0, 2.5, 0, 0, 0), 1.82, impact=True)[1])

    def test_short_impact_and_acceleration_change_warn_immediately(self):
        risk = MotionRisk()
        self.assertTrue(risk.update((0, 0, 2.8, 0, 0, 0), 0, impact=True)[1])
        risk = MotionRisk()
        risk.update((0, 0, 1, 0, 0, 0), 0)
        self.assertTrue(risk.update((0, 0, 1.4, 0, 0, 0), .04)[1])

    def test_moderate_single_spike_and_old_sample_do_not_warn(self):
        risk = MotionRisk()
        self.assertFalse(risk.update((0, 0, 1, 110, 0, 0), 0)[1])
        self.assertFalse(risk.update((0, 0, 1, 0, 0, 0), .02)[1])
        self.assertFalse(risk.update((0, 0, 1.7, 0, 0, 0), 3)[1])

    def test_low_acceleration_persistence(self):
        risk = MotionRisk()
        events = [risk.update((0, 0, .3, 0, 0, 0), i*.02)[1] for i in range(10)]
        self.assertEqual(sum(events), 1)

    def test_lying_warns_at_1_3_seconds_without_imu(self):
        fusion = FallFusion()
        events = [fusion.update('LYING', 'SENSOR_DISCONNECTED', i*.1) for i in range(20)]
        self.assertFalse(any(e.warning for e in events[:13]))
        self.assertTrue(events[13].warning)
        self.assertEqual(sum(e.warning for e in events), 1)
        self.assertFalse(any(e.alert for e in events))

    def test_fast_tilt_warns_before_lying_slow_tilt_and_occlusion_do_not(self):
        motion = PoseMotion()
        events = [motion.update(PostureAnalysis('UPRIGHT', angle), i*.1)[1]
                  for i, angle in enumerate((3, 13, 26))]
        self.assertTrue(events[-1])
        motion = PoseMotion()
        for i in range(20):
            self.assertFalse(motion.update(PostureAnalysis('UPRIGHT', i), i*.1)[1])
        motion.update(PostureAnalysis('UNKNOWN'), 2)
        self.assertFalse(motion.update(PostureAnalysis('LYING', 80), 2.1)[1])


if __name__ == '__main__':
    unittest.main()
