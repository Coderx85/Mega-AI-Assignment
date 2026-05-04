import io
from typing import Optional

import numpy as np
from PIL import Image

class FrameDecoder:
    @staticmethod
    def decode(frame_bytes: bytes) -> Optional[np.ndarray]:
        try:
            img = Image.open(io.BytesIO(frame_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")
            return np.array(img)
        
        except Exception as e:
            print(f"[Decoder] Error: {e}")
            return None
