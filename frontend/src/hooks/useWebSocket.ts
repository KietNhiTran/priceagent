import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentStep,
  AgentTrace,
  ChatMessage,
  WsMessage,
} from "../types";

interface UseWebSocketReturn {
  connected: boolean;
  messages: ChatMessage[];
  steps: AgentStep[];
  currentTrace: AgentTrace | null;
  sendMessage: (text: string) => void;
  clearHistory: () => void;
}

const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/chat`;

let msgCounter = 0;
function nextId(): string {
  return `msg-${Date.now()}-${++msgCounter}`;
}

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const shouldReconnect = useRef(true);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [currentTrace, setCurrentTrace] = useState<AgentTrace | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log("[WS] connected");
    };

    ws.onclose = () => {
      setConnected(false);
      if (!shouldReconnect.current) return;
      console.log("[WS] disconnected – reconnecting in 3s");
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = (e) => {
      console.error("[WS] error", e);
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const data: WsMessage = JSON.parse(event.data);

        switch (data.type) {
          case "welcome":
            setMessages((prev) => [
              ...prev,
              {
                id: nextId(),
                role: "system",
                content: data.message,
                timestamp: new Date(),
              },
            ]);
            break;

          case "agent_step":
            setSteps((prev) => {
              const idx = prev.findIndex(
                (s) => s.step_id === data.step.step_id
              );
              if (idx >= 0) {
                const updated = [...prev];
                updated[idx] = data.step;
                return updated;
              }
              return [...prev, data.step];
            });
            break;

          case "chat_message":
            setMessages((prev) => [
              ...prev,
              {
                id: nextId(),
                role: "assistant",
                content: data.message,
                timestamp: new Date(),
                decision: data.decision,
                beat_price: data.beat_price,
                trace_id: data.trace_id,
              },
            ]);
            break;

          case "trace_complete":
            setCurrentTrace(data.trace);
            break;

          case "error":
            setMessages((prev) => [
              ...prev,
              {
                id: nextId(),
                role: "system",
                content: `⚠️ ${data.message}`,
                timestamp: new Date(),
              },
            ]);
            break;
        }
      } catch {
        console.warn("[WS] failed to parse message", event.data);
      }
    };
  }, []);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      // Add user message locally
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", content: text, timestamp: new Date() },
      ]);

      // Reset steps for new request
      setSteps([]);
      setCurrentTrace(null);

      wsRef.current.send(JSON.stringify({ message: text }));
    },
    []
  );

  const clearHistory = useCallback(() => {
    setMessages([]);
    setSteps([]);
    setCurrentTrace(null);
  }, []);

  return { connected, messages, steps, currentTrace, sendMessage, clearHistory };
}
