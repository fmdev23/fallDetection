"""Simple geometry on COCO keypoints; LYING is a posture, never a fall."""

from dataclasses import dataclass
import math
from collections import deque


class BodyDescent:
    """Shoulders and hips descend together over planted feet, across frames.

    Also catches near-vertical collapse, which a torso-angle rule misses.
    Quick sitting/squatting may warn; this is not a confirmed fall label.
    """
    def __init__(self):
        self.samples = deque()
        self.last_risk = None
        self.latched = False

    def update(self, keypoints, now):
        groups = []
        if keypoints is not None and len(keypoints) == 17:
            for indices in ((5, 6), (11, 12), (15, 16)):
                points = [keypoints[i] for i in indices if len(keypoints[i]) >= 3
                          and all(math.isfinite(v) for v in keypoints[i][:3])
                          and keypoints[i][2] >= .5]
                if points:
                    groups.append(tuple(sum(p[d] for p in points)/len(points) for d in (0, 1)))
        candidate = False
        if len(groups) != 3:
            self.samples.clear()
        else:
            if self.samples and now-self.samples[-1][0] > .3:
                self.samples.clear()
            self.samples.append((now, *groups))
            while self.samples and now-self.samples[0][0] > .6:
                self.samples.popleft()
            shoulder, hip, foot = groups
            for t, old_shoulder, old_hip, old_foot in self.samples:
                dt = now-t
                height = old_foot[1]-old_shoulder[1]
                if .15 <= dt <= .6 and height >= 25:
                    # Measure descent relative to feet: walking toward the
                    # camera moves the whole body downward in image coordinates.
                    foot_dy = foot[1]-old_foot[1]
                    drop = min(shoulder[1]-old_shoulder[1],
                               shoulder[1]-old_shoulder[1]-foot_dy)/height
                    hip_drop = min(hip[1]-old_hip[1], hip[1]-old_hip[1]-foot_dy)/height
                    feet_shift = math.dist(foot, old_foot)/height
                    if drop >= .15 and hip_drop >= .1 and drop/dt >= .4 and feet_shift < .15:
                        candidate = True
                        break
        event = False
        # Candidate already spans >=150 ms and checks shoulders, hips and
        # planted feet. Requiring a future frame loses rapid occlusions.
        if candidate and len(self.samples) >= 3:
            event = not self.latched
            self.latched = True
            self.last_risk = now
        active = self.last_risk is not None and now-self.last_risk < 1
        if not active:
            self.latched = False
        return active, event


class PoseMotion:
    """Rapid increase in visible torso tilt: a warning, never proof of a fall."""
    def __init__(self):
        self.samples = deque()
        self.last_risk = None
        self.latched = False

    def update(self, posture, now):
        angle = posture.torso_angle
        if angle is None:
            self.samples.clear()
        else:
            if self.samples and now-self.samples[-1][0] > .5:
                self.samples.clear()
            self.samples.append((now, angle))
            while self.samples and now-self.samples[0][0] > .4:
                self.samples.popleft()
        event = False
        if len(self.samples) >= 3:
            duration = now-self.samples[0][0]
            change = angle-self.samples[0][1]
            if duration >= .1 and change >= 18 and change/duration >= 90:
                event = not self.latched
                self.latched = True
                self.last_risk = now
        active = self.last_risk is not None and now-self.last_risk < 1
        if not active:
            self.latched = False
        return active, event


@dataclass(frozen=True)
class PostureAnalysis:
    status: str
    torso_angle: float | None = None
    reason: str = "missing keypoints"


def angle_from_vertical(first, second):
    dx, dy = second[0] - first[0], second[1] - first[1]
    if math.hypot(dx, dy) < 5:
        return None
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def analyze_posture(keypoints, confidence=0.5):
    """17 [x,y,confidence] points. Require a visible torso on one body side.

    Upright: torso <=30 degrees from vertical. Lying: torso >=60 degrees
    AND visible thigh/leg >=50 degrees, reducing confusion with bending.
    Missing/ambiguous evidence yields UNKNOWN. Intended for one person.
    """
    unknown = PostureAnalysis("UNKNOWN")
    if keypoints is None or len(keypoints) != 17:
        return unknown

    def visible(index):
        point = keypoints[index]
        return (len(point) >= 3 and all(math.isfinite(v) for v in point[:3])
                and point[2] >= confidence and (point[0] != 0 or point[1] != 0))

    sides = [(5, 11, 13, 15), (6, 12, 14, 16)]
    sides = [side for side in sides if visible(side[0]) and visible(side[1])]
    if not sides:
        return unknown
    # Pick the torso with the strongest weaker point, avoiding mixed body sides.
    side = max(sides, key=lambda s: min(keypoints[s[0]][2], keypoints[s[1]][2]))
    shoulder, hip, _, _ = side
    torso = angle_from_vertical(keypoints[shoulder], keypoints[hip])
    if torso is None:
        return unknown
    if torso <= 30:
        return PostureAnalysis("UPRIGHT", torso, "vertical torso")
    if torso >= 60:
        # A clear torso on one side must not hide useful leg evidence on the
        # other side. Still check shoulder/hip/leg from the same side together.
        for shoulder, hip, knee, ankle in sides:
            side_torso = angle_from_vertical(keypoints[shoulder], keypoints[hip])
            if side_torso is None or side_torso < 60:
                continue
            lower = ankle if visible(ankle) else knee if visible(knee) else None
            if lower is not None:
                leg = angle_from_vertical(keypoints[hip], keypoints[lower])
                if leg is not None and leg >= 50:
                    return PostureAnalysis("LYING", torso, "horizontal torso and leg")
    return PostureAnalysis("UNKNOWN", torso, "ambiguous pose or hidden legs")


def posture_from_result(result):
    """Never combine different people's poses with the one available IMU."""
    if len(result.boxes) == 0:
        return PostureAnalysis("UNKNOWN", reason="person not detected or occluded")
    if len(result.boxes) != 1:
        return PostureAnalysis("UNKNOWN", reason="need exactly one person")
    if result.keypoints is None:
        return PostureAnalysis("UNKNOWN", reason="missing keypoints")
    return analyze_posture(result.keypoints.data[0].cpu().tolist())
