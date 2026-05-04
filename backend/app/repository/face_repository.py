import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from app.models.detection import DetectionRecord, FrameAnalysis

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)
DETECTIONS_FILE = os.path.join(DATA_DIR, "detections.json")

class FaceRepository:
    def __init__(self):
        self.in_memory: Dict[str, DetectionRecord] = {}
        os.makedirs(DATA_DIR, exist_ok=True)
        self._load_from_file()

    def _load_from_file(self):
        if os.path.exists(DETECTIONS_FILE):
            try:
                with open(DETECTIONS_FILE, "r") as f:
                    data = json.load(f)
                    for d in data:
                        record = DetectionRecord(**d)
                        self.in_memory[record.id] = record
                print(f"[Repo] Loaded {len(self.in_memory)} records")
            except Exception as e:
                print(f"[Repo] Error loading: {e}")

    def _save_to_file(self):
        try:
            records = [json.loads(r.model_dump_json()) for r in self.in_memory.values()]
            with open(DETECTIONS_FILE, "w") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            print(f"[Repo] Error saving: {e}")

    def create(self, session_id: str, frame_analysis: FrameAnalysis) -> DetectionRecord:
        record = DetectionRecord(
            id=str(uuid4()),
            session_id=session_id,
            frame_analysis=frame_analysis,
            created_at=datetime.utcnow().isoformat(),
        )
        self.in_memory[record.id] = record
        self._save_to_file()
        return record

    def get_by_id(self, record_id: str) -> Optional[DetectionRecord]:
        return self.in_memory.get(record_id)

    def get_recent(self, limit: int = 50) -> List[DetectionRecord]:
        sorted_records = sorted(
            self.in_memory.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return sorted_records[:limit]

    def get_stats(self) -> Dict:
        total_faces = sum(r.frame_analysis.faces_count for r in self.in_memory.values())
        sessions = set(r.session_id for r in self.in_memory.values())
        return {
            "total_records": len(self.in_memory),
            "total_faces_detected": total_faces,
            "unique_sessions": len(sessions),
        }
