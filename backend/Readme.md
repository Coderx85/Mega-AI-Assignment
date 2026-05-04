# Real-Time Face Detection Backend

## Tech Stack

- **Python 3.14**
- **FastAPI** - Async web framework
- **MediaPipe 0.10** - Face detection (BlazeFace model)
- **OpenCV** - Image processing
- **Pillow** - JPEG encode/decode
- **NumPy** - Array operations
- **Pydantic** - Data validation

## Installation

### 1. Create virtual environment

```bash
# From project root (mega-ai/)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Download model (auto-downloaded on first run)

```bash
mkdir -p models
curl -L -o models/blaze_face_short_range.tflite \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
```

### 4. Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

### Data Flow (Per Frame)

```
Frontend (10 FPS)                    Backend Pipeline
┌──────────────┐                 ┌─────────────────────────────┐
│ 320x240 JPEG │                 │ 1. Receive binary frame     │
│  binary blob │ ───WebSocket──► │ 2. JPEG → NumPy (Pillow)    │
│              │                 │ 3. Face detection (MediaPipe)│
│              │                 │ 4. Draw bounding boxes      │
│              │ ◄──WebSocket─── │ 5. NumPy → JPEG (Pillow)    │
│              │                 │ 6. Send binary + ROI JSON   │
└──────────────┘                 └─────────────────────────────┘
```

### Protocol

**Endpoint:** `ws://localhost:8000/ws/video`

| Direction | Format | Content |
|-----------|--------|---------|
| Client → Server | Binary (ArrayBuffer) | JPEG-encoded frame bytes |
| Server → Client | Binary (Blob) | Annotated JPEG with bounding boxes |
| Server → Client | Text (JSON) | ROI/detection metadata |

**ROI JSON Response:**
```json
{
  "frame_id": 42,
  "timestamp": "2026-05-05T10:30:45.123Z",
  "detections": [
    {
      "face_id": "face_42_0",
      "bbox": {"x": 100, "y": 80, "width": 120, "height": 140},
      "confidence": 0.95,
      "landmarks": [
        {"x": 0.45, "y": 0.35, "z": 0.0},
        {"x": 0.55, "y": 0.35, "z": 0.0}
      ]
    }
  ],
  "faces_count": 1
}
```

## Face Detection

### Model: BlazeFace (Short Range)

- Optimized for faces within 0–2 meters
- Provides bounding box + 6 keypoints per face
- ~1–3ms inference on CPU
- Runs via TensorFlow Lite XNNPACK delegate

### Detection Pipeline

1. **Decode** - JPEG bytes → RGB NumPy array (Pillow)
2. **Convert** - RGB → BGR (OpenCV for MediaPipe compatibility)
3. **Detect** - MediaPipe FaceDetector processes frame
4. **Parse** - Extract bboxes, confidence scores, keypoints
5. **Draw** - Render green bounding boxes on frame
6. **Encode** - Annotated frame → JPEG bytes (Pillow)
7. **Send** - Binary frame + JSON metadata via WebSocket

### Performance

| Metric | Value |
|--------|-------|
| Target FPS | 10 |
| Frame resolution | 320×240 |
| Avg inference time | ~5ms |
| End-to-end latency | <100ms |
| Model size | 224 KB |

## File Structure

```
backend/
├── main.py                              # FastAPI app entry point + DI
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Container build
├── Readme.md                            # This file
├── app/
│   ├── models/
│   │   └── detection.py                 # Pydantic schemas
│   ├── services/
│   │   ├── face_detector.py             # MediaPipe BlazeFace (no OpenCV)
│   │   ├── frame_decoder.py             # JPEG → NumPy (Pillow)
│   │   └── frame_encoder.py             # NumPy → JPEG + bbox drawing (Pillow)
│   ├── repository/
│   │   └── face_repository.py           # In-memory + JSON persistence
│   └── routes/
│       ├── video_routes.py              # WebSocket /ws/video handler
│       └── feed_routes.py               # HTTP /feed + /roi endpoints
├── models/
│   └── blaze_face_short_range.tflite    # MediaPipe face detection model
├── data/
│   └── detections.json                  # Persisted detection records
└── __pycache__/
```
backend/
├── main.py                              # FastAPI app entry point + DI
├── requirements.txt                     # Python dependencies
├── Readme.md                            # This file
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── detection.py                 # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── face_detector.py             # MediaPipe BlazeFace integration
│   │   ├── frame_decoder.py             # JPEG → NumPy
│   │   └── frame_encoder.py             # NumPy → JPEG + bbox drawing
│   ├── repository/
│   │   └── face_repository.py           # In-memory + JSON persistence
│   └── routes/
│       └── video_routes.py              # WebSocket endpoint
├── models/
│   └── blaze_face_short_range.tflite    # MediaPipe face detection model
├── data/
│   └── detections.json                  # Persisted detection records
└── __pycache__/
```

## Services

| Module | Class | Responsibility |
|--------|-------|----------------|
| `app/models/detection.py` | Pydantic models | Data validation schemas |
| `app/services/face_detector.py` | `FaceDetector` | MediaPipe BlazeFace detection |
| `app/services/frame_decoder.py` | `FrameDecoder` | JPEG bytes → RGB NumPy array |
| `app/services/frame_encoder.py` | `FrameEncoder` | NumPy → JPEG + draw bboxes |
| `app/repository/face_repository.py` | `FaceRepository` | In-memory + JSON persistence |
| `app/routes/video_routes.py` | Router | WebSocket `/ws/video` handler |

## Endpoints

| Method | Path | Type | Description |
|--------|------|------|-------------|
| WS | `/ws/video` | WebSocket | **Receive** video feed (binary JPEG frames) |
| GET | `/feed` | HTTP (MJPEG) | **Serve** processed video feed with bounding boxes |
| GET | `/roi` | HTTP (JSON) | **Serve** ROI/detection data from repository |
| GET | `/stats` | HTTP (JSON) | Detection statistics |
| GET | `/` | HTTP (JSON) | Health check + API info |

### Endpoint Details

**1. Receive Video (`/ws/video`)** - WebSocket
- Client sends binary JPEG frames at 10 FPS
- Server processes, detects faces, returns annotated frames + ROI JSON

**2. Serve Video (`/feed`)** - MJPEG Stream
- Browser-compatible MJPEG stream
- Use as `<img src="http://localhost:8000/feed" />` to display live annotated video

**3. Serve ROI (`/roi`)** - JSON API
- `GET /roi` returns last 50 detection records
- `GET /roi?limit=100` returns last 100 records

## Repository

The `FaceRepository` stores detection records in-memory with JSON file persistence:

- **Auto-saves** on every new detection record
- **Auto-loads** on server startup
- **Stats endpoint** at `/stats` for monitoring
- **Session tracking** by client IP:port

```python
# Example: get stats
curl http://localhost:8000/stats
# {"total_records": 150, "total_faces_detected": 89, "unique_sessions": 3}
```

## Backpressure Handling

The WebSocket handler checks `bufferedAmount` before sending to avoid flooding slow clients. The frontend implements the same check on its send path.

## Error Handling

| Error | Behavior |
|-------|----------|
| WebSocket disconnect | Clean exit, log session summary |
| Frame decode failure | Skip frame, continue streaming |
| No faces detected | Send original frame + empty detections array |
| MediaPipe init failure | Server won't start (fatal) |

## Docker

```bash
# Build and run
docker compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# MJPEG feed: http://localhost:8000/feed
# ROI data: http://localhost:8000/roi
```

## Troubleshooting

**403 Forbidden on WebSocket:**
```bash
# Make sure venv is activated
source ../.venv/bin/activate
uvicorn main:app --reload
```

**Model not found:**
```bash
ls models/blaze_face_short_range.tflite
# If missing, re-download:
curl -L -o models/blaze_face_short_range.tflite \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
```

**Slow detection:**
- Lower resolution (already at 320×240)
- Reduce FPS from frontend
