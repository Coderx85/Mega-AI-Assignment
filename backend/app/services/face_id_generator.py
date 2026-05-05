"""
Face ID generation for detected faces.

Uses UUID-based approach to generate globally unique face IDs
without maintaining instance state.
"""

import uuid


class FaceIDGenerator:
    """Generates unique face IDs using UUID."""

    @staticmethod
    def generate() -> str:
        """
        Generate a unique face ID.

        Returns:
            str: Unique face ID in format "face_<8-char-hex>"
        """
        return f"face_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def generate_batch(count: int) -> list[str]:
        """
        Generate a batch of unique face IDs.

        Args:
            count: Number of face IDs to generate

        Returns:
            list[str]: List of unique face IDs
        """
        return [FaceIDGenerator.generate() for _ in range(count)]
