from pydantic import BaseModel
from typing import List, Optional

class Landmark(BaseModel):
    x: float
    y: float
    z: float

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class FaceDetection(BaseModel):
    face_id: str
    bbox: BoundingBox
    confidence: float
    landmarks: Optional[List[Landmark]] = None
    timestamp: str

class FrameAnalysis(BaseModel):
    frame_id: int
    timestamp: str
    detections: List[FaceDetection]
    faces_count: int

class DetectionRecord(BaseModel):
    id: str
    session_id: str
    frame_analysis: FrameAnalysis
    created_at: str
