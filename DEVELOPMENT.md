# Development Guide

## Quick Start (Recommended for Development)

### Local Development (No Docker)

This is the recommended approach for development with hot-reload and fast iteration.

#### Prerequisites
- Python 3.14+
- Node.js 22+
- Camera access (for video capture)

#### Setup

**1. Backend Setup**
```bash
cd backend

# Create virtual environment (if not already done)
python3.14 -m venv ../.venv

# Activate virtual environment
source ../.venv/bin/activate  # On macOS/Linux
# OR
..\.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

**2. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install
# or
pnpm install
```

#### Running

**Terminal 1 - Backend:**
```bash
cd backend
../.venv/bin/uvicorn main:app --reload
```

The backend will:
- Auto-reload on code changes
- Use SQLite database (`backend/face_detection.db`)
- Log to console with structured JSON logs
- Run on `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The frontend will:
- Auto-reload on code changes
- Run on `http://localhost:5173`
- Proxy requests to backend

#### Access
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **WebSocket:** ws://localhost:8000/ws/video

---

## Database Configuration

### Option 1: SQLite (Default - Recommended for Development)

**Already configured!** No setup needed.

```python
# backend/app/config.py
database_url = "sqlite+aiosqlite:///./face_detection.db"
```

**Advantages:**
- ✅ Zero setup
- ✅ File-based (easy backup/sharing)
- ✅ Suitable for single-user development
- ✅ Fast for testing

**File Location:**
```
backend/face_detection.db
```

### Option 2: PostgreSQL (For Advanced Testing)

If you want to test with PostgreSQL locally:

**Start PostgreSQL Container:**
```bash
docker-compose -f docker-compose.dev.yaml up -d postgres
```

**Configure Backend to Use PostgreSQL:**
```bash
cd backend
export APP_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/mydb"
../.venv/bin/uvicorn main:app --reload
```

Or add to `.env` file:
```
APP_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb
```

**Stop PostgreSQL:**
```bash
docker-compose -f docker-compose.dev.yaml down
```

---

## Docker Development Workflow

### Building Docker Images Locally

**Build Backend Image:**
```bash
docker build -t mega-ai-backend:latest ./backend
```

**Build Frontend Image:**
```bash
docker build -t mega-ai-frontend:latest ./frontend
```

### Running with Docker Compose (Full Stack)

**Development Database Only (PostgreSQL):**
```bash
# Start only PostgreSQL for testing
docker-compose -f docker-compose.dev.yaml up -d postgres

# Run backend locally
cd backend
export APP_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/mydb"
../.venv/bin/uvicorn main:app --reload

# Run frontend locally
cd frontend
npm run dev
```

**Production Full Stack (All in Docker):**
```bash
# Start everything
docker-compose up --build

# Stop everything
docker-compose down
```

---

## Environment Variables

### Backend Configuration

Create `backend/.env` file:

```bash
# Database (choose one)
APP_DATABASE_URL=sqlite+aiosqlite:///./face_detection.db
# OR
APP_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb

# Face Detector Model (optional, uses default)
APP_MODEL_PATH=backend/models/blaze_face_short_range.tflite

# Confidence Threshold (0.0-1.0)
APP_CONFIDENCE_THRESHOLD=0.5
```

**Load from Environment:**
```bash
# In terminal before running uvicorn
export APP_DATABASE_URL="sqlite+aiosqlite:///./face_detection.db"
cd backend
../.venv/bin/uvicorn main:app --reload
```

---

## Testing

### Run Tests

```bash
cd backend
../.venv/bin/pytest tests/ -v
```

**Test Coverage:**
- Frame Decoder: 11 tests
- Frame Encoder: 19 tests
- Face ID Generator: 8 tests
- Face Detector (mocked): 15 tests
- BBox Converter: 23 tests

**Total:** 76+ tests (all passing)

### Run Specific Test File
```bash
../.venv/bin/pytest tests/test_frame_decoder.py -v
```

### Run with Coverage Report
```bash
../.venv/bin/pytest tests/ --cov=app --cov-report=html
```

---

## Common Development Tasks

### Adding a New Dependency

**Backend:**
```bash
cd backend
../.venv/bin/pip install <package>
../.venv/bin/pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install <package>
# or
pnpm add <package>
```

### Viewing Database

**SQLite:**
```bash
# Using sqlite3 CLI
sqlite3 backend/face_detection.db

# Common queries
SELECT * FROM face_records LIMIT 10;
SELECT COUNT(*) FROM face_records;
SELECT DISTINCT session_id FROM face_records;
```

**PostgreSQL:**
```bash
# Connect to running container
psql -h localhost -U user -d mydb

# Or via docker
docker-compose -f docker-compose.dev.yaml exec postgres psql -U user -d mydb
```

### Clearing Database

**SQLite:**
```bash
rm backend/face_detection.db
```

**PostgreSQL:**
```bash
docker-compose -f docker-compose.dev.yaml exec postgres psql -U user -d mydb -c "DROP TABLE IF EXISTS face_records; DROP TABLE IF EXISTS sessions;"
```

### Viewing Logs

**Backend (console output):**
```
Already visible in terminal running uvicorn
```

**Backend (JSON logs):**
```bash
# All logs are automatically JSON-formatted
# Parse with jq (optional)
cat logs.json | jq '.level' | sort | uniq -c
```

### Hot-Reload Issues

If hot-reload isn't working:

**Backend:**
```bash
# Restart uvicorn
Ctrl+C
../.venv/bin/uvicorn main:app --reload
```

**Frontend:**
```bash
# Restart Vite
Ctrl+C
npm run dev
```

---

## Debugging

### Enable Debug Logging

**Backend:**
Already using structlog with detailed logs. Logs are JSON-formatted.

```bash
# View logs in real-time
cd backend
../.venv/bin/uvicorn main:app --reload --log-level debug
```

### Browser Console (Frontend)

Press `F12` in browser to open Developer Tools:
- **Console:** JavaScript errors and warnings
- **Network:** WebSocket and HTTP requests/responses
- **Application:** Local storage, cookies

### Check WebSocket Connection

In browser console:
```javascript
// Check if WebSocket is connected
ws.readyState  // 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
```

---

## Performance Tuning

### Backend

**Increase Frame Detection Threshold:**
```python
# backend/app/config.py or environment
CONFIDENCE_THRESHOLD = 0.7  # Default 0.5
```

**Adjust Frame Cache Size:**
```python
# backend/app/services/frame_cache.py
MAX_CACHE_SIZE = 10  # Frames to keep
```

### Frontend

**Reduce Frame Rate:**
```typescript
// frontend/src/constants/stream.ts
export const FPS = 5;  // Default 10
```

**Reduce Frame Resolution:**
```typescript
export const FRAME_WIDTH = 160;   // Default 320
export const FRAME_HEIGHT = 120;  // Default 240
```

---

## Troubleshooting

### Issue: Docker Backend Fails - "libGLESv2.so.2: cannot open shared object file"

**Symptom:**
```
RuntimeError: Failed to initialize FaceDetector: libGLESv2.so.2: cannot open shared object file
```

**Cause:**
MediaPipe requires OpenGL ES libraries which weren't included in the Docker image.

**Solution:**
The Dockerfile has been updated with required graphics libraries:
```dockerfile
RUN apt-get install -y --no-install-recommends \
    libgles2-mesa \
    libegl1-mesa \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb1 \
    libx11-6
```

**How to fix:**
1. Delete old Docker image: `docker rmi mega-ai-backend:latest`
2. Rebuild: `docker-compose up --build`

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:**
```bash
cd backend
export PYTHONPATH=".:$PYTHONPATH"
../.venv/bin/uvicorn main:app --reload
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
../.venv/bin/uvicorn main:app --port 8001 --reload
```

### Issue: WebSocket connection fails

**Check:**
1. Backend running: `curl http://localhost:8000/`
2. Correct URL in frontend: `ws://localhost:8000/ws/video`
3. CORS enabled on backend (already configured)
4. Browser console for errors (F12)

### Issue: "No faces detected"

**Check:**
1. Ensure face is clearly visible in camera
2. Lighting is adequate
3. Check confidence threshold not too high
4. View logs for detector initialization: `detector_initialized`

### Issue: Database locked error

**Solution:**
```bash
# Close other connections
# Restart backend
Ctrl+C
../.venv/bin/uvicorn main:app --reload

# If using SQLite, restart and ensure only one process accesses it
```

---

## Directory Structure During Development

```
backend/
├── app/
│   ├── config.py           # Settings (database URL, etc.)
│   ├── database.py         # SQLAlchemy setup
│   ├── logging.py          # structlog configuration
│   ├── errors.py           # Error types
│   ├── converters/
│   ├── models/
│   ├── services/           # (edit for features)
│   ├── routes/             # (edit for endpoints)
│   └── repository/
├── tests/
│   ├── conftest.py         # pytest configuration
│   └── test_*.py           # (add new tests here)
├── models/
│   └── blaze_face_short_range.tflite
├── face_detection.db       # (auto-generated, safe to delete)
├── main.py                 # (edit if changing app setup)
├── requirements.txt        # (update after pip install)
└── .env                    # (optional, for local config)

frontend/
├── src/
│   ├── components/         # (edit for UI changes)
│   ├── hooks/             # (edit for logic changes)
│   ├── constants/         # (edit for configuration)
│   └── types/
├── public/                 # (static assets)
├── dist/                   # (auto-generated from build)
├── package.json
├── vite.config.js
└── tsconfig.json
```

---

## Using .env File

Create `.env` in project root or `backend/` directory:

```bash
# Backend settings
APP_DATABASE_URL=sqlite+aiosqlite:///./face_detection.db
APP_MODEL_PATH=backend/models/blaze_face_short_range.tflite
APP_CONFIDENCE_THRESHOLD=0.5
```

Backend automatically loads from `.env` via Pydantic settings.

---

## Development Checklist

Before pushing to production:

- [ ] Tests passing: `pytest tests/ -v`
- [ ] No hardcoded paths/credentials
- [ ] Environment variables documented
- [ ] Docker images build: `docker build`
- [ ] docker-compose works: `docker-compose up --build`
- [ ] No console errors (browser F12)
- [ ] No validation warnings from TypeScript/Python
- [ ] Logging configured correctly
- [ ] Error handling in place
- [ ] Documentation updated

---

## Summary

**For Local Development:**
1. ✅ No Docker needed
2. ✅ Use SQLite (zero setup)
3. ✅ Run backend + frontend in separate terminals
4. ✅ Hot-reload on code changes
5. ✅ Fast iteration

**For Testing with PostgreSQL:**
1. Start: `docker-compose -f docker-compose.dev.yaml up -d postgres`
2. Set: `export APP_DATABASE_URL=...`
3. Run backend with PostgreSQL

**For Production:**
1. Use: `docker-compose up --build`
2. All services in containers
3. PostgreSQL database
4. nginx reverse proxy

That's it! Happy coding! 🚀
