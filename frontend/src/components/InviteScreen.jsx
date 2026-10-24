"use client";

import { useState } from "react";
import { startDebate } from "../lib/api";

export default function InviteScreen({ debateData, onDebateStarted }) {
  const [copied, setCopied] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(debateData.invite_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleStart = async () => {
    try {
      setStarting(true);
      setError(null);
      await startDebate(debateData.debate_id, debateData.creator_token);
      if (onDebateStarted) onDebateStarted();
    } catch (err) {
      console.error(err);
      setError("Failed to start debate. Is server online?");
      setStarting(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "36px", maxWidth: "640px", margin: "0 auto", textAlign: "center" }}>
      <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>🎟️</div>
      <h2 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "8px" }} className="title-gradient">
        Arena is Ready!
      </h2>
      <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginBottom: "24px" }}>
        Share this invite link with your audience so they can join, react, and vote live.
      </p>

      {error && (
        <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid var(--accent-red)", padding: "10px", borderRadius: "var(--radius-sm)", color: "#fca5a5", marginBottom: "16px", fontSize: "0.85rem" }}>
          {error}
        </div>
      )}

      {/* Invite Box */}
      <div style={{ background: "rgba(0, 0, 0, 0.4)", border: "1px dashed rgba(255, 255, 255, 0.15)", borderRadius: "var(--radius-md)", padding: "16px", marginBottom: "24px", display: "flex", gap: "10px", alignItems: "center" }}>
        <input
          type="text"
          readOnly
          value={debateData.invite_url}
          style={{ flex: 1, background: "transparent", border: "none", color: "var(--text-main)", fontFamily: "var(--font-mono)", fontSize: "0.85rem", outline: "none" }}
        />
        <button
          onClick={handleCopy}
          style={{
            background: copied ? "var(--accent-green)" : "rgba(255, 255, 255, 0.1)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius-sm)",
            padding: "8px 16px",
            fontSize: "0.85rem",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.2s",
            whiteSpace: "nowrap",
          }}
        >
          {copied ? "✓ Copied!" : "📋 Copy"}
        </button>
      </div>

      {/* Matchup */}
      <div style={{ display: "flex", justifyContent: "center", gap: "24px", marginBottom: "32px", fontSize: "0.9rem" }}>
        <span style={{ color: "var(--agent-a)", fontWeight: 700 }}>🦙 {debateData.agent_a?.name || "Llama"}</span>
        <span style={{ color: "var(--text-dim)" }}>vs</span>
        <span style={{ color: "var(--agent-b)", fontWeight: 700 }}>🐉 {debateData.agent_b?.name || "Qwen"}</span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <button
          onClick={handleStart}
          className="btn-primary"
          style={{ width: "100%", padding: "16px", fontSize: "1.05rem" }}
          disabled={starting}
        >
          {starting ? "Starting Debate..." : "🎬 Start Debate Arena"}
        </button>

        <a
          href={debateData.invite_url}
          target="_blank"
          rel="noreferrer"
          style={{ color: "var(--text-muted)", fontSize: "0.85rem", textDecoration: "none" }}
        >
          Join as viewer in a new tab ↗
        </a>
      </div>
    </div>
  );
}
