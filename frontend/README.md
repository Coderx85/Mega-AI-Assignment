# Face Detection React Frontend 

## Tech Stack

- React ( using Vite )
- WebSocket for real-time communication with the backend.

## Installation

1. Move to the frontend directory:

```bash
cd frontend
```

2. Install the required dependencies:

```bash
pnpm install
```

3. Run the application:

```bash
pnpm run dev
```

## DataFlow Diagram
- Real time frame processing using WebSocket and rendering the detected face data from the backend on the frontend using React components.

1. **WebSocket Connection**: The frontend establishes a WebSocket connection with the backend to send images and receive detected face data in real-time.
2. **Image Capture**: The frontend captures images from the user's webcam, converts them to base64 strings, and sends them to the backend through the WebSocket connection.
3. **Data Reception**: The frontend listens for incoming messages from the backend, which contain the detected face data (such as bounding box coordinates).
4. **Rendering**: The frontend uses React components to render the detected face data on the screen, allowing users to see the results in real-time.

### Modules
1. **WebSocket Module**: Responsible for managing the WebSocket connection, sending images to the backend, and receiving detected face data.
2. **Image Capture Module**: Responsible for capturing images from the user's webcam and converting them to base64 strings for transmission to the backend.
3. **Rendering Module**: Responsible for rendering the detected face data on the screen using React components, allowing users to visualize the results in real-time.