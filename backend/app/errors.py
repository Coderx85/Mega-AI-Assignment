"""
Error handling infrastructure for frame processing pipeline.

Defines Result[T] type and frame processing error codes.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Ok(Generic[T]):
    """Success result carrying data of type T."""
    data: T

    def is_ok(self) -> bool:
        return True

    def is_error(self) -> bool:
        return False

    def unwrap(self) -> T:
        """Return the success value."""
        return self.data

    def unwrap_or(self, default: T) -> T:
        """Return success value or default."""
        return self.data

    def map(self, f):
        """Apply function to success value, return new Result."""
        return Ok(f(self.data))


@dataclass
class Error(Generic[E]):
    """Failure result carrying error of type E."""
    error: E

    def is_ok(self) -> bool:
        return False

    def is_error(self) -> bool:
        return True

    def unwrap(self) -> E:
        """Raise the error if called on Error. Use unwrap_or instead."""
        raise RuntimeError(f"Called unwrap() on Error: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Return default on error."""
        return default

    def map(self, f):
        """Skip the function on error, return self unchanged."""
        return self


# Union type for Result[T, E]
Result = Union[Ok[T], Error[E]]


@dataclass
class FrameProcessingError:
    """Standardized frame processing error with context."""
    code: str  # "decode_error", "detector_error", "encoder_error", "persistence_error"
    message: str
    context: dict  # Additional context (e.g., {"session_id": "...", "frame_id": 123})

    def __str__(self) -> str:
        return f"{self.code}: {self.message} ({self.context})"


# Error codes
class ErrorCode:
    """Frame processing error codes."""
    DECODE_JPEG_ERROR = "decode_jpeg_error"
    DECODE_OVERSIZED_FRAME = "decode_oversized_frame"
    DECODE_INVALID_FORMAT = "decode_invalid_format"
    DECODE_EMPTY_FRAME = "decode_empty_frame"
    DECODE_UNKNOWN_ERROR = "decode_unknown_error"

    DRAW_INVALID_BBOX = "draw_invalid_bbox"
    DRAW_ENCODING_ERROR = "draw_encoding_error"
    ENCODE_ERROR = "encode_error"
    ENCODE_UNKNOWN_ERROR = "encode_unknown_error"

    DETECTOR_ERROR = "detector_error"
    PERSISTENCE_ERROR = "persistence_error"
