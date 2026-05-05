from datetime import datetime, UTC
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import func, select
import structlog

from app.database import Database
from app.models.detection import FrameAnalysis
from app.models.schema import FaceDetectionRecord
from app.converters.bbox_converter import BboxConverter

# Initialize logger
logger = structlog.get_logger(__name__)

class FaceRepository:
    def __init__(self, db: Database):
        self._db = db

    async def create(self, session_id: str, frame_analysis: FrameAnalysis) -> Optional[FaceDetectionRecord]:
        records: List[FaceDetectionRecord] = []
        async with self._db.get_session() as db_session:
            for detection in frame_analysis.detections:
                try:
                    # Validate and convert bbox using converter
                    bbox_data = BboxConverter.to_orm(detection.bbox)

                    record = FaceDetectionRecord(
                        id=str(uuid4()),
                        session_id=session_id,
                        frame_id=frame_analysis.frame_id,
                        face_id=detection.face_id,
                        bbox_x=bbox_data["bbox_x"],
                        bbox_y=bbox_data["bbox_y"],
                        bbox_width=bbox_data["bbox_width"],
                        bbox_height=bbox_data["bbox_height"],
                        confidence=detection.confidence,
                        keypoints=[{"x": k.x, "y": k.y, "z": k.z} for k in detection.landmarks] if detection.landmarks else None,
                        timestamp=datetime.fromisoformat(detection.timestamp).replace(tzinfo=None),
                        created_at=datetime.now(UTC).replace(tzinfo=None),
                    )
                    # Add record to session
                    db_session.add(record)

                    # Append to local list for return value
                    records.append(record)
                except ValueError as e:
                    logger.warning("detection_persistence_failed", error=str(e), face_id=detection.face_id)
                    continue
        return records[0] if records else None

    async def get_by_id(self, record_id: str) -> Optional[FaceDetectionRecord]:
        async with self._db.get_session() as db_session:
            result = await db_session.execute(
                select(FaceDetectionRecord).where(FaceDetectionRecord.id == record_id)
            )
            return result.scalar_one_or_none()

    async def get_recent(self, limit: int = 50) -> List[FaceDetectionRecord]:
        async with self._db.get_session() as db_session:
            stmt = select(FaceDetectionRecord).order_by(FaceDetectionRecord.created_at.desc()).limit(limit)
            result = await db_session.execute(stmt)
            return list(result.scalars().all())

    async def get_stats(self) -> Dict:
        async with self._db.get_session() as db_session:
            total_records = await db_session.execute(select(func.count(FaceDetectionRecord.id)))
            total_faces = total_records.scalar() or 0

            sessions = await db_session.execute(select(func.count(func.distinct(FaceDetectionRecord.session_id))))
            unique_sessions = sessions.scalar() or 0

            return {
                "total_records": total_faces,
                "total_faces_detected": total_faces,
                "unique_sessions": unique_sessions,
            }
