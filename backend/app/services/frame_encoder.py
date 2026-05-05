"""
Frame encoder module: converts NumPy arrays to JPEG bytes and draws bounding boxes.

Returns Result[bytes] with proper error codes and logging.
"""

import io
from typing import List, Union

import numpy as np
import structlog
from PIL import Image, ImageDraw

from app.errors import Ok, Error, Result, FrameProcessingError, ErrorCode
from app.models.detection import FaceDetection

logger = structlog.get_logger(__name__)


class FrameEncoder:
    """Encodes NumPy arrays to JPEG bytes and draws bounding boxes."""

    # JPEG quality (0-100)
    DEFAULT_QUALITY = 80

    @staticmethod
    def encode(
        frame: np.ndarray,
        quality: int = None,
        context: dict = None,
    ) -> Result[bytes]:
        """
        Encode NumPy RGB array to JPEG bytes.

        Args:
            frame: RGB NumPy array
            quality: JPEG quality (0-100), defaults to DEFAULT_QUALITY
            context: Optional context dict for logging

        Returns:
            Ok(bytes) on success, Error(FrameProcessingError) on failure
        """
        context = context or {}
        quality = quality or FrameEncoder.DEFAULT_QUALITY

        try:
            # Validate frame
            if not isinstance(frame, np.ndarray):
                raise TypeError(f"Expected np.ndarray, got {type(frame)}")

            if len(frame.shape) != 3 or frame.shape[2] != 3:  # RGB channel check
                raise ValueError(f"Expected 3D array with 3 channels (RGB), got shape {frame.shape}")

            # Convert to uint8 if necessary
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)

            # Encode to JPEG
            img = Image.fromarray(frame)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            encoded_bytes = buf.getvalue()

            logger.debug("frame_encoded", size=len(encoded_bytes), quality=quality, **context)
            return Ok(encoded_bytes)

        except TypeError as e:
            error = FrameProcessingError(
                code=ErrorCode.ENCODE_ERROR,
                message=f"Invalid frame type: {str(e)}",
                context=context,
            )
            logger.warning("frame_encode_type_error", error=str(error), **context)
            return Error(error)

        except ValueError as e:
            error = FrameProcessingError(
                code=ErrorCode.ENCODE_ERROR,
                message=f"Invalid frame shape: {str(e)}",
                context=context,
            )
            logger.warning("frame_encode_value_error", error=str(error), **context)
            return Error(error)

        except OSError as e:
            error = FrameProcessingError(
                code=ErrorCode.ENCODE_ERROR,
                message=f"JPEG encoding failed: {str(e)}",
                context=context,
            )
            logger.warning("frame_encode_os_error", error=str(error), **context)
            return Error(error)

        except Exception as e:
            error = FrameProcessingError(
                code=ErrorCode.ENCODE_UNKNOWN_ERROR,
                message=f"Unexpected encode error: {type(e).__name__}: {str(e)}",
                context=context,
            )
            logger.error("frame_encode_unknown_error", error=str(error), **context, exc_info=True)
            return Error(error)

    @staticmethod
    def draw_bboxes(
        frame: np.ndarray,
        detections: List[FaceDetection],
        context: dict = None,
    ) -> Result[np.ndarray]:
        """
        Draw bounding boxes on frame for detected faces.

        Args:
            frame: RGB NumPy array
            detections: List of FaceDetection objects
            context: Optional context dict for logging

        Returns:
            Ok(frame_with_bboxes) on success, Error(FrameProcessingError) on failure
        """
        context = context or {}

        if not detections:
            logger.debug("no_detections_to_draw", count=0, **context)
            return Ok(frame)

        try:
            # Validate frame
            if not isinstance(frame, np.ndarray):
                raise TypeError(f"Expected np.ndarray, got {type(frame)}")

            # Convert to uint8 if necessary (PIL requirement)
            if frame.dtype != np.uint8:
                frame_uint8 = frame.astype(np.uint8)
            else:
                frame_uint8 = frame

            # Convert to PIL Image for drawing
            img = Image.fromarray(frame_uint8)
            draw = ImageDraw.Draw(img)

            # Draw each detection
            drawn_count = 0
            for idx, det in enumerate(detections):
                try:
                    b = det.bbox

                    # Validate bbox
                    if b.width <= 0 or b.height <= 0:
                        logger.warning(
                            "invalid_bbox_dimensions",
                            detection_index=idx,
                            width=b.width,
                            height=b.height,
                            **context,
                        )
                        continue

                    # Draw rectangle
                    draw.rectangle(
                        [(b.x, b.y), (b.x + b.width, b.y + b.height)],
                        outline=(0, 255, 0),
                        width=2,
                    )

                    # Draw confidence label
                    label = f"{det.confidence:.2f}"
                    draw.text((b.x, b.y - 10), label, fill=(0, 255, 0))

                    drawn_count += 1

                except Exception as e:
                    logger.warning(
                        "bbox_draw_error",
                        detection_index=idx,
                        error=str(e),
                        **context,
                    )
                    continue

            # Convert back to NumPy
            result_frame = np.array(img)
            logger.debug("bboxes_drawn", count=drawn_count, total=len(detections), **context)
            return Ok(result_frame)

        except TypeError as e:
            error = FrameProcessingError(
                code=ErrorCode.DRAW_INVALID_BBOX,
                message=f"Invalid frame type: {str(e)}",
                context=context,
            )
            logger.warning("draw_type_error", error=str(error), **context)
            return Error(error)

        except Exception as e:
            error = FrameProcessingError(
                code=ErrorCode.DRAW_ENCODING_ERROR,
                message=f"Unexpected drawing error: {type(e).__name__}: {str(e)}",
                context=context,
            )
            logger.error("draw_unknown_error", error=str(error), **context, exc_info=True)
            return Error(error)
