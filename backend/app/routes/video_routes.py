from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.detection import FrameAnalysis
from app.repository.face_repository import FaceRepository
from app.routes.feed_routes import update_latest_frame
from app.services.face_detector import FaceDetector
from app.services.frame_decoder import FrameDecoder
from app.services.frame_encoder import FrameEncoder

router = APIRouter()

def setup_routes(repo: FaceRepository, decoder: FrameDecoder, encoder: FrameEncoder, detector: FaceDetector):
    @router.websocket("/ws/video")
    async def websocket_video(websocket: WebSocket):
        print(f"[WS] Connection attempt from {websocket.client}")

        try:
            await websocket.accept()
            print("[WS] Connection accepted")
        except Exception as e:
            print(f"[WS] Accept failed: {e}")
            return

        session_id = f"{websocket.client.host}:{websocket.client.port}"
        frame_id = 0

        try:
            while True:
                frame_bytes = await websocket.receive_bytes()
                frame_id += 1

                frame_np = decoder.decode(frame_bytes)
                if frame_np is None:
                    continue

                detections = detector.detect(frame_np)

                analysis = FrameAnalysis(
                    frame_id=frame_id,
                    timestamp=datetime.utcnow().isoformat(),
                    detections=detections,
                    faces_count=len(detections),
                )

                if detections:
                    repo.create(session_id, analysis)
                    print(f"[WS] Frame {frame_id}: {len(detections)} face(s) found")

                annotated = encoder.draw_bboxes(frame_np, detections)
                jpeg_bytes = encoder.encode(annotated)

                update_latest_frame(jpeg_bytes)

                await websocket.send_bytes(jpeg_bytes)
                await websocket.send_text(analysis.model_dump_json())

        except WebSocketDisconnect:
            print(f"[WS] {session_id} disconnected after {frame_id} frames")
        except Exception as e:
            print(f"[WS] Error: {e}")
            try:
                await websocket.close(code=1000)
            except Exception:
                pass

    return router
