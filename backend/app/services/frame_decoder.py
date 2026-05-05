"""
Frame decoder module: converts JPEG bytes to NumPy RGB arrays.

Returns Result[NDArray] with proper error codes and logging.
"""

import io
from typing import Union

import numpy as np
import structlog
from PIL import Image

from app.errors import Ok, Error, Result, FrameProcessingError, ErrorCode

logger = structlog.get_logger(__name__)


class FrameDecoder:
    """Decodes JPEG frame bytes to NumPy RGB arrays."""

    # Maximum frame size: 10 MB
    MAX_FRAME_SIZE = 10 * 1024 * 1024

    @staticmethod
    def decode(
        frame_bytes: bytes,
        context: dict = None,
    ) -> Result[np.ndarray]:
        """
        Decode JPEG frame bytes to RGB NumPy array.

        Args:
            frame_bytes: JPEG-encoded frame bytes
            context: Optional context dict (session_id, frame_id, etc.) for logging

        Returns:
            Ok(NDArray) on success, Error(FrameProcessingError) on failure
        """
        context = context or {}

        # Validate frame size
        if len(frame_bytes) == 0:
            error = FrameProcessingError(
                code=ErrorCode.DECODE_EMPTY_FRAME,
                message="Frame bytes are empty",
                context=context,
            )
            logger.warning("frame_decode_empty", error=str(error), **context)
            return Error(error)

        if len(frame_bytes) > FrameDecoder.MAX_FRAME_SIZE:
            error = FrameProcessingError(
                code=ErrorCode.DECODE_OVERSIZED_FRAME,
                message=f"Frame size {len(frame_bytes)} exceeds max {FrameDecoder.MAX_FRAME_SIZE}",
                context=context,
            )
            logger.warning("frame_decode_oversized", error=str(error), **context)
            return Error(error)

        try:
            # Open and decode JPEG
            img = Image.open(io.BytesIO(frame_bytes))

            # Validate format (should be JPEG but also accept other formats)
            # PIL will raise if it's not a valid image format

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            frame_array = np.array(img)
            logger.debug("frame_decoded", shape=frame_array.shape, dtype=str(frame_array.dtype), **context)
            return Ok(frame_array)

        except Image.UnidentifiedImageError:
            error = FrameProcessingError(
                code=ErrorCode.DECODE_INVALID_FORMAT,
                message="Image format not recognized by PIL",
                context=context,
            )
            logger.warning("frame_decode_invalid_format", error=str(error), **context)
            return Error(error)

        except OSError as e:
            # OSError covers: cannot identify image file, etc.
            error = FrameProcessingError(
                code=ErrorCode.DECODE_JPEG_ERROR,
                message=f"JPEG decode failed: {str(e)}",
                context=context,
            )
            logger.warning("frame_decode_jpeg_error", error=str(error), **context)
            return Error(error)

        except Exception as e:
            # Catch-all for unexpected errors
            error = FrameProcessingError(
                code=ErrorCode.DECODE_UNKNOWN_ERROR,
                message=f"Unexpected decode error: {type(e).__name__}: {str(e)}",
                context=context,
            )
            logger.error("frame_decode_unknown_error", error=str(error), **context, exc_info=True)
            return Error(error)
