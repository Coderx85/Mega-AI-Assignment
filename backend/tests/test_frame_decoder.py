"""
Tests for FrameDecoder module.

Tests both successful decode and error cases (corrupt JPEG, oversized, empty, invalid format).
"""

import pytest
import numpy as np
import io
from PIL import Image

from app.services.frame_decoder import FrameDecoder
from app.errors import Ok, Error, ErrorCode


@pytest.fixture
def valid_frame_bytes():
    """Generate a valid RGB JPEG frame."""
    # Create a simple 100x100 RGB image
    img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def valid_context():
    """Provide logging context."""
    return {"session_id": "test_session", "frame_id": 1}


@pytest.fixture
def grayscale_jpeg_bytes():
    """Generate a grayscale JPEG that needs conversion to RGB."""
    img_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    img = Image.fromarray(img_array, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def corrupt_jpeg_bytes():
    """Generate truncated/corrupt JPEG data."""
    # Valid JPEG header but incomplete data
    valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"  # JPEG header
    # Truncate it to make it invalid
    return valid_jpeg


@pytest.fixture
def oversized_frame_bytes():
    """Generate frame exceeding MAX_FRAME_SIZE."""
    # Create frame larger than MAX_FRAME_SIZE (10 MB)
    return b"X" * (11 * 1024 * 1024)


@pytest.fixture
def empty_frame_bytes():
    """Empty byte string."""
    return b""


class TestFrameDecoderSuccess:
    """Test successful decode scenarios."""

    def test_decode_valid_rgb_frame(self, valid_frame_bytes, valid_context):
        """Test decoding a valid RGB JPEG."""
        result = FrameDecoder.decode(valid_frame_bytes, context=valid_context)

        assert result.is_ok()
        frame = result.unwrap()
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (100, 100, 3)
        assert frame.dtype == np.uint8

    def test_decode_grayscale_converts_to_rgb(self, grayscale_jpeg_bytes, valid_context):
        """Test that grayscale JPEG is converted to RGB."""
        result = FrameDecoder.decode(grayscale_jpeg_bytes, context=valid_context)

        assert result.is_ok()
        frame = result.unwrap()
        assert frame.shape[2] == 3  # RGB

    def test_decode_without_context(self, valid_frame_bytes):
        """Test decode works without context (defaults to empty dict)."""
        result = FrameDecoder.decode(valid_frame_bytes)

        assert result.is_ok()
        frame = result.unwrap()
        assert frame.shape == (100, 100, 3)


class TestFrameDecoderErrors:
    """Test decode error scenarios."""

    def test_decode_empty_frame(self, empty_frame_bytes, valid_context):
        """Test decode with empty frame bytes."""
        result = FrameDecoder.decode(empty_frame_bytes, context=valid_context)

        assert result.is_error()
        error = result.unwrap_or(None)
        assert error is None
        # Verify error details
        actual_error = result.error
        assert actual_error.code == ErrorCode.DECODE_EMPTY_FRAME

    def test_decode_oversized_frame(self, oversized_frame_bytes, valid_context):
        """Test decode with frame exceeding MAX_FRAME_SIZE."""
        result = FrameDecoder.decode(oversized_frame_bytes, context=valid_context)

        assert result.is_error()
        error = result.error
        assert error.code == ErrorCode.DECODE_OVERSIZED_FRAME
        assert "exceeds max" in error.message

    def test_decode_corrupt_jpeg(self, corrupt_jpeg_bytes, valid_context):
        """Test decode with truncated/corrupt JPEG."""
        result = FrameDecoder.decode(corrupt_jpeg_bytes, context=valid_context)

        assert result.is_error()
        error = result.error
        # Could be JPEG_ERROR or INVALID_FORMAT depending on PIL's response
        assert error.code in [ErrorCode.DECODE_JPEG_ERROR, ErrorCode.DECODE_INVALID_FORMAT]

    def test_decode_invalid_data(self, valid_context):
        """Test decode with random bytes (not a valid image)."""
        random_bytes = b"This is not an image at all"

        result = FrameDecoder.decode(random_bytes, context=valid_context)

        assert result.is_error()
        error = result.error
        assert error.code in [ErrorCode.DECODE_INVALID_FORMAT, ErrorCode.DECODE_JPEG_ERROR]

    def test_error_includes_context(self, empty_frame_bytes, valid_context):
        """Test that errors include the provided context."""
        result = FrameDecoder.decode(empty_frame_bytes, context=valid_context)

        assert result.is_error()
        error = result.error
        assert error.context == valid_context

    def test_error_message_is_descriptive(self, oversized_frame_bytes, valid_context):
        """Test that error messages are descriptive."""
        result = FrameDecoder.decode(oversized_frame_bytes, context=valid_context)

        assert result.is_error()
        error = result.error
        assert len(error.message) > 0
        assert str(error)  # Should be human-readable


class TestFrameDecoderResultInterface:
    """Test Result[T] interface methods."""

    def test_ok_result_interface(self, valid_frame_bytes):
        """Test Ok result methods (is_ok, is_error, unwrap, unwrap_or)."""
        result = FrameDecoder.decode(valid_frame_bytes)

        # Test is_ok, is_error
        assert result.is_ok()
        assert not result.is_error()

        # Test unwrap
        frame = result.unwrap()
        assert isinstance(frame, np.ndarray)

        # Test unwrap_or (should return data)
        frame_or = result.unwrap_or(None)
        assert isinstance(frame_or, np.ndarray)

    def test_error_result_interface(self, empty_frame_bytes):
        """Test Error result methods."""
        result = FrameDecoder.decode(empty_frame_bytes)

        # Test is_ok, is_error
        assert not result.is_ok()
        assert result.is_error()

        # Test unwrap_or (should return default)
        default_frame = np.zeros((1, 1, 3), dtype=np.uint8)
        frame_or = result.unwrap_or(default_frame)
        assert np.array_equal(frame_or, default_frame)

        # Test unwrap (should raise)
        with pytest.raises(RuntimeError, match="Called unwrap"):
            result.unwrap()
