"use client";

import CitationCard from "./CitationCard";
import ThinkingIndicator from "./ThinkingIndicator";

export default function AgentPanel({
  agent = "A", // "A" or "B"
  name = "Llama",
  emoji = "🦙",
  model = "llama-3.3-70b-versatile",
  position = "FOR",
  isActive = false,
  isThinking = false,
  currentStreamText = "",
  roundsHistory = [],
  thinkingMessage = "",
}) {
  const isAgentA = agent === "A";
  const primaryColor = isAgentA ? "var(--agent-a)" : "var(--agent-b)";
  const bgGlow = isAgentA ? "var(--agent-a-glow)" : "var(--agent-b-glow)";

  return (
    <div
      className="glass-panel"
      style={{
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        border: isActive ? `2px solid ${primaryColor}` : "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: isActive ? `0 0 30px ${bgGlow}` : "none",
        transition: "all 0.3s ease",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", paddingBottom: "12px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "var(--radius-sm)",
              background: isAgentA ? "rgba(168, 85, 247, 0.2)" : "rgba(6, 182, 212, 0.2)",
              border: `1px solid ${primaryColor}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "1rem",
              color: primaryColor,
            }}
          >
            {agent}
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: "1.2rem", color: primaryColor }}>
              {name}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
              {model}
            </div>
          </div>
        </div>

        <div style={{ textAlign: "right" }}>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 800,
              padding: "4px 10px",
              borderRadius: "var(--radius-full)",
              background: position === "FOR" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
              color: position === "FOR" ? "var(--accent-green)" : "var(--accent-red)",
              border: `1px solid ${position === "FOR" ? "var(--accent-green)" : "var(--accent-red)"}`,
            }}
          >
            {position} TOPIC
          </span>
          {isActive && (
            <div style={{ fontSize: "0.7rem", color: "var(--accent-gold)", fontWeight: 700, marginTop: "4px" }}>
              ● SPEAKING NOW
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Previous Rounds by this agent */}
        {roundsHistory.map((r, idx) => (
          <div
            key={idx}
            style={{
              background: "rgba(15, 23, 42, 0.4)",
              borderRadius: "var(--radius-md)",
              padding: "16px",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: primaryColor, fontWeight: 800, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>
              Round {r.round} — {r.label}
            </div>
            <p style={{ fontSize: "0.95rem", lineHeight: "1.6", whiteSpace: "pre-wrap", color: "var(--text-main)" }}>
              {r.argument}
            </p>

            {/* Citations */}
            {r.citations && r.citations.length > 0 && (
              <div style={{ marginTop: "12px", paddingTop: "8px", borderTop: "1px dashed rgba(255, 255, 255, 0.08)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>
                  Sources & Citations:
                </div>
                {r.citations.map((c, cIdx) => (
                  <CitationCard key={cIdx} index={cIdx + 1} title={c.title} snippet={c.snippet} url={c.url} />
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Live Active Streaming Turn */}
        {isActive && (
          <div
            style={{
              background: "rgba(15, 23, 42, 0.7)",
              borderRadius: "var(--radius-md)",
              padding: "18px",
              border: `1px solid ${primaryColor}`,
              boxShadow: `0 0 20px ${bgGlow}`,
            }}
          >
            {isThinking && (
              <ThinkingIndicator agentName={name} message={thinkingMessage} />
            )}

            {currentStreamText && (
              <div>
                <p style={{ fontSize: "1rem", lineHeight: "1.65", whiteSpace: "pre-wrap", color: "var(--text-main)" }}>
                  {currentStreamText}
                  <span className="typing-cursor" />
                </p>
              </div>
            )}
          </div>
        )}

        {!isActive && roundsHistory.length === 0 && (
          <div style={{ textAlign: "center", color: "var(--text-dim)", margin: "auto", fontSize: "0.9rem" }}>
            Awaiting turn in the debate...
          </div>
        )}
      </div>
    </div>
  );
}
