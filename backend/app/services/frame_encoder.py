import io
from typing import List

import numpy as np
from PIL import Image, ImageDraw

from app.models.detection import FaceDetection

class FrameEncoder:
    @staticmethod
    def encode(frame: np.ndarray, quality: int = 80) -> bytes:
        try:
            img = Image.fromarray(frame.astype("uint8"))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return buf.getvalue()
        except Exception as e:
            print(f"[Encoder] Error: {e}")
            return b""

    @staticmethod
    def draw_bboxes(frame: np.ndarray, detections: List[FaceDetection]) -> np.ndarray:
        try:
            img = Image.fromarray(frame.astype("uint8"))
            draw = ImageDraw.Draw(img)
            for det in detections:
                b = det.bbox
                draw.rectangle(
                    [(b.x, b.y), (b.x + b.width, b.y + b.height)],
                    outline=(0, 255, 0),
                    width=2,
                )
                draw.text((b.x, b.y - 10), f"{det.confidence:.2f}", fill=(0, 255, 0))
            return np.array(img)
        except Exception as e:
            print(f"[Encoder] Draw error: {e}")
            return frame
