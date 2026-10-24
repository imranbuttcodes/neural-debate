"use client";

export default function RoundBadge({ round = 1, label = "Opening", agentName = "Debater" }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "10px",
        background: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "var(--radius-full)",
        padding: "6px 20px",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4)",
      }}
    >
      <span style={{ fontWeight: 800, fontSize: "0.95rem", letterSpacing: "0.5px" }}>
        Round {round} — {label}
      </span>
      <span style={{ width: "4px", height: "4px", borderRadius: "50%", background: "var(--text-dim)" }} />
      <span style={{ color: "var(--agent-b)", fontWeight: 700, fontSize: "0.85rem" }}>
        {agentName}&apos;s Turn
      </span>
    </div>
  );
}
