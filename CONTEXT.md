# Domain Model: Face Detection Video Streaming

## Core Concepts

**Video Feed**
A continuous stream of JPEG-encoded frames sent from a client (browser) to the backend via WebSocket. The feed is per-session (one per browser tab).

**Frame**
A single image in the video feed. Exists in multiple representations:
- **Frame (bytes)**: JPEG-encoded bytes received from client
- **Frame (NumPy)**: RGB NumPy array after decoding
- **Frame (PIL)**: PIL Image object for manipulation (drawing, encoding)

**Face Detection**
The process of finding all faces in a frame using MediaPipe. Returns a list of `FaceDetection` objects (zero or more).

**FaceDetection**
A single detected face in a frame. Contains:
- **ROI** (Region of Interest): bounding box as x, y, width, height
- **Confidence**: detection confidence (0–1)
- **Landmarks**: facial keypoints (eyes, nose, etc.), optional
- **Face ID**: unique identifier for this detection (per-frame)

**Frame Analysis**
The result of running detection on a frame. Aggregates all detections in that frame:
- **Frame ID**: frame number in the stream
- **Timestamp**: when the frame was processed
- **Detections**: list of `FaceDetection` objects
- **Faces Count**: number of faces detected (0 or more, assume max 1 per spec)

**Session**
A per-client connection to the backend. Identified by client IP and port (string). One session per browser tab.

**ROI (Region of Interest)**
A bounding box around a detected face. Axis-aligned minimal bounding box (AABB). Stored in database and returned to frontend for drawing.

## Data Flow

1. Client → WebSocket → Frame (bytes) → Backend
2. Backend → Decoder → Frame (NumPy)
3. Frame (NumPy) → Detector → List[FaceDetection]
4. List[FaceDetection] → Frame Analysis (aggregate)
5. Frame Analysis → Repository (persist ROI + metadata)
6. Repository → Database (PostgreSQL)
7. Database → API → Client (JSON: frame ID, ROI, confidence)

## Invariants & Assumptions

- **Single face per frame** (per spec assumption; assume max 1 face in each frame)
- **One session per browser tab** (session ID = IP:port)
- **Detections are ordered by confidence** (highest confidence first, assumed but not enforced)
- **ROI coordinates are frame-relative** (x, y, width, height relative to frame origin)
- **Landmarks are optional** (may be None if detector doesn't provide)
- **Timestamp is ISO 8601 string** (when frame was analyzed, not received)
