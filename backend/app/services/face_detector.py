from datetime import datetime
from typing import List

import numpy as np
from PIL import Image
from mediapipe import Image as MPImage, ImageFormat
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from app.models.detection import FaceDetection, BoundingBox, Landmark

MODEL_PATH = "models/blaze_face_short_range.tflite"

class FaceDetector:
    def __init__(self):
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=0.5,
        )
        self.detector = vision.FaceDetector.create_from_options(options)
        self.frame_count = 0

    def detect(self, frame: np.ndarray) -> List[FaceDetection]:
        self.frame_count += 1
        h, w, _ = frame.shape

        mp_image = MPImage(image_format=ImageFormat.SRGB, data=frame)

        result = self.detector.detect(mp_image)
        detections: List[FaceDetection] = []

        for i, detection in enumerate(result.detections):
            bbox = detection.bounding_box
            xmin = max(0, int(bbox.origin_x))
            ymin = max(0, int(bbox.origin_y))
            width = min(int(bbox.width), w - xmin)
            height = min(int(bbox.height), h - ymin)

            keypoints = detection.keypoints
            landmarks = []
            for kp in keypoints:
                landmarks.append(Landmark(
                    x=kp.x / w,
                    y=kp.y / h,
                    z=0.0,
                ))

            score = detection.categories[0].score if detection.categories else 0.0

            detections.append(FaceDetection(
                face_id=f"face_{self.frame_count}_{i}",
                bbox=BoundingBox(x=xmin, y=ymin, width=width, height=height),
                confidence=score,
                landmarks=landmarks if landmarks else None,
                timestamp=datetime.utcnow().isoformat(),
            ))

        return detections
