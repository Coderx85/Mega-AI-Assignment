"""
Face detection service using MediaPipe.

Detects faces in frames and returns FaceDetection objects with ROI and landmarks.
"""

import os
from datetime import datetime, UTC
from typing import List

import numpy as np
import structlog
from mediapipe import Image as MPImage, ImageFormat
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from app.models.detection import FaceDetection, BoundingBox, Landmark
from app.services.face_id_generator import FaceIDGenerator

logger = structlog.get_logger(__name__)


class FaceDetector:
    """Detects faces in frames using MediaPipe."""

    DEFAULT_MODEL_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "models",
        "blaze_face_short_range.tflite",
    )
    DEFAULT_CONFIDENCE_THRESHOLD = 0.5

    def __init__(
        self,
        model_path: str = None,
        confidence_threshold: float = None,
    ):
        """
        Initialize face detector with MediaPipe model.

        Args:
            model_path: Path to TFLite model file. Defaults to DEFAULT_MODEL_PATH.
            confidence_threshold: Minimum detection confidence (0.0-1.0). Defaults to DEFAULT_CONFIDENCE_THRESHOLD.

        Raises:
            FileNotFoundError: If model_path does not exist.
            RuntimeError: If MediaPipe initialization fails.
        """
        self.model_path = model_path or self.DEFAULT_MODEL_PATH
        self.confidence_threshold = confidence_threshold or self.DEFAULT_CONFIDENCE_THRESHOLD

        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.FaceDetectorOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                min_detection_confidence=self.confidence_threshold,
            )
            self.detector = vision.FaceDetector.create_from_options(options)
            logger.info("detector_initialized", model_path=self.model_path, confidence=self.confidence_threshold)
        except FileNotFoundError as e:
            logger.error("model_file_not_found", model_path=self.model_path, error=str(e))
            raise
        except Exception as e:
            logger.error("detector_initialization_failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to initialize FaceDetector: {str(e)}") from e

    def detect(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces in a frame.

        Args:
            frame: RGB NumPy array (H, W, 3) with uint8 values

        Returns:
            List[FaceDetection]: Detected faces (may be empty)

        Raises:
            ValueError: If frame shape is invalid
            RuntimeError: If detection fails
        """
        try:
            # Validate frame
            if not isinstance(frame, np.ndarray):
                raise ValueError(f"Expected np.ndarray, got {type(frame)}")

            if len(frame.shape) != 3 or frame.shape[2] != 3:
                raise ValueError(f"Expected RGB frame (H, W, 3), got shape {frame.shape}")

            h, w, _ = frame.shape

            # Convert to MediaPipe Image
            mp_image = MPImage(image_format=ImageFormat.SRGB, data=frame)

            # Run detection
            result = self.detector.detect(mp_image)

            detections: List[FaceDetection] = []

            for i, detection in enumerate(result.detections):
                try:
                    # Extract and clamp bounding box
                    bbox = detection.bounding_box
                    xmin = max(0, int(bbox.origin_x))
                    ymin = max(0, int(bbox.origin_y))
                    width = min(int(bbox.width), w - xmin)
                    height = min(int(bbox.height), h - ymin)

                    # Validate bbox
                    if width <= 0 or height <= 0:
                        logger.warning("invalid_bbox_from_detector", index=i, width=width, height=height)
                        continue

                    # Extract landmarks (normalized to 0-1 range)
                    keypoints = detection.keypoints
                    landmarks = []
                    for kp in keypoints:
                        landmarks.append(Landmark(
                            x=kp.x / w,
                            y=kp.y / h,
                            z=0.0,
                        ))

                    # Extract confidence score
                    score = detection.categories[0].score if detection.categories else 0.0

                    # Generate unique face ID (UUID-based, no instance state)
                    face_id = FaceIDGenerator.generate()

                    detections.append(FaceDetection(
                        face_id=face_id,
                        bbox=BoundingBox(x=xmin, y=ymin, width=width, height=height),
                        confidence=score,
                        landmarks=landmarks if landmarks else None,
                        timestamp=datetime.now(UTC).isoformat(),
                    ))

                except Exception as e:
                    logger.warning("detection_extraction_failed", index=i, error=str(e), exc_info=True)
                    continue

            logger.debug("detection_complete", count=len(detections))
            return detections

        except ValueError as e:
            logger.error("detection_invalid_frame", error=str(e))
            raise

        except Exception as e:
            logger.error("detection_failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Face detection failed: {str(e)}") from e
