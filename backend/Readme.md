# FACE DETECTION Python Backend

## Tech Stacl

- Python 3.8
- Pillow library for image processing.
- Mediapipe library for face detection.

## Installation

1. Make a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Windows:

```bash
venv\Scripts\activate
```
- On macOS/Linux: 

```bash
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python app.py
```

## DataFlow Diagram

1. **API Layer**: We get the image from the frontend as a base64 string using WebSocket layer.

2. **Image Service Layer**: We convert the base64 string to an image format that can be processed. We use the Pillow library for this conversion.

3. **Face Detection Layer**: We use the Mediapipe library to detect faces in the image. The library provides a pre-trained model that can identify facial landmarks and bounding boxes.

4. **Repository Layer**: We store the detected face data (such as bounding box coordinates) in a PostgresSQL database.

5. **Response Layer**: We send the detected face data back to the frontend through the WebSocket connection, allowing the frontend to display the results to the user.

### Endpoints 

1. `/upload`: A WebSocket endpoint that receives the video feed from the frontend as a base64 string, processes it for face detection, and sends the detected face data back to the frontend in real-time.

2. `/video`: An HTTP endpoint that serves the video feed to the frontend, allowing users to view the live video stream.

3. `/roi`: An HTTP endpoint that serves the Region of Interest (ROI) data to the frontend, allowing users to view the detected face regions.

### Services

1. **Image Service**: Responsible for handling image processing tasks, such as converting base64 strings to images and vice versa.

2. **Face Detection Service**: Responsible for using the Mediapipe library to detect faces in the images and extract relevant data.

3. **Database Service**: Responsible for interacting with the PostgreSQL database to store and retrieve detected face data.

### Repositories
1. **Face Repository**: Responsible for managing the storage of detected face data in the database, including creating, reading, updating, and deleting records as necessary.

### File Structure
```backend/
├── app.py
├── requirements.txt
├── services/
│   ├── image_service.py
│   ├── face_detection_service.py
│   └── database_service.py
├── repositories/
│   └── face_repository.py
└── README.md
```
