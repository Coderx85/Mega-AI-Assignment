export type TFrame = ArrayBuffer;

export type TRoiData = Record<string, unknown> | null;

export interface TStats {
  framesReceived: number;
  lastFrameTime: string | null;
};

export type TUseRenderer = {
  processedImageUrl: string | null;
  roiData: TRoiData;
  stats: TStats;
};

export type TUseCamera = {
  stream: MediaStream | null;
  error: string | null;
  isActive: boolean;
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
  captureFrame: () => HTMLCanvasElement | null;
  getFrameAsArrayBuffer: (quality?: number) => Promise<ArrayBuffer | null>;
};

export type TUseWebSocket = {
  isConnected: boolean;
  error: string | null;
  send: (data: ArrayBuffer) => boolean;
  onMessage: (handler: (data: ArrayBuffer) => void) => () => void;
};