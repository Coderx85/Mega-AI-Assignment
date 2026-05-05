"""
WebSocket video feed handler for face detection pipeline.

Receives JPEG frames, runs detection, draws ROIs, caches, and persists.
Uses Result types for error handling and structured logging.
"""

from datetime import datetime, UTC

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from app.models.detection import FrameAnalysis
from app.repository.face_repository import FaceRepository
from app.services.face_detector import FaceDetector
from app.services.frame_decoder import FrameDecoder
from app.services.frame_encoder import FrameEncoder
from app.services.frame_cache import FrameCache

router = APIRouter()
logger = structlog.get_logger(__name__)


def setup_routes(
    repo: FaceRepository,
    decoder: FrameDecoder,
    encoder: FrameEncoder,
    detector: FaceDetector,
    cache: FrameCache,
):
    """Setup video feed routes with dependency injection."""

    @router.websocket("/ws/video")
    async def websocket_video(websocket: WebSocket):
        """
        WebSocket endpoint for video feed with face detection.

        Receives JPEG frames, detects faces, draws ROIs, caches, and persists.
        """
        client_addr = str(websocket.client) if websocket.client else "unknown"
        logger.info("ws_connection_attempt", client=client_addr)

        try:
            await websocket.accept()
            logger.info("ws_connection_accepted", client=client_addr)
        except Exception as e:
            logger.error("ws_accept_failed", error=str(e), client=client_addr, exc_info=True)
            print(f"ERROR: WebSocket accept failed: {e}")  # Also print for debugging
            return

        session_id = f"{websocket.client.host}:{websocket.client.port}" # type: ignore
        frame_id = 0
        frames_processed = 0
        frames_skipped = 0
        frames_persisted = 0

        try:
            while True:
                # Receive JPEG frame from client
                frame_bytes = await websocket.receive_bytes()
                frame_id += 1

                # Create context for logging
                context = {
                    "session_id": session_id,
                    "frame_id": frame_id,
                }

                # Decode JPEG to NumPy array
                decode_result = decoder.decode(frame_bytes, context=context)

                if decode_result.is_error():
                    # Log decode error and skip frame
                    error = decode_result.error # type: ignore
                    logger.warning(
                        "frame_decode_failed",
                        error_code=error.code,
                        error_message=error.message,
                        **context,
                    )
                    frames_skipped += 1
                    continue

                frame_np = decode_result.unwrap()
                frames_processed += 1

                # Run face detection
                try:
                    detections = detector.detect(frame_np)
                    logger.debug("frame_detected", detections_count=len(detections), **context)
                except Exception as e:
                    logger.error(
                        "detection_failed",
                        error=str(e),
                        **context,
                        exc_info=True,
                    )
                    frames_skipped += 1
                    continue

                # Create frame analysis
                analysis = FrameAnalysis(
                    frame_id=frame_id,
                    timestamp=datetime.now(UTC).isoformat(),
                    detections=detections,
                    faces_count=len(detections),
                )

                # Persist to database if detections found
                if detections:
                    try:
                        record = await repo.create(session_id, analysis)
                        if record:
                            frames_persisted += 1
                            logger.info(
                                "frame_persisted",
                                faces_count=len(detections),
                                **context,
                            )
                    except Exception as e:
                        logger.error(
                            "persistence_failed",
                            error=str(e),
                            **context,
                            exc_info=True,
                        )

                # Draw bounding boxes on frame
                draw_result = encoder.draw_bboxes(frame_np, detections, context=context)

                if draw_result.is_error():
                    error = draw_result.error # type: ignore
                    logger.warning(
                        "draw_bboxes_failed",
                        error_code=error.code,
                        error_message=error.message,
                        **context,
                    )
                    # Use original frame if drawing failed
                    annotated = frame_np
                else:
                    annotated = draw_result.unwrap()

                # Encode to JPEG
                encode_result = encoder.encode(annotated, context=context)

                if encode_result.is_error():
                    error = encode_result.error # type: ignore
                    logger.error(
                        "encode_failed",
                        error_code=error.code,
                        error_message=error.message,
                        **context,
                    )
                    frames_skipped += 1
                    continue

                jpeg_bytes = encode_result.unwrap()

                # Cache the encoded frame
                try:
                    await cache.put(session_id, jpeg_bytes)
                except Exception as e:
                    logger.warning("cache_put_failed", error=str(e), **context)

                # Send encoded frame and analysis to client
                try:
                    await websocket.send_bytes(jpeg_bytes)
                    await websocket.send_text(analysis.model_dump_json())
                except Exception as e:
                    logger.warning("send_failed", error=str(e), **context)

        except WebSocketDisconnect:
            logger.info(
                "ws_disconnect",
                session_id=session_id,
                frames_processed=frames_processed,
                frames_persisted=frames_persisted,
                frames_skipped=frames_skipped,
            )
            try:
                await cache.clear(session_id)
            except Exception as e:
                logger.warning("cache_clear_failed", session_id=session_id, error=str(e))

        except Exception as e:
            logger.error(
                "ws_error",
                session_id=session_id,
                error=str(e),
                frames_processed=frames_processed,
                exc_info=True,
            )
            try:
                await cache.clear(session_id)
                await websocket.close(code=1011)  # Server error
            except Exception as close_error:
                logger.warning("ws_close_failed", error=str(close_error))

    return router
