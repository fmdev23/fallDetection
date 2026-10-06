import unittest
from python_app.fall_fusion import FallFusion


class FusionTests(unittest.TestCase):
    def test_single_source_never_confirms(self):
        for posture, sensor in (("UPRIGHT", "IMPACT"), ("LYING", "NORMAL")):
            fusion = FallFusion()
            for step in range(20):
                self.assertEqual(fusion.update(posture, sensor, step * .5).status,
                                 "SUSPICIOUS")

    def test_fall_latches_once_and_recovers(self):
        fusion = FallFusion()
        self.assertEqual(fusion.update("UPRIGHT", "NORMAL", 0).status, "NORMAL")
        self.assertEqual(fusion.update("UPRIGHT", "IMPACT", .5).status, "SUSPICIOUS")
        alerts = []
        for step in range(2, 12):
            alerts.append(fusion.update("LYING", "NORMAL", step * .5).alert)
        self.assertEqual(sum(alerts), 1)
        self.assertEqual(fusion.status, "FALL_DETECTED")
        self.assertEqual(fusion.update("UNKNOWN", "SENSOR_DISCONNECTED", 6).status,
                         "FALL_DETECTED")
        for step in range(13, 18):
            fusion.update("UPRIGHT", "NORMAL", step * .5)
        self.assertEqual(fusion.status, "NORMAL")

    def test_expired_impact_and_long_existing_lying(self):
        fusion = FallFusion()
        for step in range(12):
            fusion.update("UPRIGHT", "IMPACT" if step == 0 else "NORMAL", step * .5)
        for step in range(12, 20):
            self.assertNotEqual(fusion.update("LYING", "NORMAL", step * .5).status,
                                "FALL_DETECTED")
        fusion = FallFusion()
        for step in range(20):
            status = "IMPACT" if step == 12 else "NORMAL"
            self.assertNotEqual(fusion.update("LYING", status, step * .5).status,
                                "FALL_DETECTED")

    def test_disconnect_occlusion_and_frame_gap_cancel_hold(self):
        for bad_posture, bad_sensor, timestamp in (
                ("UNKNOWN", "NORMAL", 1), ("LYING", "SENSOR_DISCONNECTED", 1),
                ("LYING", "NORMAL", 5)):
            fusion = FallFusion()
            fusion.update("LYING", "IMPACT", 0)
            fusion.update("LYING", "NORMAL", .5)
            result = fusion.update(bad_posture, bad_sensor, timestamp)
            self.assertNotEqual(result.status, "FALL_DETECTED")
            self.assertFalse(fusion.update("LYING", "NORMAL", timestamp + .5).alert)

    def test_short_impact_between_frames_is_preserved(self):
        fusion = FallFusion()
        fusion.update("UPRIGHT", "NORMAL", 0)
        fusion.update("LYING", "NORMAL", .5, impact_at=.25)
        results = [fusion.update("LYING", "NORMAL", t, impact_at=.25)
                   for t in (1, 1.5, 2, 2.5)]
        self.assertEqual(sum(r.alert for r in results), 1)

    def test_ongoing_impact_before_walking_to_camera_is_not_expired(self):
        fusion = FallFusion()
        for step in range(40):
            fusion.update("UPRIGHT", "IMPACT", step * .5)
        events = [fusion.update("LYING", "IMPACT", 20 + step * .25)
                  for step in range(12)]
        self.assertEqual(sum(r.alert for r in events), 1)

    def test_brief_missing_keypoint_pauses_instead_of_erasing_progress(self):
        fusion = FallFusion()
        events = []
        for step in range(35):
            posture = "UNKNOWN" if step in (4, 9, 14, 19) else "LYING"
            result = fusion.update(posture, "IMPACT", step * .1)
            self.assertFalse(result.alert and posture == "UNKNOWN")
            events.append(result)
        self.assertEqual(sum(r.alert for r in events), 1)

    def test_long_occlusion_and_disconnect_never_confirm(self):
        fusion = FallFusion()
        fusion.update("LYING", "IMPACT", 0)
        fusion.update("LYING", "NORMAL", .5)
        for i in range(1, 10):
            self.assertFalse(fusion.update("UNKNOWN", "NORMAL", .5+i*.2).alert)
        self.assertEqual(fusion.lying_seconds, 0)
        for i in range(30):
            self.assertFalse(fusion.update("LYING", "SENSOR_DISCONNECTED", 3+i*.2).alert)

    def test_prolonged_lying_warns_once_without_claiming_fall(self):
        fusion = FallFusion()
        events = [fusion.update("LYING", "NORMAL", i*.5) for i in range(30)]
        self.assertEqual(sum(r.warning for r in events), 1)
        self.assertFalse(any(r.alert for r in events))
        self.assertEqual(events[-1].status, "SUSPICIOUS")


if __name__ == "__main__":
    unittest.main()
