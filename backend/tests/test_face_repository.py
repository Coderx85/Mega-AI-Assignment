import pytest
import pytest_asyncio
from datetime import datetime, timezone

from app.database import Database
from app.models.detection import (
    FrameAnalysis,
    FaceDetection,
    BoundingBox,
    Landmark,
)
from app.models.schema import Base
from app.repository.face_repository import FaceRepository


@pytest_asyncio.fixture
async def db():
    test_db = Database("sqlite+aiosqlite:///")
    test_db.init()
    async with test_db._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_db
    await test_db.close()


@pytest.fixture
def repo(db: Database) -> FaceRepository:
    return FaceRepository(db)


@pytest.fixture
def sample_frame_analysis() -> FrameAnalysis:
    return FrameAnalysis(
        frame_id=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        detections=[
            FaceDetection(
                face_id="face_0",
                bbox=BoundingBox(x=100, y=50, width=120, height=140),
                confidence=0.94,
                landmarks=[
                    Landmark(x=0.4, y=0.3, z=0.0),
                    Landmark(x=0.6, y=0.3, z=0.0),
                ],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        ],
        faces_count=1,
    )


@pytest.fixture
def sample_frame_no_detections() -> FrameAnalysis:
    return FrameAnalysis(
        frame_id=2,
        timestamp=datetime.now(timezone.utc).isoformat(),
        detections=[],
        faces_count=0,
    )


@pytest.fixture
def sample_frame_two_faces() -> FrameAnalysis:
    return FrameAnalysis(
        frame_id=3,
        timestamp=datetime.now(timezone.utc).isoformat(),
        detections=[
            FaceDetection(
                face_id="face_0",
                bbox=BoundingBox(x=80, y=40, width=100, height=120),
                confidence=0.92,
                landmarks=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
            FaceDetection(
                face_id="face_1",
                bbox=BoundingBox(x=200, y=60, width=110, height=130),
                confidence=0.87,
                landmarks=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        ],
        faces_count=2,
    )


@pytest.mark.asyncio
async def test_create_and_get_by_id(repo, sample_frame_analysis):
    record = await repo.create("session_a", sample_frame_analysis)
    assert record is not None
    assert record.session_id == "session_a"
    assert record.frame_id == 1

    fetched = await repo.get_by_id(record.id)
    assert fetched is not None
    assert fetched.face_id == "face_0"
    assert fetched.bbox_x == 100
    assert fetched.bbox_y == 50
    assert fetched.bbox_width == 120
    assert fetched.bbox_height == 140
    assert fetched.confidence == 0.94
    assert len(fetched.keypoints) == 2


@pytest.mark.asyncio
async def test_create_no_detections_returns_none(repo, sample_frame_no_detections):
    result = await repo.create("session_b", sample_frame_no_detections)
    assert result is None


@pytest.mark.asyncio
async def test_create_multiple_faces(repo, sample_frame_two_faces):
    record = await repo.create("session_c", sample_frame_two_faces)
    assert record is not None

    stats = await repo.get_stats()
    assert stats["total_faces_detected"] == 2


@pytest.mark.asyncio
async def test_get_recent_ordering(repo, sample_frame_analysis):
    await repo.create("session_1", sample_frame_analysis)

    second = FrameAnalysis(
        frame_id=2,
        timestamp=datetime.now(timezone.utc).isoformat(),
        detections=[
            FaceDetection(
                face_id="face_1",
                bbox=BoundingBox(x=50, y=30, width=90, height=110),
                confidence=0.88,
                landmarks=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        ],
        faces_count=1,
    )
    await repo.create("session_2", second)

    recent = await repo.get_recent(limit=5)
    assert len(recent) == 2
    assert recent[0].frame_id >= recent[1].frame_id


@pytest.mark.asyncio
async def test_get_recent_limit(repo, sample_frame_analysis):
    for i in range(10):
        fa = FrameAnalysis(
            frame_id=i,
            timestamp=datetime.now(timezone.utc).isoformat(),
            detections=[
                FaceDetection(
                    face_id=f"face_{i}",
                    bbox=BoundingBox(x=i * 10, y=0, width=50, height=60),
                    confidence=0.9,
                    landmarks=None,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            ],
            faces_count=1,
        )
        await repo.create(f"session_{i}", fa)

    recent = await repo.get_recent(limit=3)
    assert len(recent) == 3


@pytest.mark.asyncio
async def test_get_stats_empty(db):
    empty_repo = FaceRepository(db)
    stats = await empty_repo.get_stats()
    assert stats["total_records"] == 0
    assert stats["total_faces_detected"] == 0
    assert stats["unique_sessions"] == 0


@pytest.mark.asyncio
async def test_get_stats_counts(repo, sample_frame_analysis, sample_frame_two_faces):
    await repo.create("session_a", sample_frame_analysis)
    await repo.create("session_b", sample_frame_two_faces)

    stats = await repo.get_stats()
    assert stats["total_faces_detected"] == 3
    assert stats["unique_sessions"] == 2
