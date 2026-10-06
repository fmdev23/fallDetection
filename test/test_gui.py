"""Desktop lifecycle tests: real Tk, fake inference; no sound during tests."""

from pathlib import Path
from tempfile import TemporaryDirectory
import time
import tkinter as tk
import unittest
from unittest.mock import patch

import numpy as np

from python_app.alerts import AlertNotifier
from python_app.fall_fusion import FusionResult
from python_app.gui import FallDetectionApp
from python_app.main import FrameUpdate
from python_app.posture_analyzer import PostureAnalysis
from python_app.sensor_reader import SensorSnapshot


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_popup_is_nonmodal_acknowledgeable_and_deduplicated(self):
        notifier = AlertNotifier(self.root, sound=False)
        try:
            notifier.show("FALL", "Automated notification test")
            popup = notifier.window
            notifier.show("FALL", "same incident")
            self.assertIs(notifier.window, popup)
            notifier.show("EARLY_WARNING", "must not replace confirmed fall")
            self.assertIs(notifier.window, popup)
            self.assertIsNone(self.root.grab_current())
            self.root.update()
            self.assertTrue(popup.winfo_exists())
            notifier.acknowledge()
            self.assertIsNone(notifier.window)
        finally:
            notifier.close()

    def test_sensor_alarm_reaches_tk_before_slow_vision_first_frame(self):
        def source(args, stop, on_sensor=None):
            on_sensor(SensorSnapshot("NORMAL", 1, 120, time.monotonic(),
                                     risk_active=True, risk_event=True, risk_reason="Fast rotation"))
            stop.wait(2)  # Simulated blocked inference; no frame produced.
            return
            yield

        with TemporaryDirectory() as directory, patch('python_app.gui.PROJECT', Path(directory)):
            app = FallDetectionApp(self.root)
            app.notifier.sound_enabled = False
            with patch('python_app.gui.monitor_frames', source):
                started = time.monotonic()
                app.start()
                while time.monotonic()-started < .5 and app.notifier.window is None:
                    self.root.update()
                    time.sleep(.005)
                self.assertEqual(app.notifier.kind, "EARLY_WARNING")
                self.assertIsNone(app.last_update)
                self.assertIn("CẢNH BÁO SỚM", app.banner['text'])
                self.assertLess(time.monotonic()-started, .5)
                app.stop()
                app.worker.join(1)
            self.root.after_cancel(app._poll_id)
            app.notifier.close()

    def test_worker_delivers_alert_even_if_video_frames_are_replaced(self):
        final = FusionResult("FALL_DETECTED", alert=True, reason="Test event", progress=1)
        update = FrameUpdate(np.zeros((480, 640, 3), np.uint8), PostureAnalysis("LYING"),
                             SensorSnapshot("IMPACT", 2.5, 200), final, 1.0)

        def source(args, stop, on_sensor=None):
            yield update
            for _ in range(8):
                yield FrameUpdate(update.frame, update.posture, update.sensor,
                                  FusionResult("FALL_DETECTED", reason="Latched", progress=1), 2.0)

        with TemporaryDirectory() as directory, patch('python_app.gui.PROJECT', Path(directory)):
            app = FallDetectionApp(self.root)
            app.notifier.sound_enabled = False
            with patch('python_app.gui.monitor_frames', source):
                app.start()
                until = time.monotonic()+3
                while time.monotonic() < until and (app.notifier.window is None or app.last_update is None):
                    self.root.update()
                    time.sleep(.02)
                self.assertEqual(app.frame_count, 9)
                self.assertIsNotNone(app.notifier.window)
                self.assertEqual(app.last_update.final.status, "FALL_DETECTED")
                self.assertEqual(float(app.progress['value']), 100)
                self.assertIn('THÔNG BÁO FALL', app.history.get('1.0', 'end'))
                app.stop()
                self.assertIsNone(app.notifier.window)
                self.assertFalse(app.worker.is_alive())
            self.root.after_cancel(app._poll_id)
            app.notifier.close()


if __name__ == '__main__':
    unittest.main()
