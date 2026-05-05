import asyncio
from datetime import datetime, UTC
from typing import Dict, Optional

class FrameCache:
    def __init__(self):
        self._frames: Dict[str, tuple[datetime, bytes]] = {}
        self._lock = asyncio.Lock()
        self._latest_session: str | None = None

    async def put(self, session_id: str, frame_bytes: bytes) -> None:
        async with self._lock:
            self._frames[session_id] = (datetime.now(UTC), frame_bytes)
            self._latest_session = session_id

    async def latest(self, session_id: str) -> Optional[bytes]:
        async with self._lock:
            entry = self._frames.get(session_id)
            return entry[1] if entry else None

    async def latest_any(self) -> Optional[bytes]:
        async with self._lock:
            if self._latest_session is None:
                return None
            entry = self._frames.get(self._latest_session)
            return entry[1] if entry else None

    async def clear(self, session_id: str) -> None:
        async with self._lock:
            self._frames.pop(session_id, None)
