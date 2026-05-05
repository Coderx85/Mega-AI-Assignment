"""
Tests for FaceIDGenerator module.

Tests that face IDs are unique, properly formatted, and have no state.
"""

import pytest

from app.services.face_id_generator import FaceIDGenerator


class TestFaceIDGenerator:
    """Test Face ID generation."""

    def test_generate_returns_string(self):
        """Test that generate() returns a string."""
        face_id = FaceIDGenerator.generate()
        assert isinstance(face_id, str)

    def test_generate_format(self):
        """Test that face ID follows format 'face_<8-hex-chars>'."""
        face_id = FaceIDGenerator.generate()
        assert face_id.startswith("face_")
        hex_part = face_id[5:]  # Remove "face_" prefix
        assert len(hex_part) == 8
        # Verify it's valid hex
        int(hex_part, 16)

    def test_generate_uniqueness(self):
        """Test that multiple generated IDs are unique."""
        ids = [FaceIDGenerator.generate() for _ in range(100)]
        assert len(ids) == len(set(ids)), "Generated IDs should be unique"

    def test_generate_no_state(self):
        """Test that generate() has no state (doesn't depend on call count)."""
        # Generate same ID twice (should be different each time due to UUID)
        id1 = FaceIDGenerator.generate()
        id2 = FaceIDGenerator.generate()
        assert id1 != id2

    def test_generate_batch(self):
        """Test batch generation."""
        ids = FaceIDGenerator.generate_batch(10)
        assert len(ids) == 10
        assert len(set(ids)) == 10  # All unique
        assert all(id.startswith("face_") for id in ids)

    def test_generate_batch_empty(self):
        """Test batch generation with count=0."""
        ids = FaceIDGenerator.generate_batch(0)
        assert ids == []

    def test_generate_batch_single(self):
        """Test batch generation with count=1."""
        ids = FaceIDGenerator.generate_batch(1)
        assert len(ids) == 1
        assert ids[0].startswith("face_")

    def test_multiple_calls_independent(self):
        """Test that multiple calls to generate are independent."""
        gen1_ids = [FaceIDGenerator.generate() for _ in range(50)]
        gen2_ids = [FaceIDGenerator.generate() for _ in range(50)]
        # No overlap between two sets of generated IDs
        assert len(set(gen1_ids) & set(gen2_ids)) == 0
