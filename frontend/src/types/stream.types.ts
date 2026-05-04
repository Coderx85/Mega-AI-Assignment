export type TStream = MediaStream

export type TVideo = HTMLVideoElement

export type TCanvas = HTMLCanvasElement

export type TStreamContext = {
  stream: TStream | null;
  videoRef: React.RefObject<TVideo>;
  canvasRef: React.RefObject<TCanvas>;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
};

export type TRoiRecord = Record<string, unknown>;
