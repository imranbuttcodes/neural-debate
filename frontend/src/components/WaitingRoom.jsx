"use client";

export default function WaitingRoom({ debateData, viewer, totalViewers }) {
  return (
    <div className="glass-panel" style={{ padding: "48px 32px", maxWidth: "560px", margin: "0 auto", textAlign: "center" }}>
      <div style={{ fontSize: "3rem", marginBottom: "16px", animation: "pulse-glow 2s infinite" }}>
        🎭
      </div>

      <h2 style={{ fontSize: "1.7rem", fontWeight: 800, marginBottom: "8px" }} className="title-neon">
        Waiting for Creator to Start...
      </h2>

      <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginBottom: "28px" }}>
        Grab your popcorn! The verbal battle will begin shortly.
      </p>

      {/* Viewer Card */}
      <div style={{ display: "inline-flex", alignItems: "center", gap: "12px", background: "rgba(15, 23, 42, 0.7)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "var(--radius-full)", padding: "8px 20px", marginBottom: "32px" }}>
        <span style={{ fontSize: "1.6rem" }}>{viewer?.avatar_emoji || "🦊"}</span>
        <span style={{ fontWeight: 700, fontSize: "1.05rem" }}>{viewer?.display_name || "Viewer"}</span>
        <span style={{ fontSize: "0.75rem", background: "rgba(16, 185, 129, 0.2)", color: "var(--accent-green)", padding: "2px 8px", borderRadius: "var(--radius-full)", fontWeight: 700 }}>
          READY
        </span>
      </div>

      {/* Topic Card */}
      <div style={{ background: "rgba(0, 0, 0, 0.35)", borderRadius: "var(--radius-md)", padding: "18px", textAlign: "left", marginBottom: "24px" }}>
        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>
          TOPIC
        </div>
        <div style={{ fontWeight: 700, fontSize: "1.1rem", marginBottom: "12px" }}>
          {debateData.topic}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "var(--text-muted)" }}>
          <span>Tone: <strong style={{ color: "var(--text-main)" }}>{debateData.tone}</strong></span>
          <span>Duration: <strong style={{ color: "var(--text-main)" }}>{Math.round(debateData.duration_secs / 60)}m</strong></span>
        </div>
      </div>

      <div style={{ color: "var(--text-dim)", fontSize: "0.85rem" }}>
        👥 <strong>{totalViewers || 1}</strong> viewers connected in the arena lobby
      </div>
    </div>
  );
}
