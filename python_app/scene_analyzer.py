"""Shared per-person evidence for webcam and video; conservative IMU binding."""
from dataclasses import dataclass, replace
import math

if __package__:
    from .fall_fusion import FallFusion
    from .posture_analyzer import analyze_posture, PostureAnalysis, PoseMotion, BodyDescent
    from .visual_motion import VisualMotion
else:
    from fall_fusion import FallFusion
    from posture_analyzer import analyze_posture, PostureAnalysis, PoseMotion, BodyDescent
    from visual_motion import VisualMotion


@dataclass
class Track:
    number: int
    box: list
    seen: float
    fusion: FallFusion
    pose_motion: PoseMotion
    visual: VisualMotion
    descent: BodyDescent


def overlap(a, b):
    intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    area_a, area_b = (a[2]-a[0])*(a[3]-a[1]), (b[2]-b[0])*(b[3]-b[1])
    return intersection / max(1, area_a+area_b-intersection)


class SceneAnalyzer:
    def __init__(self, args):
        self.args = args
        self.tracks = {}
        self.next_number = 1
        self.empty_fusion = self._fusion()

    def _fusion(self):
        return FallFusion(self.args.impact_window, self.args.lying_hold,
                          self.args.recovery_hold, occlusion_grace=self.args.occlusion_grace,
                          lying_warning=self.args.lying_warning)

    def update(self, frame, boxes, keypoints, now, sensor=None):
        self.tracks = {n: t for n, t in self.tracks.items()
                       if now-t.seen <= 1.5 or t.fusion.status == 'FALL_DETECTED'}
        candidates = []
        for n, track in self.tracks.items():
            for i, box in enumerate(boxes):
                iou = overlap(track.box, box)
                distance = math.hypot((box[0]+box[2]-track.box[0]-track.box[2])/2,
                                      (box[1]+box[3]-track.box[1]-track.box[3])/2)
                height = max(1, track.box[3]-track.box[1])
                ratio = (box[3]-box[1])/height
                if iou >= .1 and distance < height*.6 and .3 <= ratio <= 3:
                    candidates.append((iou-distance/height*.1, n, i))
        matched, used = {}, set()
        for _, n, i in sorted(candidates, reverse=True):
            if n not in matched and i not in used:
                matched[n] = i
                used.add(i)
        for i, box in enumerate(boxes):
            if i not in used:
                n = self.next_number
                self.next_number += 1
                self.tracks[n] = Track(n, box, now, self._fusion(), PoseMotion(), VisualMotion(), BodyDescent())
                matched[n] = i
        results, labels, reasons = [], [], []
        shared = {}
        for n, track in self.tracks.items():
            i = matched.get(n)
            if i is None:
                pose = PostureAnalysis('UNKNOWN', reason='person not detected or occluded')
                visible_boxes = []
            else:
                track.box, track.seen = boxes[i], now
                pose = analyze_posture(keypoints[i]) if i < len(keypoints) else PostureAnalysis('UNKNOWN')
                visible_boxes = [boxes[i]]
                labels.append((n, boxes[i], pose.status))
            # Cropping at an image edge can swing the estimated torso abruptly.
            # Keep posture display, but do not interpret that swing as motion.
            motion_pose = pose
            if i is not None:
                x1, y1, x2, y2 = boxes[i][:4]
                h, w = frame.shape[:2]
                if x1 <= 3 or y1 <= 3 or x2 >= w-3 or y2 >= h*.92:
                    motion_pose = PostureAnalysis('UNKNOWN')
            active, event = track.pose_motion.update(motion_pose, now)
            flow_active, flow_event = track.visual.update(frame, visible_boxes, now, shared,
                                                         allow_warning=pose.status == 'UNKNOWN')
            descent_active, descent_event = track.descent.update(keypoints[i] if i is not None and i < len(keypoints) else None, now)
            active, event = active or flow_active or descent_active, event or flow_event or descent_event
            reason = (f"Người #{n}: thân và hông hạ nhanh trong khi chân ít dịch chuyển; cần kiểm tra."
                      if descent_active else f"Người #{n}: vùng vừa theo dõi chuyển động xuống nhanh; có thể ngã/che khuất, cần kiểm tra."
                      if flow_active else f"Người #{n}: thân nghiêng nhanh; cần kiểm tra.")
            if event:
                reasons.append(reason)
            # Never attach one IMU's impact to one of several possible people.
            sensor_status = ('VIDEO_ONLY' if sensor is None else sensor.status
                             if len(self.tracks) == 1 else 'SENSOR_UNASSIGNED')
            impact_at = sensor.impact_at if sensor is not None and len(self.tracks) == 1 else None
            final = track.fusion.update(pose.status, sensor_status, now, impact_at)
            final = replace(final, reason=f"Người #{n}: {final.reason}")
            rank = (final.status == 'FALL_DETECTED', final.warning, event, active, final.lying_seconds,
                    i is not None, (track.box[2]-track.box[0])*(track.box[3]-track.box[1]))
            results.append((rank, pose, final, active, event, reason))
        if not results:
            pose = PostureAnalysis('UNKNOWN', reason='person not detected or occluded')
            status = 'VIDEO_ONLY' if sensor is None else sensor.status
            return pose, self.empty_fusion.update('UNKNOWN', status, now), False, False, '', labels
        _, pose, final, active, _, reason = max(results, key=lambda item: item[0])
        warning_reasons = [r[2].reason for r in results if r[2].warning]
        if warning_reasons:
            final = replace(final, warning=True, reason=' | '.join(warning_reasons))
        return pose, final, any(r[3] for r in results), bool(reasons), ' | '.join(reasons) or reason, labels
