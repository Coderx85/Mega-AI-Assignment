"""
Tests for FaceDetector module.

Tests face detection with mocked MediaPipe to avoid runtime dependencies.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from app.services.face_detector import FaceDetector
from app.models.detection import FaceDetection, BoundingBox


@pytest.fixture
def valid_frame():
    """Create a valid RGB frame."""
    return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_mediapipe_detector():
    """Create a mock MediaPipe detector."""
    mock_detector = Mock()

    # Mock detection result
    mock_result = Mock()

    # Create mock detections (2 faces)
    mock_detection_1 = Mock()
    mock_detection_1.bounding_box = Mock(origin_x=50, origin_y=60, width=100, height=120)
    mock_detection_1.keypoints = [
        Mock(x=100, y=100),  # Eye 1
        Mock(x=150, y=100),  # Eye 2
        Mock(x=125, y=140),  # Nose
    ]
    mock_detection_1.categories = [Mock(score=0.95)]

    mock_detection_2 = Mock()
    mock_detection_2.bounding_box = Mock(origin_x=200, origin_y=80, width=90, height=110)
    mock_detection_2.keypoints = [
        Mock(x=245, y=110),
        Mock(x=290, y=110),
        Mock(x=267, y=150),
    ]
    mock_detection_2.categories = [Mock(score=0.87)]

    mock_result.detections = [mock_detection_1, mock_detection_2]
    mock_detector.detect = Mock(return_value=mock_result)

    return mock_detector


class TestFaceDetectorInitialization:
    """Test FaceDetector initialization."""

    @patch("app.services.face_detector.vision.FaceDetector")
    @patch("app.services.face_detector.python.BaseOptions")
    @patch("app.services.face_detector.vision.FaceDetectorOptions")
    def test_init_default_model_path(self, mock_options, mock_base_options, mock_fd):
        """Test detector init with default model path."""
        detector = FaceDetector()
        assert detector.model_path == FaceDetector.DEFAULT_MODEL_PATH
        assert detector.confidence_threshold == FaceDetector.DEFAULT_CONFIDENCE_THRESHOLD

    @patch("app.services.face_detector.vision.FaceDetector")
    @patch("app.services.face_detector.python.BaseOptions")
    @patch("app.services.face_detector.vision.FaceDetectorOptions")
    def test_init_custom_model_path(self, mock_options, mock_base_options, mock_fd):
        """Test detector init with custom model path."""
        custom_path = "/custom/model.tflite"
        detector = FaceDetector(model_path=custom_path)
        assert detector.model_path == custom_path

    @patch("app.services.face_detector.vision.FaceDetector")
    @patch("app.services.face_detector.python.BaseOptions")
    @patch("app.services.face_detector.vision.FaceDetectorOptions")
    def test_init_custom_confidence(self, mock_options, mock_base_options, mock_fd):
        """Test detector init with custom confidence threshold."""
        detector = FaceDetector(confidence_threshold=0.7)
        assert detector.confidence_threshold == 0.7

    @patch("app.services.face_detector.python.BaseOptions")
    def test_init_missing_model_file(self, mock_base_options):
        """Test detector init with missing model file."""
        mock_base_options.side_effect = FileNotFoundError("Model file not found")
        with pytest.raises(FileNotFoundError):
            FaceDetector(model_path="nonexistent.tflite")


class TestFaceDetectorDetection:
    """Test face detection."""

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_valid_frame(self, mock_create, mock_mediapipe_detector, valid_frame):
        """Test detection on valid frame returns FaceDetection objects."""
        mock_create.return_value = mock_mediapipe_detector

        detector = FaceDetector()
        detections = detector.detect(valid_frame)

        assert len(detections) == 2
        assert all(isinstance(d, FaceDetection) for d in detections)

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_returns_correct_bbox(self, mock_create, mock_mediapipe_detector, valid_frame):
        """Test that detection returns correct bounding box."""
        mock_create.return_value = mock_mediapipe_detector
        detector = FaceDetector()
        detections = detector.detect(valid_frame)

        # Check first detection bbox
        bbox = detections[0].bbox
        assert isinstance(bbox, BoundingBox)
        assert bbox.x >= 0 and bbox.y >= 0
        assert bbox.width > 0 and bbox.height > 0

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_includes_landmarks(self, mock_create, mock_mediapipe_detector, valid_frame):
        """Test that detection includes landmarks."""
        mock_create.return_value = mock_mediapipe_detector
        detector = FaceDetector()
        detections = detector.detect(valid_frame)

        assert detections[0].landmarks is not None
        assert len(detections[0].landmarks) > 0
        # Landmarks should be normalized (0-1 range)
        for landmark in detections[0].landmarks:
            assert 0 <= landmark.x <= 1
            assert 0 <= landmark.y <= 1

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_includes_confidence(self, mock_create, mock_mediapipe_detector, valid_frame):
        """Test that detection includes confidence score."""
        mock_create.return_value = mock_mediapipe_detector
        detector = FaceDetector()
        detections = detector.detect(valid_frame)

        assert detections[0].confidence == pytest.approx(0.95)
        assert detections[1].confidence == pytest.approx(0.87)

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_generates_unique_face_ids(self, mock_create, mock_mediapipe_detector, valid_frame):
        """Test that each detection gets a unique face ID."""
        mock_create.return_value = mock_mediapipe_detector
        detector = FaceDetector()
        detections = detector.detect(valid_frame)

        face_ids = [d.face_id for d in detections]
        assert len(face_ids) == len(set(face_ids)), "Face IDs should be unique"
        assert all(id.startswith("face_") for id in face_ids)

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_face_ids_no_state(self, mock_create, mock_mediapipe_detector, valid_frame):
        """Test that face IDs are generated without instance state."""
        mock_create.return_value = mock_mediapipe_detector
        detector = FaceDetector()

        detections1 = detector.detect(valid_frame)
        detections2 = detector.detect(valid_frame)

        # Face IDs should be different each time (UUID-based)
        ids1 = {d.face_id for d in detections1}
        ids2 = {d.face_id for d in detections2}
        assert len(ids1 & ids2) == 0, "Face IDs should not collide across calls"

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_empty_detections(self, mock_create, valid_frame):
        """Test detection when no faces are found."""
        mock_detector = Mock()
        mock_result = Mock()
        mock_result.detections = []
        mock_detector.detect.return_value = mock_result
        mock_create.return_value = mock_detector

        detector = FaceDetector()
        detections = detector.detect(valid_frame)

        assert detections == []

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_invalid_frame_type(self, mock_create):
        """Test detection with invalid frame type."""
        mock_create.return_value = Mock()
        detector = FaceDetector()

        with pytest.raises(ValueError, match="Expected np.ndarray"):
            detector.detect("not an array")

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_invalid_frame_shape(self, mock_create):
        """Test detection with invalid frame shape."""
        mock_create.return_value = Mock()
        detector = FaceDetector()

        invalid_frame = np.zeros((480, 640), dtype=np.uint8)  # 2D, not 3D
        with pytest.raises(ValueError, match="Expected RGB frame"):
            detector.detect(invalid_frame)

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_invalid_bbox_skipped(self, mock_create):
        """Test that invalid bboxes (width=0 or height=0) are skipped."""
        mock_detector = Mock()
        mock_result = Mock()

        # Create detection with invalid bbox
        mock_detection = Mock()
        mock_detection.bounding_box = Mock(origin_x=50, origin_y=60, width=0, height=120)  # width=0
        mock_detection.keypoints = []
        mock_detection.categories = [Mock(score=0.95)]

        mock_result.detections = [mock_detection]
        mock_detector.detect.return_value = mock_result
        mock_create.return_value = mock_detector

        detector = FaceDetector()
        valid_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = detector.detect(valid_frame)

        # Should skip invalid detection
        assert len(detections) == 0

    @patch("app.services.face_detector.vision.FaceDetector.create_from_options")
    def test_detect_bbox_clamping(self, mock_create):
        """Test that bboxes are clamped to frame bounds."""
        mock_detector = Mock()
        mock_result = Mock()

        # Create detection with bbox extending beyond frame
        mock_detection = Mock()
        mock_detection.bounding_box = Mock(origin_x=600, origin_y=450, width=100, height=100)
        # Frame is 480x640, so origin is outside
        mock_detection.keypoints = []
        mock_detection.categories = [Mock(score=0.95)]

        mock_result.detections = [mock_detection]
        mock_detector.detect.return_value = mock_result
        mock_create.return_value = mock_detector

        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = detector.detect(frame)

        # Should clamp to frame bounds
        if detections:  # May be skipped if clamped to zero
            bbox = detections[0].bbox
            assert bbox.x + bbox.width <= 640
            assert bbox.y + bbox.height <= 480
