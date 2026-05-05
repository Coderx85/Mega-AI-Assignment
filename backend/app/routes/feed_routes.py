import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import structlog

from app.repository.face_repository import FaceRepository
from app.services.frame_cache import FrameCache
from app.converters.bbox_converter import BboxConverter

router = APIRouter()
logger = structlog.get_logger(__name__)


def _record_to_dict(record) -> dict:
    """Convert ORM record to API response dict using converters."""
    try:
        return {
            "id": record.id,
            "session_id": record.session_id,
            "frame_id": record.frame_id,
            "face_id": record.face_id,
            "bbox": BboxConverter.to_api(record),
            "confidence": record.confidence,
            "keypoints": record.keypoints,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
    except Exception as e:
        logger.error("record_to_dict_failed", error=str(e), record_id=record.id, exc_info=True)
        raise


def setup_routes(repo: FaceRepository, cache: FrameCache):
    @router.get("/feed")
    async def serve_video_feed(session: str | None = None):
        async def frame_stream() -> AsyncGenerator[bytes, None]:
            while True:
                if session:
                    frame_bytes = await cache.latest(session)
                else:
                    frame_bytes = await cache.latest_any()

                if frame_bytes:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + frame_bytes
                        + b"\r\n"
                    )
                await asyncio.sleep(0.1)

        return StreamingResponse(
            frame_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    @router.get("/roi")
    async def serve_roi_data(limit: int = 50):
        records = await repo.get_recent(limit)
        return {
            "total": len(records),
            "records": [_record_to_dict(r) for r in records],
        }

    return router
