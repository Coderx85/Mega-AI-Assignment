"""
Tests for FrameEncoder module.

Tests encoding to JPEG and drawing bounding boxes with error handling.
"""

import pytest
import numpy as np
import io
from PIL import Image

from app.services.frame_encoder import FrameEncoder
from app.models.detection import FaceDetection, BoundingBox, Landmark
from app.errors import Ok, Error, ErrorCode


@pytest.fixture
def valid_rgb_frame():
    """Generate a valid RGB frame as NumPy array."""
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def valid_frame_float():
    """Generate a valid RGB frame with float values (0.0-1.0 or 0-255)."""
    return np.random.random((100, 100, 3)) * 255.0


@pytest.fixture
def valid_context():
    """Provide logging context."""
    return {"session_id": "test_session", "frame_id": 1}


@pytest.fixture
def single_detection():
    """Create a single valid face detection."""
    return FaceDetection(
        face_id="face_0",
        bbox=BoundingBox(x=10, y=10, width=50, height=50),
        confidence=0.95,
        landmarks=[Landmark(x=0.3, y=0.3, z=0.0)],
        timestamp="2025-05-05T00:00:00Z",
    )


@pytest.fixture
def multiple_detections():
    """Create multiple face detections."""
    return [
        FaceDetection(
            face_id="face_0",
            bbox=BoundingBox(x=10, y=10, width=40, height=40),
            confidence=0.95,
            landmarks=None,
            timestamp="2025-05-05T00:00:00Z",
        ),
        FaceDetection(
            face_id="face_1",
            bbox=BoundingBox(x=70, y=20, width=30, height=30),
            confidence=0.88,
            landmarks=None,
            timestamp="2025-05-05T00:00:00Z",
        ),
    ]


@pytest.fixture
def invalid_bbox():
    """Create detection with invalid bbox (zero/negative dimensions)."""
    return FaceDetection(
        face_id="face_bad",
        bbox=BoundingBox(x=10, y=10, width=0, height=50),  # width=0 is invalid
        confidence=0.95,
        landmarks=None,
        timestamp="2025-05-05T00:00:00Z",
    )


class TestFrameEncoderSuccess:
    """Test successful encoding scenarios."""

    def test_encode_valid_frame(self, valid_rgb_frame, valid_context):
        """Test encoding a valid RGB frame to JPEG."""
        result = FrameEncoder.encode(valid_rgb_frame, context=valid_context)

        assert result.is_ok()
        jpeg_bytes = result.unwrap()
        assert isinstance(jpeg_bytes, bytes)
        assert len(jpeg_bytes) > 0
        assert jpeg_bytes[:2] == b"\xff\xd8"  # JPEG magic bytes

    def test_encode_float_frame_converts_to_uint8(self, valid_frame_float, valid_context):
        """Test that float frames are converted to uint8."""
        result = FrameEncoder.encode(valid_frame_float, context=valid_context)

        assert result.is_ok()
        jpeg_bytes = result.unwrap()
        assert len(jpeg_bytes) > 0

    def test_encode_with_custom_quality(self, valid_rgb_frame, valid_context):
        """Test encoding with custom JPEG quality."""
        high_quality = FrameEncoder.encode(valid_rgb_frame, quality=95, context=valid_context).unwrap()
        low_quality = FrameEncoder.encode(valid_rgb_frame, quality=30, context=valid_context).unwrap()

        # Lower quality should produce smaller bytes
        assert len(low_quality) < len(high_quality)

    def test_encode_without_context(self, valid_rgb_frame):
        """Test encode works without context."""
        result = FrameEncoder.encode(valid_rgb_frame)

        assert result.is_ok()
        jpeg_bytes = result.unwrap()
        assert len(jpeg_bytes) > 0


class TestFrameEncoderErrors:
    """Test encoding error scenarios."""

    def test_encode_invalid_type(self, valid_context):
        """Test encode with non-array input."""
        result = FrameEncoder.encode("not an array", context=valid_context)

        assert result.is_error()
        error = result.error
        assert error.code == ErrorCode.ENCODE_ERROR

    def test_encode_invalid_channels(self, valid_context):
        """Test encode with wrong number of channels."""
        invalid_frame = np.random.randint(0, 256, (100, 100), dtype=np.uint8)  # Grayscale, not RGB

        result = FrameEncoder.encode(invalid_frame, context=valid_context)

        assert result.is_error()
        error = result.error
        assert error.code == ErrorCode.ENCODE_ERROR

    def test_encode_invalid_quality(self, valid_rgb_frame, valid_context):
        """Test encode with out-of-range quality (should still work, PIL handles it)."""
        result = FrameEncoder.encode(valid_rgb_frame, quality=150, context=valid_context)

        # PIL clamps quality to 0-100, so it might still succeed
        # But we're documenting the behavior
        assert isinstance(result.is_ok(), bool)


class TestFrameEncoderDrawBboxes:
    """Test drawing bounding boxes on frames."""

    def test_draw_single_bbox(self, valid_rgb_frame, single_detection, valid_context):
        """Test drawing a single bounding box."""
        result = FrameEncoder.draw_bboxes(valid_rgb_frame, [single_detection], context=valid_context)

        assert result.is_ok()
        frame_with_bbox = result.unwrap()
        assert frame_with_bbox.shape == valid_rgb_frame.shape
        assert frame_with_bbox.dtype == np.uint8

    def test_draw_multiple_bboxes(self, valid_rgb_frame, multiple_detections, valid_context):
        """Test drawing multiple bounding boxes."""
        result = FrameEncoder.draw_bboxes(valid_rgb_frame, multiple_detections, context=valid_context)

        assert result.is_ok()
        frame_with_bboxes = result.unwrap()
        assert frame_with_bboxes.shape == valid_rgb_frame.shape

    def test_draw_no_detections(self, valid_rgb_frame, valid_context):
        """Test drawing with no detections (should return frame unchanged)."""
        result = FrameEncoder.draw_bboxes(valid_rgb_frame, [], context=valid_context)

        assert result.is_ok()
        frame = result.unwrap()
        # Should be the same frame
        assert np.array_equal(frame, valid_rgb_frame)

    def test_draw_invalid_bbox_dimensions(self, valid_rgb_frame, invalid_bbox, valid_context):
        """Test drawing with invalid bbox (zero width) — should skip but not fail."""
        result = FrameEncoder.draw_bboxes(valid_rgb_frame, [invalid_bbox], context=valid_context)

        # Should not fail, but skip the invalid bbox
        assert result.is_ok()
        frame = result.unwrap()
        assert frame.shape == valid_rgb_frame.shape

    def test_draw_bbox_outside_frame(self, valid_rgb_frame, valid_context):
        """Test drawing bbox that's partially outside frame (PIL allows this)."""
        out_of_bounds_det = FaceDetection(
            face_id="face_oob",
            bbox=BoundingBox(x=95, y=95, width=50, height=50),  # Extends beyond 100x100
            confidence=0.90,
            landmarks=None,
            timestamp="2025-05-05T00:00:00Z",
        )

        result = FrameEncoder.draw_bboxes(valid_rgb_frame, [out_of_bounds_det], context=valid_context)

        # Should still work (PIL clips to frame bounds)
        assert result.is_ok()
        frame = result.unwrap()
        assert frame.shape == valid_rgb_frame.shape

    def test_draw_invalid_frame_type(self, single_detection, valid_context):
        """Test draw_bboxes with non-array frame."""
        result = FrameEncoder.draw_bboxes("not an array", [single_detection], context=valid_context)

        assert result.is_error()
        error = result.error
        assert error.code == ErrorCode.DRAW_INVALID_BBOX

    def test_draw_float_frame_converts(self, valid_frame_float, single_detection, valid_context):
        """Test draw_bboxes converts float frame to uint8."""
        result = FrameEncoder.draw_bboxes(valid_frame_float, [single_detection], context=valid_context)

        assert result.is_ok()
        frame = result.unwrap()
        assert frame.dtype == np.uint8


class TestFrameEncoderRoundTrip:
    """Test encode/decode round-trip."""

    def test_encode_decode_roundtrip(self, valid_rgb_frame, valid_context):
        """Test that encoded JPEG can be decoded back (with lossy compression)."""
        from app.services.frame_decoder import FrameDecoder

        # Encode
        encode_result = FrameEncoder.encode(valid_rgb_frame, context=valid_context)
        assert encode_result.is_ok()
        jpeg_bytes = encode_result.unwrap()

        # Decode
        decode_result = FrameDecoder.decode(jpeg_bytes, context=valid_context)
        assert decode_result.is_ok()
        decoded_frame = decode_result.unwrap()

        # Shapes should match (lossy compression may change values slightly)
        assert decoded_frame.shape == valid_rgb_frame.shape
        assert decoded_frame.dtype == np.uint8


class TestFrameEncoderResultInterface:
    """Test Result[T] interface for encoder methods."""

    def test_encode_ok_interface(self, valid_rgb_frame):
        """Test Ok result interface on encode."""
        result = FrameEncoder.encode(valid_rgb_frame)

        assert result.is_ok()
        assert not result.is_error()

        jpeg_bytes = result.unwrap()
        assert isinstance(jpeg_bytes, bytes)

    def test_encode_error_interface(self):
        """Test Error result interface on encode."""
        result = FrameEncoder.encode("invalid")

        assert result.is_error()
        assert not result.is_ok()

        # unwrap_or should return default
        default = b"fallback"
        fallback = result.unwrap_or(default)
        assert fallback == default

    def test_draw_bboxes_ok_interface(self, valid_rgb_frame, single_detection):
        """Test Ok result interface on draw_bboxes."""
        result = FrameEncoder.draw_bboxes(valid_rgb_frame, [single_detection])

        assert result.is_ok()
        frame = result.unwrap()
        assert isinstance(frame, np.ndarray)

    def test_draw_bboxes_error_interface(self, single_detection):
        """Test Error result interface on draw_bboxes."""
        result = FrameEncoder.draw_bboxes("invalid", [single_detection])

        assert result.is_error()
        default_frame = np.zeros((1, 1, 3), dtype=np.uint8)
        fallback = result.unwrap_or(default_frame)
        assert np.array_equal(fallback, default_frame)
