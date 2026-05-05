FROM python:3.14

WORKDIR /app

# Install system dependencies for MediaPipe and graphics rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglvnd0 \
    libglvnd-dev \
    libglx0 \
    libopengl0 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment to use CPU for MediaPipe
ENV MEDIAPIPE_DISABLE_GPU=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p models && \
    curl -sL -o models/blaze_face_short_range.tflite \
    "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"

RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
