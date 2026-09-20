import { useCallback, useEffect, useRef, useState } from "react";
import type { TelemetryStreamMessage } from "../types/api";

export type ConnectionState = "connecting" | "open" | "closed";

export function useTelemetryStream(historyLimit = 300) {
  const [latest, setLatest] = useState<TelemetryStreamMessage | null>(null);
  const [history, setHistory] = useState<TelemetryStreamMessage[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  // Lets the dashboard blank all live readouts the instant a run stops or a
  // fresh run starts, so gauges/charts drop to zero instead of freezing on
  // the last frame.
  const clear = useCallback(() => {
    setLatest(null);
    setHistory([]);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let retryTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      if (cancelled) return;
      // Same VITE_API_BASE_URL used for REST calls, converted to a ws(s)://
      // URL. If unset (local dev), fall back to the page's own host, which
      // is what the Vite proxy expects.
      const apiBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
      let url: string;
      if (apiBase) {
        url = apiBase.replace(/^http/, "ws") + "/ws/telemetry";
      } else {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        url = `${protocol}//${window.location.host}/ws/telemetry`;
      }
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setConnectionState("connecting");

      ws.onopen = () => setConnectionState("open");
      ws.onclose = () => {
        setConnectionState("closed");
        // Reconnect after a short delay — the demo shouldn't die just
        // because the backend restarted or the tab was backgrounded.
        retryTimeout = setTimeout(connect, 1500);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (event) => {
        try {
          const message: TelemetryStreamMessage = JSON.parse(event.data);
          setLatest(message);
          setHistory((prev) => {
            const next = [...prev, message];
            return next.length > historyLimit ? next.slice(next.length - historyLimit) : next;
          });
        } catch {
          // Ignore malformed frames rather than crashing the dashboard.
        }
      };
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimeout);
      wsRef.current?.close();
    };
  }, [historyLimit]);

  return { latest, history, connectionState, clear };
}
