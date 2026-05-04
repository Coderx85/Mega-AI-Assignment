import { useState, useEffect, useRef, useCallback } from 'react';

type UseWebSocketProps = {
  url: string;
  options?: {
    backpressureThreshold?: number;
  };
}

export function useWebSocket({ url, options = {} }: UseWebSocketProps) {
  const {
    backpressureThreshold = 1024 * 1024,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messageHandlersRef = useRef<((data: ArrayBuffer) => void)[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('WebSocket connected');
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = () => {
      setError('WebSocket error');
      setIsConnected(false);
    };

    ws.onmessage = (event) => {
      messageHandlersRef.current.forEach((handler) => handler(event.data));
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [url]);

  const send = useCallback(
    (data: ArrayBuffer) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return false;
      }

      if (wsRef.current.bufferedAmount > backpressureThreshold) {
        return false;
      }

      wsRef.current.send(data);
      return true;
    },
    [backpressureThreshold]
  );

  const onMessage = useCallback((handler: (data: ArrayBuffer) => void) => {
    messageHandlersRef.current.push(handler);
    return () => {
      messageHandlersRef.current = messageHandlersRef.current.filter(
        (h) => h !== handler
      );
    };
  }, []);

  return {
    isConnected,
    error,
    send,
    onMessage,
  };
}
