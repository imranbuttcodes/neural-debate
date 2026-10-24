const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

/**
 * Creates a managed WebSocket connection to a debate room.
 * Handles auto-reconnect, JSON parsing, and cleanup.
 */
export function connectDebateWS(debateId, viewerId, { onMessage, onOpen, onClose, onError }) {
  let ws = null;
  let isManuallyClosed = false;
  let reconnectTimeout = null;
  let pingInterval = null;

  function connect() {
    if (isManuallyClosed) return;

    const query = viewerId ? `?viewer_id=${encodeURIComponent(viewerId)}` : "";
    const url = `${WS_BASE}/ws/debates/${debateId}${query}`;

    ws = new WebSocket(url);

    ws.onopen = () => {
      if (onOpen) onOpen();
      // Start ping heartbeat every 15s to keep connection alive
      pingInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 15000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "pong") return;
        if (onMessage) onMessage(data);
      } catch (err) {
        console.error("Failed to parse WS message:", err, event.data);
      }
    };

    ws.onerror = (err) => {
      if (onError) onError(err);
    };

    ws.onclose = () => {
      clearInterval(pingInterval);
      if (onClose) onClose();
      if (!isManuallyClosed) {
        // Auto-reconnect after 2 seconds
        reconnectTimeout = setTimeout(connect, 2000);
      }
    };
  }

  connect();

  return {
    send: (msg) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(typeof msg === "string" ? msg : JSON.stringify(msg));
      }
    },
    close: () => {
      isManuallyClosed = true;
      clearInterval(pingInterval);
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    },
  };
}
