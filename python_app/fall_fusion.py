"""Temporal fusion with brief-occlusion tolerance and explicit alert reasons."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class FusionResult:
    status: str
    alert: bool = False
    warning: bool = False
    reason: str = ""
    lying_seconds: float = 0.0
    progress: float = 0.0
    impact_age: float | None = None


class FallFusion:
    def __init__(self, impact_window=5.0, lying_hold=1.3, recovery_hold=2.0,
                 max_frame_gap=1.5, occlusion_grace=0.6, lying_warning=1.3):
        for value in (impact_window, lying_hold, recovery_hold, max_frame_gap,
                      occlusion_grace, lying_warning):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Fusion durations must be finite and positive")
        self.impact_window, self.lying_hold = impact_window, lying_hold
        self.recovery_hold, self.max_frame_gap = recovery_hold, max_frame_gap
        self.occlusion_grace, self.lying_warning = occlusion_grace, lying_warning
        self.status = "NORMAL"
        self.last_time = self.last_impact = self.recovery_since = None
        self.previous_posture = None
        self.warning_latched = False
        self._reset_lying()

    def _reset_lying(self):
        self.lying_since = self.last_lying = None
        self.lying_seconds = self.confirm_seconds = 0.0
        self.matched_impact = False

    def update(self, posture, sensor_status, now, impact_at=None):
        if not math.isfinite(now) or (self.last_time is not None and now < self.last_time):
            raise ValueError("Fusion timestamps must be finite and nondecreasing")
        dt = 0 if self.last_time is None else now - self.last_time
        if dt > self.max_frame_gap:
            self._reset_lying()
            self.recovery_since = None
            self.previous_posture = None
            dt = 0
        self.last_time = now
        connected = sensor_status in ("NORMAL", "IMPACT")
        if not connected:
            self.last_impact = None
            self.matched_impact = False
            self.confirm_seconds = 0
        elif sensor_status == "IMPACT":
            # An ongoing high reading is current evidence, not an expired edge.
            self.last_impact = now
        elif (impact_at is not None and math.isfinite(impact_at)
              and 0 <= now-impact_at <= self.impact_window):
            if self.last_impact is None or impact_at > self.last_impact:
                self.last_impact = impact_at

        if posture == "LYING":
            if self.last_lying is not None and self.previous_posture != "LYING":
                if now-self.last_lying > self.occlusion_grace:
                    self._reset_lying()
            if self.lying_since is None:
                self.lying_since = now
            # Only observed LYING-to-LYING intervals count. UNKNOWN pauses time.
            observed_dt = dt if self.previous_posture == "LYING" else 0
            self.lying_seconds += observed_dt
            if self.matched_impact:
                self.confirm_seconds += observed_dt
            self.last_lying = now
            recent = self.last_impact is not None and now-self.last_impact <= self.impact_window
            if (connected and recent and not self.matched_impact
                    and now-self.lying_since <= self.impact_window):
                self.matched_impact = True
                self.confirm_seconds = 0
        elif posture == "UNKNOWN":
            if self.last_lying is not None and now-self.last_lying > self.occlusion_grace:
                self._reset_lying()
        else:
            self._reset_lying()

        if posture == "UPRIGHT" and sensor_status in ("NORMAL", "VIDEO_ONLY"):
            if self.recovery_since is None:
                self.recovery_since = now
            if now-self.recovery_since >= self.recovery_hold:
                self.status = "NORMAL"
                self.warning_latched = False
        else:
            self.recovery_since = None

        alert = warning = False
        if self.status == "FALL_DETECTED":
            reason = "Đã cảnh báo. Đứng ổn định và sensor bình thường để tự phục hồi."
        elif (posture == "LYING" and connected and self.matched_impact
              and self.confirm_seconds + 1e-9 >= self.lying_hold):
            self.status = "FALL_DETECTED"
            alert = True
            reason = "Có impact phù hợp và tư thế nằm được xác nhận đủ thời gian."
        else:
            if posture != "UPRIGHT" or sensor_status not in ("NORMAL", "VIDEO_ONLY"):
                self.status = "SUSPICIOUS"
            if posture == "UNKNOWN":
                reason = "Camera chưa thấy rõ tư thế; đếm giờ tạm dừng, không tự xác nhận té."
            elif posture == "LYING" and self.matched_impact:
                reason = f"Đã có impact; đang xác nhận nằm {self.confirm_seconds:.1f}/{self.lying_hold:.1f} giây."
            elif sensor_status == "VIDEO_ONLY":
                reason = ("Video độc lập: đang quan sát tư thế nằm; cảnh báo sau thời gian đã đặt."
                          if posture == "LYING" else "Video độc lập: tư thế thẳng, không ghép sensor hiện tại vào clip.")
            elif posture == "LYING" and not connected:
                reason = "Đang nằm nhưng sensor mất kết nối; chưa đủ hai nguồn để xác nhận té."
            elif posture == "LYING":
                reason = "Đang nằm nhưng chưa có impact phù hợp; sẽ nhắc kiểm tra nếu nằm kéo dài."
            elif sensor_status == "IMPACT":
                reason = "Sensor có impact; đang chờ tư thế nằm."
            elif not connected:
                reason = "Không nhận được dữ liệu sensor mới. Kiểm tra Wokwi."
            elif self.status == "SUSPICIOUS":
                reason = "Đang chờ đứng và sensor bình thường ổn định để phục hồi."
            else:
                reason = "Tư thế thẳng và sensor bình thường."
            if sensor_status == 'SENSOR_UNASSIGNED':
                reason = "Có nhiều mục tiêu: vẫn cảnh báo bằng hình ảnh, chưa gán IMU cho một người cụ thể."
            if (posture == "LYING" and self.lying_seconds + 1e-9 >= self.lying_warning
                    and not self.warning_latched):
                warning = self.warning_latched = True
                reason = "Nằm kéo dài: cần kiểm tra người trong hình; chưa xác nhận té ngã."

        self.previous_posture = posture
        age = None if self.last_impact is None else max(0, now-self.last_impact)
        return FusionResult(self.status, alert, warning, reason, self.lying_seconds,
                            min(1, max(self.confirm_seconds/self.lying_hold,
                                       self.lying_seconds/self.lying_warning)), age)
