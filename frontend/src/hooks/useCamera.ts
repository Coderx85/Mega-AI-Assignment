import { useState, useEffect, useRef, useCallback } from 'react';
import { TFrame, TStream, TVideo, TCanvas } from '../types';

type UseCameraProps = {
  width?: number;
  height?: number;
};

export function useCamera(
  { width = 320, height = 240 }: UseCameraProps = {}
){
  const [stream, setStream] = useState<TStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isActive, setIsActive] = useState<boolean>(false);
  const videoRef = useRef<TVideo | null>(null);
  const canvasRef = useRef<TCanvas | null>(null);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: width },
          height: { ideal: height },
        },
        audio: false,
      });
      setStream(mediaStream);
      setIsActive(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Camera access error:', err);
    }
  }, [width, height]);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
      setIsActive(false);
    }
  }, [stream]);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video.readyState < 2) return null;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, width, height);

    return canvas;
  }, [width, height]);

  const getFrameAsArrayBuffer: (quality?: number) => Promise<TFrame | null> = useCallback(
    async (quality = 0.7) => {
      const canvas = captureFrame();
      if (!canvas) return null;

      return new Promise((resolve) => {
        canvas.toBlob(
          async (blob) => {
            if (blob) {
              const buffer = await blob.arrayBuffer();
              resolve(buffer);
            } else {
              resolve(null);
            }
          },
          'image/jpeg',
          quality
        );
      });
    },
    [captureFrame]
  );

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  return {
    videoRef,
    canvasRef,
    stream,
    error,
    isActive,
    startCamera,
    stopCamera,
    getFrameAsArrayBuffer,
  };
}
