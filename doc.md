# Face Detection Video Streaming - Architecture & API Documentation

## Overview

This document describes the architecture and interaction between the **frontend** (React) and **backend** (FastAPI) for real-time video streaming with face detection using MediaPipe.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  ┌───────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Camera   │  │   WebSocket  │  │   HTTP Polling     │  │
│  │  Capture  │  │   Upload     │  │   (ROI Data)       │  │
│  └───────────┘  └──────────────┘  └────────────────────┘  │
└────────┬──────────────────────────────────────────┬─────────┘
         │                                          │
         │ 1. JPEG frames via WebSocket             │ 2. HTTP polling for ROI data
         │ ws://localhost:8000/ws/video             │ GET http://localhost:8000/roi
         │                                          │
┌────────▼──────────────────────────────────────────▼─────────┐
│                    Backend (FastAPI)                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  WebSocket Endpoint: /ws/video                     │   │
│  │  • Receive JPEG frames                             │   │
│  │  • Decode → Detect → Draw → Encode                │   │
│  │  • Persist ROI data to database                    │   │
│  │  • Send processed JPEG back to client              │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  HTTP Endpoints:                                   │   │
│  │  • GET /roi - Fetch recent detections              │   │
│  │  • GET /feed - MJPEG stream (multipart)            │   │
│  │  • GET /stats - Repository statistics              │   │
│  │  • GET / - API info                                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Database (SQLite)                                 │   │
│  │  • Stores frame analysis & detection records       │   │
│  │  • Session tracking                                │   │
│  │  • Face ROI & landmarks persistence                │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Endpoints

### 1. **WebSocket: `/ws/video`**

**Purpose:** Real-time video streaming with face detection  
**Protocol:** WebSocket (binary + text frames)  
**Connection:** `ws://localhost:8000/ws/video`

#### Data Flow:
```
Client                          Backend
  │                               │
  ├─ Connect ─────────────────────>│
  │                               │ Accept connection
  │                               │
  ├─ Send JPEG bytes ─────────────>│ Receive & Decode
  │                               │ ↓ Run Face Detection
  │                               │ ↓ Draw Bounding Boxes
  │                               │ ↓ Persist to Database
  │                               │ ↓ Encode to JPEG
  │<────── Processed JPEG ────────┤
  │<────── Frame Analysis JSON ───┤
  │                               │
  ├─ Send JPEG bytes ─────────────>│ (repeat for next frame)
  │                               │
  └─ Close ───────────────────────>│ Cleanup session cache
```

#### Frame Format:

**Request (Client → Server):**
```javascript
// Raw JPEG bytes (ArrayBuffer)
// Size: ~5-20KB per frame (depends on compression)
// Sent at FPS rate (10 FPS = 100ms interval)
```

**Response (Server → Client):**

1. **Binary Frame:** Processed JPEG bytes
   ```
   Content-Type: image/jpeg
   Contains: Original frame with drawn bounding boxes
   ```

2. **Text Frame:** Frame Analysis JSON
   ```json
   {
     "frame_id": 42,
     "timestamp": "2026-05-05T12:34:56.789Z",
     "faces_count": 1,
     "detections": [
       {
         "face_id": "face_a1b2c3d4",
         "bbox": {
           "x": 100,
           "y": 80,
           "width": 150,
           "height": 180
         },
         "confidence": 0.95,
         "landmarks": [
           {"x": 0.35, "y": 0.25, "z": 0.0},
           {"x": 0.65, "y": 0.25, "z": 0.0}
         ]
       }
     ]
   }
   ```

---

### 2. **HTTP GET: `/roi`**

**Purpose:** Fetch recent face detection records  
**Query Parameters:**
- `limit` (integer, default 50): Number of recent records to return

**Request:**
```
GET http://localhost:8000/roi?limit=50
```

**Response:**
```json
{
  "total": 14,
  "records": [
    {
      "id": 123,
      "session_id": "127.0.0.1:54321",
      "frame_id": 150,
      "face_id": "face_a1b2c3d4",
      "bbox": {
        "x": 100,
        "y": 80,
        "width": 150,
        "height": 180
      },
      "confidence": 0.95,
      "keypoints": [...],
      "timestamp": "2026-05-05T12:34:56.789Z",
      "created_at": "2026-05-05T12:34:57.123Z"
    },
    ...
  ]
}
```

---

### 3. **HTTP GET: `/feed`**

**Purpose:** MJPEG stream for viewing processed video feed  
**Query Parameters:**
- `session` (string, optional): Session ID to filter by specific client

**Request:**
```
GET http://localhost:8000/feed
```

**Response:**
```
Content-Type: multipart/x-mixed-replace; boundary=frame

--frame
Content-Type: image/jpeg

[JPEG binary data]
--frame
Content-Type: image/jpeg

[JPEG binary data]
--frame
...
```

This is the standard MJPEG format that can be displayed in an `<img>` tag:
```html
<img src="http://localhost:8000/feed" alt="Processed video feed" />
```

---

### 4. **HTTP GET: `/stats`**

**Purpose:** Get repository statistics  
**Request:**
```
GET http://localhost:8000/stats
```

**Response:**
```json
{
  "total_records": 14,
  "total_faces_detected": 14,
  "unique_sessions": 1
}
```

---

### 5. **HTTP GET: `/`**

**Purpose:** API information and endpoint listing  
**Request:**
```
GET http://localhost:8000/
```

**Response:**
```json
{
  "message": "Face Detection API",
  "status": "ok",
  "endpoints": {
    "ws_receive": "ws://localhost:8000/ws/video",
    "feed_stream": "http://localhost:8000/feed",
    "roi_data": "http://localhost:8000/roi"
  }
}
```

---

## Frontend Architecture

### Components & Hooks

#### **VideoStream.tsx** (Main Component)
- Orchestrates camera capture, WebSocket streaming, and ROI display
- Manages UI state (camera on/off, connection status)
- Displays:
  - Live camera feed
  - Processed video (MJPEG stream)
  - Detection history table

#### **useCamera() Hook**
- Captures frames from browser camera
- Returns frame as JPEG ArrayBuffer
- Quality: 70% compression

#### **useWebSocket() Hook**
- Manages WebSocket connection to backend
- Handles binary (JPEG) and text (JSON) frames
- Provides `send()` and `onMessage()` callbacks

#### **useFrameSender() Hook**
- Sends frames at configurable FPS (default: 10)
- Throttles frame capture to prevent backlog
- Stops when WebSocket disconnects

---

## Sequence Diagram: Full Video Streaming Flow

```
Frontend                        Backend
   │                              │
   │   1. User clicks "Start"     │
   ├─────────────────────────────>│ WebSocket /ws/video
   │   Connect WebSocket          │
   │                              │
   │<─────────────────────────────┤ Accept connection
   │   Connection established     │
   │                              │
   │   2. Start camera capture    │
   └──────────────────────────────┘
   │ (Every 100ms @ 10 FPS)
   │
   │   3. For each frame:         │
   │                              │
   │   a) Capture JPEG            │
   ├─────── Send JPEG ───────────>│
   │                              │
   │                              │ Receive JPEG
   │                              │ ↓ Decode to NumPy
   │                              │ ↓ Run MediaPipe Detection
   │                              │ ↓ Extract face ROI/confidence
   │                              │ ↓ Create FrameAnalysis
   │                              │ ↓ Persist to SQLite
   │                              │
   │                              │ ↓ Draw bounding boxes
   │                              │ ↓ Encode back to JPEG
   │                              │
   │<─────── JPEG bytes ─────────┤
   │ Display in "Processed" video │
   │                              │
   │<─ Frame Analysis JSON ──────┤
   │ Receive detection metadata   │
   │                              │
   │   4. Poll ROI endpoint       │
   ├─── GET /roi?limit=50 ──────>│
   │                              │
   │<── Recent detections JSON ──┤
   │ Update detection history    │
   │ table with latest faces     │
   │                              │
   │   5. Loop until stopped     │
   │                              │
   │   User clicks "Stop"         │
   ├───── WebSocket Close ──────>│
   │                              │
   │                              │ Cleanup session cache
   └──────────────────────────────┘
```

---

## Data Flow Pipeline (Backend)

```
┌────────────────┐
│  JPEG Bytes    │ (from client via WebSocket)
│  (320x240)     │
└────────┬───────┘
         │
         ▼
┌────────────────────────────────┐
│  Frame Decoder                 │
│  • Validate size               │
│  • Decompress JPEG             │
│  • Convert to NumPy RGB array  │
│  Returns: Result[NDArray]      │
└────────┬───────────────────────┘
         │
    ✓ OK │ ✗ Error
         │    └──> Log & Skip
         │
         ▼
┌────────────────────────────────┐
│  Face Detector (MediaPipe)     │
│  • Input: RGB NumPy array      │
│  • Detect faces                │
│  • Extract ROI, landmarks      │
│  • Generate UUID face IDs      │
│  Returns: List[FaceDetection]  │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Frame Analysis                │
│  • Aggregate detections        │
│  • Timestamp frame             │
│  • Create FrameAnalysis object │
└────────┬───────────────────────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌──────────────────┐    ┌──────────────────┐
│  Persistence     │    │  Frame Encoder   │
│  (if faces)      │    │  • Draw bboxes   │
│  • SQLite ORM    │    │  • Encode JPEG   │
│  • Validate bbox │    │  • Add quality   │
│  Returns: Record │    │  Returns: bytes  │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │  Frame Cache     │
         │              │  • Store latest  │
         │              │  • Per-session   │
         └──────────────│  JPEG for MJPEG  │
                        └──────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Send to Client                │
│  • JPEG bytes (processed)      │
│  • Frame Analysis JSON         │
└────────────────────────────────┘
```

---

## Key Concepts

### **Session**
- Unique per browser tab/client connection
- Identified by: `{client_IP}:{client_port}`
- Used for frame caching and tracking

### **Frame ID**
- Sequential counter per session
- Increments with each received frame
- Helps track frame order

### **Face ID**
- UUID-based, unique per face detection
- Format: `face_a1b2c3d4` (hex suffix)
- Regenerated for each frame (no cross-frame linking in current version)

### **ROI (Region of Interest)**
- Bounding box around detected face
- Format: `{x, y, width, height}` in pixels
- Absolute coordinates relative to frame origin

### **Landmarks**
- Facial keypoints (eyes, nose, mouth, etc.)
- Normalized coordinates: 0.0 to 1.0 (relative to frame)
- Z-axis: depth information (0.0 for 2D)

---

## Error Handling

### **Frontend Errors:**
- **Camera access denied:** Show error banner
- **WebSocket connection failed:** Retry, show disconnected status
- **ROI fetch failed:** Display error in table, retry every 2 seconds

### **Backend Errors:**
- **JPEG decode error:** Log warning, skip frame, continue
- **Face detection error:** Log error, skip frame
- **BBox invalid:** Log warning, skip detection
- **Database error:** Log error, attempt reconnect

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Frame rate | 10 FPS |
| Frame resolution | 320x240 px |
| JPEG compression | 70% quality |
| Frame size | ~5-20 KB |
| Detection latency | ~50-100ms per frame |
| ROI polling interval | 2 seconds |
| Max concurrent sessions | Unlimited* |

*Limited by system resources (RAM, CPU)

---

## Configuration

### Frontend (src/constants/stream.ts)
```typescript
export const FRAME_WIDTH = 320;
export const FRAME_HEIGHT = 240;
export const FPS = 10;
export const WEBSOCKET_URL = 'ws://localhost:8000/ws/video';
export const BACKEND_URL = 'http://localhost:8000';
export const ROI_URL = `${BACKEND_URL}/roi`;
export const FEED_URL = `${BACKEND_URL}/feed`;
```

### Backend (backend/app/config.py)
```python
database_url = "sqlite+aiosqlite:///./face_detection.db"
```

### FaceDetector (backend/app/services/face_detector.py)
```python
DEFAULT_MODEL_PATH = "backend/models/blaze_face_short_range.tflite"
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
```

---

## Troubleshooting

### WebSocket Connection Failed
**Symptom:** "WebSocket is closed before connection established"  
**Causes:**
- Backend not running
- CORS misconfiguration
- Wrong URL/port

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/`
2. Check console logs for errors
3. Verify WebSocket URL in `src/constants/stream.ts`

### No Detections Appearing
**Symptom:** ROI table empty, no bounding boxes shown  
**Causes:**
- No faces in camera view
- Confidence threshold too high
- Model not loaded

**Solution:**
1. Check server logs for `detector_initialized`
2. Ensure face is clearly visible
3. Lower confidence threshold

### MJPEG Feed Not Loading
**Symptom:** "Start stream to see processed feed" placeholder  
**Causes:**
- No frames being sent to backend
- WebSocket not connected
- Frame encoding error

**Solution:**
1. Check WebSocket connection status indicator
2. Verify frames are being captured
3. Check backend logs for encode errors

---

## Running the Application

### Start Backend
```bash
cd backend
../. venv/bin/uvicorn main:app --reload
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/video

---

## Technologies

- **Frontend:** React, TypeScript, Vite
- **Backend:** FastAPI, SQLAlchemy, asyncio
- **Database:** SQLite (development) / PostgreSQL (production)
- **Detection:** MediaPipe FaceDetection
- **Logging:** structlog (JSON structured logs)
- **Serialization:** Pydantic, BboxConverter

---

## Future Enhancements

- [ ] Cross-frame face tracking (Face ID persistence)
- [ ] Face recognition/identification
- [ ] Recording video with overlays
- [ ] Real-time metrics dashboard
- [ ] Multiple concurrent streams
- [ ] GPU acceleration support
- [ ] Configurable confidence threshold via UI
