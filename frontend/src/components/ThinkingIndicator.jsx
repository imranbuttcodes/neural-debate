"use client";

export default function ThinkingIndicator({ agentName = "Agent", message = "Researching sources and formulating argument..." }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "14px",
        background: "rgba(15, 23, 42, 0.7)",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        borderRadius: "var(--radius-md)",
        padding: "12px 18px",
        margin: "12px 0",
      }}
    >
      <div
        style={{
          width: "16px",
          height: "16px",
          border: "2px solid rgba(255, 255, 255, 0.2)",
          borderTopColor: "var(--agent-b)",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <div>
        <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--text-main)" }}>
          {agentName}
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          {message}
        </div>
      </div>
      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
