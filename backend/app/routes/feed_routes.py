import asyncio
import io
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.detection import DetectionRecord
from app.repository.face_repository import FaceRepository
from app.services.face_detector import FaceDetector
from app.services.frame_decoder import FrameDecoder
from app.services.frame_encoder import FrameEncoder

router = APIRouter()

_frame_store: dict = {"latest_frame": None}

def setup_routes(repo: FaceRepository, encoder: FrameEncoder):
    @router.get("/feed")
    async def serve_video_feed():
        async def frame_stream() -> AsyncGenerator[bytes, None]:
            while True:
                frame_bytes = _frame_store.get("latest_frame")
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
        records = repo.get_recent(limit)
        return {
            "total": len(records),
            "records": [r.model_dump() for r in records],
        }

    return router

def update_latest_frame(frame_bytes: bytes) -> None:
    _frame_store["latest_frame"] = frame_bytes
