"""
Tests for BboxConverter module.

Tests conversion between BoundingBox, ORM, and API formats, plus validation.
"""

import pytest
from unittest.mock import Mock

from app.converters.bbox_converter import BboxConverter
from app.models.detection import BoundingBox


@pytest.fixture
def valid_bbox():
    """Create a valid bounding box."""
    return BoundingBox(x=10, y=20, width=100, height=150)


@pytest.fixture
def valid_orm_record(valid_bbox):
    """Create a mock ORM record with valid bbox."""
    record = Mock()
    record.bbox_x = valid_bbox.x
    record.bbox_y = valid_bbox.y
    record.bbox_width = valid_bbox.width
    record.bbox_height = valid_bbox.height
    return record


class TestBboxValidation:
    """Test bounding box validation."""

    def test_validate_valid_bbox(self, valid_bbox):
        """Test that valid bbox passes validation."""
        assert BboxConverter.validate(valid_bbox) is True

    def test_validate_width_zero_fails(self):
        """Test that bbox with width=0 fails validation."""
        bbox = BoundingBox(x=10, y=20, width=0, height=100)
        with pytest.raises(ValueError, match="width must be"):
            BboxConverter.validate(bbox)

    def test_validate_height_zero_fails(self):
        """Test that bbox with height=0 fails validation."""
        bbox = BoundingBox(x=10, y=20, width=100, height=0)
        with pytest.raises(ValueError, match="height must be"):
            BboxConverter.validate(bbox)

    def test_validate_negative_width_fails(self):
        """Test that bbox with negative width fails."""
        bbox = BoundingBox(x=10, y=20, width=-50, height=100)
        with pytest.raises(ValueError, match="width must be"):
            BboxConverter.validate(bbox)

    def test_validate_negative_x_fails(self):
        """Test that bbox with negative x fails."""
        bbox = BoundingBox(x=-10, y=20, width=100, height=100)
        with pytest.raises(ValueError, match="must be >= 0"):
            BboxConverter.validate(bbox)

    def test_validate_negative_y_fails(self):
        """Test that bbox with negative y fails."""
        bbox = BoundingBox(x=10, y=-20, width=100, height=100)
        with pytest.raises(ValueError, match="must be >= 0"):
            BboxConverter.validate(bbox)

    def test_validate_oversized_coordinate_fails(self):
        """Test that coordinates exceeding max fail."""
        bbox = BoundingBox(x=200000, y=20, width=100, height=100)
        with pytest.raises(ValueError, match="exceed max"):
            BboxConverter.validate(bbox)

    def test_validate_oversized_dimension_fails(self):
        """Test that dimensions exceeding max fail."""
        bbox = BoundingBox(x=10, y=20, width=200000, height=100)
        with pytest.raises(ValueError, match="exceed max"):
            BboxConverter.validate(bbox)

    def test_validate_non_bbox_fails(self):
        """Test that non-BoundingBox raises TypeError."""
        with pytest.raises(TypeError, match="Expected BoundingBox"):
            BboxConverter.validate({"x": 10, "y": 20, "width": 100, "height": 100}) # type: ignore


class TestBboxToORM:
    """Test conversion to ORM format."""

    def test_to_orm_valid_bbox(self, valid_bbox):
        """Test converting valid bbox to ORM dict."""
        orm_dict = BboxConverter.to_orm(valid_bbox)
        assert orm_dict == {
            "bbox_x": 10,
            "bbox_y": 20,
            "bbox_width": 100,
            "bbox_height": 150,
        }

    def test_to_orm_converts_to_int(self):
        """Test that ORM dict has int values (coerced from Pydantic)."""
        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        orm_dict = BboxConverter.to_orm(bbox)
        assert all(isinstance(v, int) for v in orm_dict.values())
        assert orm_dict["bbox_x"] == 10
        assert orm_dict["bbox_y"] == 20
        assert orm_dict["bbox_width"] == 100
        assert orm_dict["bbox_height"] == 150

    def test_to_orm_invalid_bbox_fails(self):
        """Test that invalid bbox raises during to_orm."""
        bbox = BoundingBox(x=10, y=20, width=0, height=100)
        with pytest.raises(ValueError):
            BboxConverter.to_orm(bbox)


class TestBboxFromORM:
    """Test conversion from ORM format."""

    def test_from_orm_valid_record(self, valid_orm_record):
        """Test converting ORM record to BoundingBox."""
        bbox = BboxConverter.from_orm(valid_orm_record)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 150

    def test_from_orm_missing_field_fails(self):
        """Test that ORM record missing field raises AttributeError."""
        record = Mock(spec=['bbox_x', 'bbox_y', 'bbox_width'])  # Missing bbox_height
        record.bbox_x = 10
        record.bbox_y = 20
        record.bbox_width = 100
        with pytest.raises(AttributeError, match="missing bbox field"):
            BboxConverter.from_orm(record)

    def test_from_orm_invalid_values_fails(self):
        """Test that ORM with invalid bbox values raises."""
        record = Mock()
        record.bbox_x = 10
        record.bbox_y = 20
        record.bbox_width = 0  # Invalid
        record.bbox_height = 100
        with pytest.raises(ValueError):
            BboxConverter.from_orm(record)


class TestBboxToAPI:
    """Test conversion to API format."""

    def test_to_api_valid_record(self, valid_orm_record):
        """Test converting ORM record to API dict."""
        api_dict = BboxConverter.to_api(valid_orm_record)
        assert api_dict == {
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 150,
        }

    def test_to_api_missing_field_fails(self):
        """Test that ORM record missing field raises."""
        record = Mock(spec=['bbox_x', 'bbox_y', 'bbox_width'])  # Missing bbox_height
        record.bbox_x = 10
        record.bbox_y = 20
        record.bbox_width = 100
        with pytest.raises(AttributeError):
            BboxConverter.to_api(record)


class TestBboxFromAPI:
    """Test conversion from API format."""

    def test_from_api_valid_dict(self):
        """Test converting API dict to BoundingBox."""
        api_dict = {"x": 10, "y": 20, "width": 100, "height": 150}
        bbox = BboxConverter.from_api(api_dict)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 150

    def test_from_api_missing_key_fails(self):
        """Test that missing key raises KeyError."""
        api_dict = {"x": 10, "y": 20, "width": 100}  # Missing height
        with pytest.raises(KeyError, match="missing bbox field"):
            BboxConverter.from_api(api_dict)

    def test_from_api_invalid_values_fails(self):
        """Test that invalid values raise."""
        api_dict = {"x": 10, "y": 20, "width": 0, "height": 100}  # width=0
        with pytest.raises(ValueError):
            BboxConverter.from_api(api_dict)

    def test_from_api_non_numeric_fails(self):
        """Test that non-numeric values raise."""
        api_dict = {"x": "ten", "y": 20, "width": 100, "height": 150}
        with pytest.raises(ValueError):
            BboxConverter.from_api(api_dict)


class TestBboxRoundTrip:
    """Test round-trip conversions."""

    def test_bbox_to_orm_to_bbox(self, valid_bbox):
        """Test BoundingBox → ORM → BoundingBox round-trip."""
        orm_dict = BboxConverter.to_orm(valid_bbox)
        record = Mock()
        record.bbox_x = orm_dict["bbox_x"]
        record.bbox_y = orm_dict["bbox_y"]
        record.bbox_width = orm_dict["bbox_width"]
        record.bbox_height = orm_dict["bbox_height"]
        bbox_restored = BboxConverter.from_orm(record)
        assert bbox_restored.x == valid_bbox.x
        assert bbox_restored.y == valid_bbox.y
        assert bbox_restored.width == valid_bbox.width
        assert bbox_restored.height == valid_bbox.height

    def test_bbox_to_api_to_bbox(self, valid_bbox):
        """Test BoundingBox → API → BoundingBox round-trip."""
        orm_dict = BboxConverter.to_orm(valid_bbox)
        record = Mock()
        record.bbox_x = orm_dict["bbox_x"]
        record.bbox_y = orm_dict["bbox_y"]
        record.bbox_width = orm_dict["bbox_width"]
        record.bbox_height = orm_dict["bbox_height"]
        api_dict = BboxConverter.to_api(record)
        bbox_restored = BboxConverter.from_api(api_dict)
        assert bbox_restored.x == valid_bbox.x
        assert bbox_restored.y == valid_bbox.y
        assert bbox_restored.width == valid_bbox.width
        assert bbox_restored.height == valid_bbox.height
