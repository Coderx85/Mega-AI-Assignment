# Real-Time Face Detection Backend

## Tech Stack

- **Python 3.14**
- **FastAPI** - Async web framework
- **MediaPipe 0.10** - Face detection (BlazeFace model)
- **Pillow** - JPEG encode/decode (no OpenCV)
- **NumPy** - Array operations
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL 14** - Detection data storage
- **Pydantic** - Data validation

## Installation

### 1. Create virtual environment

```bash
# From project root (mega-ai/)
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start PostgreSQL (Docker)

```bash
docker compose -f docker-compose.dev.yaml up -d database
```

### 4. Download model

```bash
mkdir -p models
curl -L -o models/blaze_face_short_range.tflite \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
```

### 5. Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Tables are auto-created on startup.

## Architecture

### Data Flow

```
Frontend                          Backend Pipeline
┌──────────────┐              ┌─────────────────────────────┐
│ 320x240 JPEG │              │ 1. Receive binary frame     │
│  binary blob │ ──WS────►    │ 2. JPEG → NumPy (Pillow)    │
│              │              │ 3. Face detection (MediaPipe)│
│              │              │ 4. Draw bounding boxes       │
│              │ ◄──WS─────── │ 5. NumPy → JPEG (Pillow)    │
│              │              │ 6. Store ROI in PostgreSQL   │
│              │              │ 7. Send binary + ROI JSON    │
└──────────────┘              └─────────────────────────────┘
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
      "landmarks": [{"x": 0.45, "y": 0.35, "z": 0.0}]
    }
  ],
  "faces_count": 1
}
```

## File Structure

```
backend/
├── main.py                              # FastAPI app entry + lifespan
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Container build
├── Readme.md                            # This file
├── app/
│   ├── __init__.py
│   ├── config.py                        # Pydantic settings (DB URL)
│   ├── database.py                      # Async engine + session factory
│   ├── models/
│   │   ├── detection.py                 # Pydantic response schemas
│   │   └── schema.py                    # SQLAlchemy ORM models
│   ├── services/
│   │   ├── face_detector.py             # MediaPipe BlazeFace
│   │   ├── frame_decoder.py             # JPEG → NumPy
│   │   └── frame_encoder.py             # NumPy → JPEG + bbox drawing
│   ├── repository/
│   │   └── face_repository.py           # PostgreSQL CRUD operations
│   └── routes/
│       ├── video_routes.py              # WebSocket /ws/video
│       └── feed_routes.py               # HTTP /feed + /roi
├── models/
│   └── blaze_face_short_range.tflite    # MediaPipe model (224KB)
└── __pycache__/
```

## Database Schema

**Table:** `face_detections`

| Column | Type | Description |
|--------|------|-------------|
| `id` | String (PK) | Unique record ID (UUID) |
| `session_id` | String (idx) | Client session (IP:port) |
| `frame_id` | Integer | Sequential frame counter |
| `face_id` | String | Detection identifier |
| `bbox_x`, `bbox_y` | Integer | Bounding box origin |
| `bbox_width`, `bbox_height` | Integer | Bounding box dimensions |
| `confidence` | Float | Detection confidence (0-1) |
| `keypoints` | JSON | Facial landmark coordinates |
| `timestamp` | DateTime | Detection time |
| `created_at` | DateTime | Record insertion time |

## Endpoints

| Method | Path | Type | Description |
|--------|------|------|-------------|
| WS | `/ws/video` | WebSocket | Receive video feed, return processed frames + ROI |
| GET | `/feed` | HTTP (MJPEG) | Serve live annotated video stream |
| GET | `/roi` | HTTP (JSON) | Serve detection records from PostgreSQL |
| GET | `/stats` | HTTP (JSON) | Detection statistics |
| GET | `/` | HTTP (JSON) | Health check |

### ROI Endpoint

```bash
GET /roi?limit=50
```

Returns recent detection records with bounding box data.

## Services

| Module | Class | Responsibility |
|--------|-------|----------------|
| `app/config.py` | `Settings` | Environment-based DB URL config |
| `app/database.py` | - | Async engine, session management |
| `app/models/schema.py` | `FaceDetectionRecord` | SQLAlchemy ORM table definition |
| `app/repository/face_repository.py` | `FaceRepository` | Async PostgreSQL CRUD |
| `app/services/face_detector.py` | `FaceDetector` | MediaPipe BlazeFace detection |
| `app/services/frame_decoder.py` | `FrameDecoder` | JPEG → NumPy (Pillow) |
| `app/services/frame_encoder.py` | `FrameEncoder` | NumPy → JPEG + bbox (Pillow) |

## Docker

```bash
# Dev: backend + PostgreSQL
docker compose -f docker-compose.dev.yaml up --build

# Prod: backend + frontend + PostgreSQL
docker compose up --build
```

## Configuration

Environment variables (prefix `APP_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/mydb` | Async PostgreSQL connection string |
