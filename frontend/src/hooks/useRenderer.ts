import { useState, useEffect, useRef, useCallback } from 'react';
import { TRoiData, TStats } from '@types';

type TUrl = string;

export function useRenderer() {
  const [processedImageUrl, setProcessedImageUrl] = useState<TUrl | null>(null);
  const [roiData, setRoiData] = useState<TRoiData>(null);
  const [stats, setStats] = useState<TStats>({ framesReceived: 0, lastFrameTime: null });
  const previousUrlRef = useRef<TUrl | null>(null);

  const renderFrame = useCallback((blob: Blob) => {
    if (previousUrlRef.current) {
      URL.revokeObjectURL(previousUrlRef.current);
    }

    const url = URL.createObjectURL(blob);
    previousUrlRef.current = url;

    setProcessedImageUrl(url);
    setStats(
      (prev: TStats) => ({
        framesReceived: prev.framesReceived + 1,
        lastFrameTime: new Date().toISOString(),
      })
    );
  }, []);

  const renderRoi = useCallback((data: TRoiData) => {
    setRoiData(data);
  }, []);

  const handleMessage = useCallback(
    (data: ArrayBuffer | Blob | string) => {
      if (data instanceof Blob || data instanceof ArrayBuffer) {
        const blob = data instanceof ArrayBuffer ? new Blob([data]) : data;
        renderFrame(blob);
      } else if (typeof data === 'string') {
        try {
          const parsed = JSON.parse(data);
          if (parsed.roi || parsed.bboxes || parsed.detections) {
            renderRoi(parsed);
          }
        } catch {
          // Ignore JSON parsing errors for non-ROI messages
        }
      }
    },
    [renderFrame, renderRoi]
  );

  useEffect(() => {
    return () => {
      if (previousUrlRef.current) {
        URL.revokeObjectURL(previousUrlRef.current);
      }
    };
  }, []);

  return {
    processedImageUrl,
    roiData,
    stats,
    handleMessage,
  };
}
