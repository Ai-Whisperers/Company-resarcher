"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseWebSocketReturn {
  status: WebSocketStatus;
  lastMessage: any;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    
    // Use relative URL if starting with /
    const wsUrl = url.startsWith("/") 
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}${url}`
      : url;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setStatus("connected");
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setStatus("error");
    };

    ws.onclose = () => {
      setStatus("disconnected");
      console.log("WebSocket disconnected");
      wsRef.current = null;
      
      // Auto reconnect after 3 seconds
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    wsRef.current = ws;
  }, [url]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    clearTimeout(reconnectTimeoutRef.current);
    setStatus("disconnected");
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not connected, cannot send message");
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { status, lastMessage, sendMessage, connect, disconnect };
}
