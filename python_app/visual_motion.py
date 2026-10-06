"""Short optical-flow bridge across lost pose, not a fall classifier."""
import cv2
import numpy as np


class VisualMotion:
    def __init__(self):
        self.previous = None
        self.previous_time = None
        self.box = None
        self.anchor_time = None
        self.since = None
        self.last_risk = None
        self.latched = False
        self.flow_estimator = None

    def update(self, frame, boxes, now, shared=None, allow_warning=True):
        shared = {} if shared is None else shared
        height, width = frame.shape[:2]
        scale = min(1, 320 / width)
        if 'gray' not in shared:
            shared['gray'] = cv2.cvtColor(cv2.resize(frame, (round(width*scale), round(height*scale))),
                                          cv2.COLOR_BGR2GRAY)
        gray = shared['gray']
        dt = 0 if self.previous_time is None else now-self.previous_time
        valid_pair = (self.previous is not None and self.previous.shape == gray.shape
                      and .005 <= dt <= .2)
        scene_cut = valid_pair and np.mean(cv2.absdiff(self.previous, gray)) > 40
        # Multiple people cannot be reliably associated with the previous target.
        if len(boxes) > 1 or scene_cut or (self.previous is not None and not valid_pair):
            self.box = self.anchor_time = None
            self.since = None
        candidate = False
        if (valid_pair and not scene_cut and self.box is not None
                and now-self.anchor_time <= 1.2):
            x1, y1, x2, y2 = self.box
            body_height, body_width = y2-y1, x2-x1
            # Do not warn merely because a person walks through an image edge.
            margin = max(4, gray.shape[0]*.08)
            inside = (x1 > 3 and y1 > 3 and x2 < gray.shape[1]-3
                      and y2 < gray.shape[0]-margin and body_height >= 25)
            if len(boxes) == 1:
                current = np.asarray(boxes[0][:4])*scale
                inside = inside and (current[0] > 3 and current[1] > 3
                                     and current[2] < gray.shape[1]-3
                                     and current[3] < gray.shape[0]-margin)
            if inside:
                if 'flow' not in shared:
                    # Inverse-search flow handles larger inter-frame movement
                    # at webcam FPS; share one calculation across all people.
                    if self.flow_estimator is None:
                        self.flow_estimator = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
                    shared['flow'] = self.flow_estimator.calc(self.previous, gray, None)
                flow = shared['flow']
                # Compensate common camera translation using pixels outside ROI.
                left, right = max(0, int(x1-body_width*.5)), min(gray.shape[1], int(x2+body_width*.5))
                top, bottom = max(0, int(y1-body_height*.25)), min(gray.shape[0], int(y2+body_height*.6))
                background = np.ones(gray.shape, bool)
                background[top:bottom, left:right] = False
                if background.sum() >= gray.size*.25:
                    flow = flow - np.median(flow[background], axis=0)
                    downward = flow[top:bottom, left:right, 1]
                    # Require a region of coherent rapid downward motion,
                    # not a single noisy point; normalize by last body height.
                    candidate = (downward.size > 0 and
                                 np.mean(downward > max(.8, body_height*dt*.7)) >= .05)
        event = False
        if candidate and allow_warning:
            if self.since is None:
                # Flow measures the entire previous->current interval. Counting
                # only its endpoint unfairly requires extra frames at low FPS.
                self.since = now-dt
            if now-self.since >= .06-1e-9:
                event = not self.latched
                self.latched = True
                self.last_risk = now
        else:
            self.since = None
        active = self.last_risk is not None and now-self.last_risk < 1
        if not active:
            self.latched = False
        if len(boxes) == 1:
            box = boxes[0]
            if len(box) >= 5 and box[4] >= .5:
                self.box = np.asarray(box[:4], dtype=float)*scale
                self.anchor_time = now
        self.previous, self.previous_time = gray, now
        return active, event
