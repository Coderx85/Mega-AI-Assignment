# Face Detection Video Streaming

A real-time video streaming application with face detection using MediaPipe. Stream live video from your camera, detect faces, draw bounding boxes, and persist detection data.

## ✨ Features

- **Real-time Video Streaming:** WebSocket-based frame transmission (10 FPS)
- **Face Detection:** MediaPipe-powered with 95%+ confidence
- **ROI Drawing:** Axis-aligned bounding boxes (without OpenCV, using PIL)
- **Data Persistence:** SQLite (dev) / PostgreSQL (prod)
- **MJPEG Feed:** View processed stream with drawn bounding boxes
- **ROI API:** Query detection history via REST API
- **Structured Logging:** JSON-formatted logs for debugging
- **Docker Ready:** Containerized backend & frontend
- **Type Safe:** Python type hints + TypeScript

## 🏗️ Architecture

```
Frontend (React + TypeScript)
        ↓ WebSocket (JPEG frames)
Backend (FastAPI)
        ├─ Frame Decoder (JPEG → NumPy)
        ├─ Face Detector (MediaPipe)
        ├─ ROI Drawer (PIL)
        ├─ Frame Encoder (NumPy → JPEG)
        └─ Database (SQLite/PostgreSQL)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.14+
- Node.js 22+
- Camera access

## Running the Application (using Docker)

1. Build and run the full stack:

```bash
docker-compose up --build
```

2. Access the application:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/video`


### Local Development (Recommended)

**Backend - Terminal 1:**
```bash
cd backend
../.venv/bin/uvicorn main:app --reload
```

**Frontend - Terminal 2:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/video

## 📦 Installation

### Backend Setup
```bash
cd backend
python3.14 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
# or
pnpm install
```

## 🐳 Docker Deployment

### Production (Full Stack)
```bash
docker-compose up --build
```

### Development Database Only
```bash
docker-compose -f docker-compose.dev.yaml up -d postgres
export APP_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/mydb"
cd backend && ../.venv/bin/uvicorn main:app --reload
```

## 🔧 Configuration

### Environment Variables

Create `backend/.env`:
```bash
APP_DATABASE_URL=sqlite+aiosqlite:///./face_detection.db
APP_MODEL_PATH=backend/models/blaze_face_short_range.tflite
APP_CONFIDENCE_THRESHOLD=0.5
```

### Database Options
- **SQLite (Default):** Zero setup, perfect for development
- **PostgreSQL:** Use with `docker-compose.dev.yaml`

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[doc.md](./doc.md)** | API endpoints, sequence diagrams, architecture |
| **[DEVELOPMENT.md](./DEVELOPMENT.md)** | Development workflow, troubleshooting, tasks |
| **[COMPLETION_STATUS.md](./COMPLETION_STATUS.md)** | Assignment checklist, compliance matrix |
| **[CONTEXT.md](./CONTEXT.md)** | Domain model glossary |

## 🧪 Testing

```bash
cd backend
../.venv/bin/pytest tests/ -v
```

**Test Coverage:**
- Frame Decoder: 11 tests ✅
- Frame Encoder: 19 tests ✅
- Face ID Generator: 8 tests ✅
- Face Detector: 15 tests ✅
- BBox Converter: 23 tests ✅

**Total:** 76+ passing tests

## 📋 API Endpoints

### WebSocket
- **`ws://localhost:8000/ws/video`** - Real-time video streaming with face detection

### HTTP
- **`GET /feed`** - MJPEG stream
- **`GET /roi?limit=50`** - Recent detection records (JSON)
- **`GET /stats`** - Repository statistics
- **`GET /`** - API information

See [doc.md](./doc.md) for detailed endpoint documentation.

## 🛠️ Technologies

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, SQLAlchemy, asyncio |
| Frontend | React, TypeScript, Vite |
| Detection | MediaPipe FaceDetection |
| Image Processing | PIL (Pillow) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Containerization | Docker, docker-compose |
| Logging | structlog (JSON) |

## 📁 Project Structure

```
mega-ai/
├── backend/
│   ├── app/
│   │   ├── services/          # FrameDecoder, FaceDetector, FrameEncoder
│   │   ├── routes/            # WebSocket & HTTP endpoints
│   │   ├── repository/        # Database persistence
│   │   └── converters/        # BBox serialization
│   ├── models/                # MediaPipe TFLite model
│   ├── tests/                 # 76+ unit tests
│   └── main.py                # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # useCamera, useWebSocket, useFrameSender
│   │   └── constants/         # Configuration
│   └── index.html
├── docker-compose.yml         # Production stack
├── docker-compose.dev.yaml    # Development database
└── [Documentation files]
```

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Frame Rate | 10 FPS |
| Resolution | 320x240 px |
| JPEG Quality | 70% |
| Detection Latency | ~50-100ms |
| Max Concurrent Sessions | Unlimited* |

*Limited by system resources

## 🐛 Troubleshooting

### WebSocket Connection Failed
```bash
# Verify backend is running
curl http://localhost:8000/

# Check frontend URL in src/constants/stream.ts
cat frontend/src/constants/stream.ts | grep WEBSOCKET_URL
```

### Port Already in Use
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

### Database Issues
```bash
# Reset SQLite database
rm backend/face_detection.db

# Reset PostgreSQL
docker-compose -f docker-compose.dev.yaml down -v
docker-compose -f docker-compose.dev.yaml up -d postgres
```

See [DEVELOPMENT.md](./DEVELOPMENT.md) for more troubleshooting tips.

## 📈 Development Workflow

### Add a New Backend Feature
1. Create service in `backend/app/services/`
2. Add tests in `backend/tests/`
3. Run: `pytest tests/ -v`
4. Update documentation if needed
5. Commit with clear message

### Add a New Frontend Feature
1. Create component in `frontend/src/components/`
2. Add types in `frontend/src/types/`
3. Test in browser: http://localhost:5173
4. Update documentation if needed
5. Commit with clear message

## ✅ Checklist Before Production

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Docker images build: `docker build ./backend`
- [ ] docker-compose works: `docker-compose up --build`
- [ ] No hardcoded credentials
- [ ] Environment variables documented
- [ ] Error handling in place
- [ ] Logging configured
- [ ] Documentation updated

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Run tests: `cd backend && ../.venv/bin/pytest tests/ -v`
4. Commit with clear message: `git commit -m "feat: add feature"`
5. Push and create pull request

## 📝 License

[Add your license here]

## 📞 Support

For issues and questions:
1. Check [DEVELOPMENT.md](./DEVELOPMENT.md) troubleshooting section
2. Review [doc.md](./doc.md) for architecture details
3. Check backend logs: `cat backend/logs.json | jq`

---

**Ready to get started?** See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed setup instructions! 🚀
