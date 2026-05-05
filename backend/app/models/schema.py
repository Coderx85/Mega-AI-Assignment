from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, JSON
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class FaceDetectionRecord(Base):
    __tablename__ = "face_detections"

    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    frame_id = Column(Integer, nullable=False)
    face_id = Column(String, nullable=False)
    bbox_x = Column(Integer, nullable=False)
    bbox_y = Column(Integer, nullable=False)
    bbox_width = Column(Integer, nullable=False)
    bbox_height = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    keypoints = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<FaceDetection id={self.face_id} confidence={self.confidence}>"
