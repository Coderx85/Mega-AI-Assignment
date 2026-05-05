"""
Bounding box serialization converter.

Handles conversion between Pydantic BoundingBox, ORM columns, and API response format.
Centralizes bbox validation and serialization logic.
"""

from typing import Dict, Any

import structlog

from app.models.detection import BoundingBox

logger = structlog.get_logger(__name__)


class BboxConverter:
    """Converts bounding boxes between different representations."""

    # Bbox invariants
    MIN_DIMENSION = 0
    MAX_COORDINATE = 100000  # Reasonable max coordinate value

    @staticmethod
    def validate(bbox: BoundingBox) -> bool:
        """
        Validate bounding box invariants.

        Args:
            bbox: BoundingBox to validate

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValueError: If bbox violates invariants
        """
        if not isinstance(bbox, BoundingBox):
            raise TypeError(f"Expected BoundingBox, got {type(bbox)}")

        if bbox.width <= BboxConverter.MIN_DIMENSION:
            raise ValueError(f"bbox.width must be > {BboxConverter.MIN_DIMENSION}, got {bbox.width}")

        if bbox.height <= BboxConverter.MIN_DIMENSION:
            raise ValueError(f"bbox.height must be > {BboxConverter.MIN_DIMENSION}, got {bbox.height}")

        if bbox.x < 0:
            raise ValueError(f"bbox.x must be >= 0, got {bbox.x}")

        if bbox.y < 0:
            raise ValueError(f"bbox.y must be >= 0, got {bbox.y}")

        if bbox.x > BboxConverter.MAX_COORDINATE or bbox.y > BboxConverter.MAX_COORDINATE:
            raise ValueError(f"bbox coordinates exceed max {BboxConverter.MAX_COORDINATE}")

        if bbox.width > BboxConverter.MAX_COORDINATE or bbox.height > BboxConverter.MAX_COORDINATE:
            raise ValueError(f"bbox dimensions exceed max {BboxConverter.MAX_COORDINATE}")

        return True

    @staticmethod
    def to_orm(bbox: BoundingBox) -> Dict[str, int]:
        """
        Convert BoundingBox to ORM column dict.

        Args:
            bbox: BoundingBox to convert

        Returns:
            dict: {bbox_x, bbox_y, bbox_width, bbox_height}

        Raises:
            ValueError: If bbox is invalid
        """
        BboxConverter.validate(bbox)

        return {
            "bbox_x": int(bbox.x),
            "bbox_y": int(bbox.y),
            "bbox_width": int(bbox.width),
            "bbox_height": int(bbox.height),
        }

    @staticmethod
    def from_orm(orm_record: Any) -> BoundingBox:
        """
        Convert ORM record to BoundingBox.

        Args:
            orm_record: ORM record with bbox_x, bbox_y, bbox_width, bbox_height attributes

        Returns:
            BoundingBox: Reconstructed bounding box

        Raises:
            AttributeError: If ORM record missing required fields
            ValueError: If values don't reconstruct a valid bbox
        """
        try:
            bbox = BoundingBox(
                x=orm_record.bbox_x,
                y=orm_record.bbox_y,
                width=orm_record.bbox_width,
                height=orm_record.bbox_height,
            )
            BboxConverter.validate(bbox)
            return bbox
        except AttributeError as e:
            raise AttributeError(f"ORM record missing bbox field: {str(e)}") from e
        except ValueError as e:
            raise ValueError(f"Invalid bbox reconstructed from ORM: {str(e)}") from e

    @staticmethod
    def to_api(orm_record: Any) -> Dict[str, int]:
        """
        Convert ORM record to API response dict.

        Args:
            orm_record: ORM record with bbox_x, bbox_y, bbox_width, bbox_height attributes

        Returns:
            dict: {x, y, width, height} for JSON serialization

        Raises:
            AttributeError: If ORM record missing required fields
        """
        try:
            return {
                "x": orm_record.bbox_x,
                "y": orm_record.bbox_y,
                "width": orm_record.bbox_width,
                "height": orm_record.bbox_height,
            }
        except AttributeError as e:
            logger.error("bbox_api_conversion_failed", error=str(e), exc_info=True)
            raise AttributeError(f"ORM record missing bbox field: {str(e)}") from e

    @staticmethod
    def from_api(api_dict: Dict[str, int]) -> BoundingBox:
        """
        Convert API request dict to BoundingBox.

        Args:
            api_dict: {x, y, width, height} dict

        Returns:
            BoundingBox: Parsed bounding box

        Raises:
            KeyError: If dict missing required keys
            ValueError: If values invalid
        """
        try:
            bbox = BoundingBox(
                x=int(api_dict["x"]),
                y=int(api_dict["y"]),
                width=int(api_dict["width"]),
                height=int(api_dict["height"]),
            )
            BboxConverter.validate(bbox)
            return bbox
        except KeyError as e:
            raise KeyError(f"API dict missing bbox field: {str(e)}") from e
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid bbox in API dict: {str(e)}") from e
