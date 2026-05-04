import { useCallback, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useWebSocket } from '../hooks/useWebSocket';
import { useFrameSender } from '../hooks/useFrameSender';
import { useRenderer } from '../hooks/useRenderer';

const WS_URL = 'ws://localhost:8000/ws/video';
const FPS = 10;
const FRAME_WIDTH = 320;
const FRAME_HEIGHT = 240;

function VideoStream() {
  const {
    videoRef,
    canvasRef,
    error: cameraError,
    isActive,
    startCamera,
    stopCamera,
    getFrameAsArrayBuffer,
  } = useCamera({ width: FRAME_WIDTH, height: FRAME_HEIGHT });

  const {
    isConnected,
    error: wsError,
    send,
    onMessage,
  } = useWebSocket(WS_URL);

  const { processedImageUrl, roiData, stats, handleMessage } = useRenderer();

  useEffect(() => {
    return onMessage(handleMessage);
  }, [onMessage, handleMessage]);

  const getFrame = useCallback(() => {
    return getFrameAsArrayBuffer(0.7);
  }, [getFrameAsArrayBuffer]);

  const sendFrame = useCallback(
    (frameBuffer) => {
      return send(frameBuffer);
    },
    [send]
  );

  const { isSending } = useFrameSender({
    getFrame,
    sendFrame,
    fps: FPS,
    enabled: isActive && isConnected,
  });

  const handleToggleStream = async () => {
    if (isActive) {
      stopCamera();
    } else {
      await startCamera();
    }
  };

  return (
    <div className="video-stream">
      <div className="stream-header">
        <h2>Video Stream</h2>
        <div className="status-indicators">
          <span className={`status ${isActive ? 'active' : 'inactive'}`}>
            Camera: {isActive ? 'ON' : 'OFF'}
          </span>
          <span className={`status ${isConnected ? 'active' : 'inactive'}`}>
            WS: {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {isSending && (
            <span className="status sending">Streaming</span>
          )}
        </div>
      </div>

      {(cameraError || wsError) && (
        <div className="error-banner">
          {cameraError && <p>Camera: {cameraError}</p>}
          {wsError && <p>WebSocket: {wsError}</p>}
        </div>
      )}

      <div className="video-grid">
        <div className="video-panel">
          <h3>Live Feed</h3>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="video-element"
          />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        <div className="video-panel">
          <h3>Processed</h3>
          {processedImageUrl ? (
            <img
              src={processedImageUrl}
              alt="Processed frame"
              className="video-element"
            />
          ) : (
            <div className="placeholder">Waiting for processed frames...</div>
          )}
        </div>
      </div>

      {roiData && (
        <div className="roi-panel">
          <h3>ROI / Detection Data</h3>
          <pre>{JSON.stringify(roiData, null, 2)}</pre>
        </div>
      )}

      <div className="stream-controls">
        <button
          onClick={handleToggleStream}
          className={isActive ? 'btn-stop' : 'btn-start'}
        >
          {isActive ? 'Stop Stream' : 'Start Stream'}
        </button>
        <div className="stream-stats">
          <span>FPS: {FPS}</span>
          <span>Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}</span>
          <span>Frames received: {stats.framesReceived}</span>
        </div>
      </div>
    </div>
  );
}

export default VideoStream;
