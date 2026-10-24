"use client";

import { useEffect } from "react";

export default function WinnerScreen({
  winner = "A",
  winnerName = "Llama",
  isTie = false,
  finalVotes = { A: 0, B: 0, total: 0 },
  roundsBreakdown = [],
  topic = "Debate Topic",
}) {
  useEffect(() => {
    // Trigger confetti if canvas-confetti is loaded
    try {
      import("canvas-confetti").then((confettiModule) => {
        const confetti = confettiModule.default || confettiModule;
        confetti({
          particleCount: 120,
          spread: 80,
          origin: { y: 0.6 },
          colors: ["#a855f7", "#06b6d4", "#f59e0b", "#10b981"],
        });
      }).catch(() => {});
    } catch {
      // Ignored if confetti fails
    }
  }, []);

  return (
    <div className="glass-panel" style={{ padding: "40px", maxWidth: "640px", margin: "0 auto", textAlign: "center" }}>
      <div style={{ fontSize: "3.5rem", marginBottom: "12px" }}>
        {isTie ? "🤝" : "🏆"}
      </div>

      <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "2px", color: "var(--accent-gold)", fontWeight: 800, marginBottom: "6px" }}>
        DEBATE CONCLUDED
      </div>

      <h1 style={{ fontSize: "2.2rem", fontWeight: 900, marginBottom: "8px" }} className="title-gradient">
        {isTie ? "Epic Tie!" : `${winnerName} Wins!`}
      </h1>

      <p style={{ color: "var(--text-muted)", fontSize: "1rem", marginBottom: "32px" }}>
        Topic: &ldquo;{topic}&rdquo;
      </p>

      {/* Final Score Banner */}
      <div
        style={{
          background: "rgba(0, 0, 0, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "var(--radius-lg)",
          padding: "24px",
          marginBottom: "32px",
          display: "flex",
          justifyContent: "space-around",
          alignItems: "center",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.8rem", marginBottom: "4px" }}>🦙</div>
          <div style={{ fontWeight: 800, color: "var(--agent-a)", fontSize: "1.2rem" }}>
            {finalVotes.A} Votes
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
            {finalVotes.total > 0 ? Math.round((finalVotes.A / finalVotes.total) * 100) : 0}% of audience
          </div>
        </div>

        <div style={{ fontSize: "1.8rem", fontWeight: 900, color: "var(--text-dim)" }}>
          :
        </div>

        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.8rem", marginBottom: "4px" }}>🐉</div>
          <div style={{ fontWeight: 800, color: "var(--agent-b)", fontSize: "1.2rem" }}>
            {finalVotes.B} Votes
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
            {finalVotes.total > 0 ? Math.round((finalVotes.B / finalVotes.total) * 100) : 0}% of audience
          </div>
        </div>
      </div>

      {/* Round by Round Breakdown */}
      {roundsBreakdown.length > 0 && (
        <div style={{ marginBottom: "32px", textAlign: "left" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-dim)", marginBottom: "12px" }}>
            Round Breakdown
          </div>
          <div style={{ background: "rgba(15, 23, 42, 0.6)", borderRadius: "var(--radius-md)", overflow: "hidden", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            {roundsBreakdown.map((rb, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "12px 16px",
                  borderBottom: idx !== roundsBreakdown.length - 1 ? "1px solid rgba(255, 255, 255, 0.05)" : "none",
                  fontSize: "0.85rem",
                }}
              >
                <span>
                  <strong>Round {rb.round}</strong> ({rb.label})
                </span>
                <span style={{ fontFamily: "var(--font-mono)" }}>
                  <span style={{ color: "var(--agent-a)" }}>🦙 {rb.A}</span>
                  {"  "}vs{"  "}
                  <span style={{ color: "var(--agent-b)" }}>🐉 {rb.B}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <a
        href="/"
        className="btn-primary"
        style={{ textDecoration: "none", display: "inline-flex", padding: "14px 28px" }}
      >
        ✨ Create Another Debate
      </a>
    </div>
  );
}
