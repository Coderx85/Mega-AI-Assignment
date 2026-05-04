import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_bytes()
        await websocket.send_bytes(data)


@app.websocket("/upload")
async def websocket_upload(websocket: WebSocket):
    await websocket.accept()
    with open("result.mp4", "wb") as f:
        while True:
            try:
                data = await websocket.receive_bytes()
                f.write(data)
            except Exception:
                # Handle client disconnection
                break


async def event_generator():
    i = 0
    while True:
        # Yield data every second
        yield f"data: This is message {i}\\n\\n"
        i += 1
        await asyncio.sleep(1)

@app.get("/stream")
async def stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
