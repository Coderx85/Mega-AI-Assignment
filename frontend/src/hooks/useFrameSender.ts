import { useRef, useEffect, useCallback } from 'react';
import { TFrame } from '../types/frame.types';

type UseFrameSenderProps = {
  getFrame: () => Promise<TFrame>;
  sendFrame: (frame: TFrame) => void;
  fps?: number;
  enabled?: boolean;
};

export function useFrameSender({ 
  getFrame, 
  sendFrame, 
  fps = 10, 
  enabled = false
}: UseFrameSenderProps) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const enabledRef = useRef<boolean>(enabled);
  const getFrameRef = useRef<() => Promise<TFrame>>(getFrame);
  const sendFrameRef = useRef<(frame: TFrame) => void>(sendFrame);
  const isProcessingRef = useRef<boolean>(false);

  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  useEffect(() => {
    getFrameRef.current = getFrame;
  }, [getFrame]);

  useEffect(() => {
    sendFrameRef.current = sendFrame;
  }, [sendFrame]);

  useEffect(() => {
    if (!enabled) return;

    const intervalMs = 1000 / fps;

    const captureAndSend = async () => {
      if (isProcessingRef.current) return;
      if (!enabledRef.current) return;

      isProcessingRef.current = true;

      try {
        const frame = await getFrameRef.current();
        if (frame !== null && enabledRef.current) {
          sendFrameRef.current(frame);
        }
      } catch (err) {
        console.error('[FrameSender] Capture error:', err);
      } finally {
        isProcessingRef.current = false;
      }
    };

    intervalRef.current = setInterval(captureAndSend, intervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, fps]);

  return { isSending: enabled };
}
