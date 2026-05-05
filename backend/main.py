import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
import structlog

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Database
from app.models.schema import Base
from app.repository.face_repository import FaceRepository
from app.services.frame_decoder import FrameDecoder
from app.services.frame_encoder import FrameEncoder
from app.services.face_detector import FaceDetector
from app.services.frame_cache import FrameCache
from app.routes.video_routes import setup_routes as setup_video_routes
from app.routes.feed_routes import setup_routes as setup_feed_routes
from app.logging import setup_logging

# Initialize structured logging
setup_logging()
logger = structlog.get_logger(__name__)

db = Database(settings.database_url)
repo = FaceRepository(db)
decoder = FrameDecoder()
encoder = FrameEncoder()
detector = FaceDetector()
cache = FrameCache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    await db.create_tables(Base)
    logger.info("server_starting", message="Face Detection API initializing...")
    stats = await repo.get_stats()
    logger.info("repository_stats", total_records=stats["total_records"], total_faces=stats["total_faces_detected"], unique_sessions=stats["unique_sessions"])
    yield
    await db.close()
    logger.info("server_shutdown", message="Face Detection API shutting down")

app = FastAPI(title="Face Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Face Detection API",
        "status": "ok",
        "endpoints": {
            "ws_receive": "ws://localhost:8000/ws/video",
            "feed_stream": "http://localhost:8000/feed",
            "roi_data": "http://localhost:8000/roi",
        },
    }

@app.get("/stats")
async def stats():
    return await repo.get_stats()

app.include_router(setup_video_routes(repo, decoder, encoder, detector, cache))
app.include_router(setup_feed_routes(repo, cache))
