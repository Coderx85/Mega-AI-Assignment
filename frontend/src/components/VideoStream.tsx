import { useState, useCallback, useEffect, useRef } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useWebSocket } from '../hooks/useWebSocket';
import { useFrameSender } from '../hooks/useFrameSender';
import * as Default from "../constants/stream"
import { TStats } from '@types';

function VideoStream() {
  const {
    videoRef,
    canvasRef,
    error: cameraError,
    isActive,
    startCamera,
    stopCamera,
    getFrameAsArrayBuffer,
  } = useCamera({ width: Default.FRAME_WIDTH, height: Default.FRAME_HEIGHT });

  const {
    isConnected,
    error: wsError,
    send,
    onMessage,
  } = useWebSocket({ url: Default.WEBSOCKET_URL });

  const [roiRecords, setRoiRecords] = useState<any[]>([]);
  const [roiError, setRoiError] = useState<string | null>(null);
  const [stats, setStats] = useState<TStats>({ framesReceived: 0, lastFrameTime: null });
  const processedFrameRef = useRef<string | null>(null);
  const roiIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const fetchRoi = async () => {
      try {
        const res = await fetch(`${Default.ROI_URL}?limit=50`);
        if (res.ok) {
          const data = await res.json();
          setRoiRecords(data.records);
          setRoiError(null);
        }
      } catch (err: unknown) {
        console.error('Failed to fetch ROI data:', err);
        setRoiError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    fetchRoi();
    roiIntervalRef.current = setInterval(fetchRoi, 2000);
    return () => {
      if (roiIntervalRef.current) {
        clearInterval(roiIntervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    return onMessage((data) => {
      if (data instanceof Blob || data instanceof ArrayBuffer) {
        const blob = data instanceof ArrayBuffer ? new Blob([data]) : data;
        const url = URL.createObjectURL(blob);
        processedFrameRef.current = url;
        setStats(
          (prev: TStats) => ({
            framesReceived: prev.framesReceived + 1,
            lastFrameTime: new Date().toISOString(),
          })
        );
      }
    });
  }, [onMessage]);

  const getFrame: () => Promise<ArrayBuffer> = useCallback(() => {
    return getFrameAsArrayBuffer(0.7) as Promise<ArrayBuffer>;
  }, [getFrameAsArrayBuffer]);

  const sendFrame = useCallback(
    (frameBuffer: ArrayBuffer) => {
      return send(frameBuffer);
    },
    [send]
  );

  const { isSending } = useFrameSender({
    getFrame,
    sendFrame,
    fps: Default.FPS,
    enabled: isActive && isConnected,
  });

  const handleToggleStream = async () => {
    if (isActive) {
      stopCamera();
    } else {
      await startCamera();
    }
  };

  const latestRoi = roiRecords[0];

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
          <h3>Live Camera</h3>
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
          <h3>Processed (MJPEG Feed)</h3>
          {isActive && isConnected ? (
            <img
              src={Default.FEED_URL}
              alt="Processed video feed"
              className="video-element"
            />
          ) : (
            <div className="placeholder">Start stream to see processed feed</div>
          )}
        </div>
      </div>

      {/* <div className="roi-section"> */}
        {/* <div className="roi-current">
          <h3>Current Detection</h3>
          {latestRoi ? (
            <pre className="roi-json">{JSON.stringify(latestRoi, null, 2)}</pre>
          ) : (
            <p className="roi-empty">No faces detected yet</p>
          )}
        </div> */}

        <div className="roi-history">
          <h3>Detection History ({roiRecords.length})</h3>
          {roiError && <p className="error-text">Failed to load: {roiError}</p>}
          <div className="roi-table-wrapper">
            <table className="roi-table">
              <thead>
                <tr>
                  <th>Frame</th>
                  <th>Faces</th>
                  <th>Confidence</th>
                  <th>BBox (x,y,w,h)</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {roiRecords.map((record: any) => {
                  const d = record?.frame_analysis?.detections?.[0];
                  return (
                    <tr key={record.id}>
                      <td>{record.frame_analysis.frame_id}</td>
                      <td>{record.frame_analysis.faces_count}</td>
                      <td>{d ? d.confidence.toFixed(2) : '-'}</td>
                      <td>
                        {d
                          ? `${d.bbox.x},${d.bbox.y},${d.bbox.width},${d.bbox.height}`
                          : '-'}
                      </td>
                      <td>{new Date(record.created_at).toLocaleTimeString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      {/* </div> */}

      <div className="stream-controls">
        <button
          onClick={handleToggleStream}
          className={isActive ? 'btn-stop' : 'btn-start'}
        >
          {isActive ? 'Stop Stream' : 'Start Stream'}
        </button>
        <div className="stream-stats">
          <span>FPS: {Default.FPS}</span>
          <span>Resolution: {Default.FRAME_WIDTH}x{Default.FRAME_HEIGHT}</span>
          <span>Frames sent: {stats.framesReceived}</span>
        </div>
      </div>
    </div>
  );
}

export default VideoStream;
