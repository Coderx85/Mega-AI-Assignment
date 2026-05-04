import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.repository.face_repository import FaceRepository
from app.services.frame_decoder import FrameDecoder
from app.services.frame_encoder import FrameEncoder
from app.services.face_detector import FaceDetector
from app.routes.video_routes import setup_routes as setup_video_routes
from app.routes.feed_routes import setup_routes as setup_feed_routes

app = FastAPI(title="Face Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repo = FaceRepository()
decoder = FrameDecoder()
encoder = FrameEncoder()
detector = FaceDetector()

@app.on_event("startup")
async def startup():
    print("[Server] Starting Face Detection API...")
    print(f"[Server] Repository stats: {repo.get_stats()}")

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
    return repo.get_stats()

app.include_router(setup_video_routes(repo, decoder, encoder, detector))
app.include_router(setup_feed_routes(repo, encoder))
