"use client";

import { useState } from "react";
import { registerViewer } from "../lib/api";

const AVATARS = ["🦊", "🐻", "🦁", "🐯", "🐼", "🐨", "🤖", "👽", "👻", "🦄", "🚀", "🔥", "⚡", "🎯", "👑", "💎"];

export default function JoinLobby({ debateData, onJoined }) {
  const [name, setName] = useState("");
  const [avatar, setAvatar] = useState("🦊");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleJoin = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter your name to enter the arena.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await registerViewer({
        debate_id: debateData.id,
        display_name: name.trim(),
        avatar_emoji: avatar,
      });

      // Save viewer profile to localStorage for auto-reconnect
      if (typeof window !== "undefined") {
        localStorage.setItem(`viewer_${debateData.id}`, JSON.stringify(res));
      }

      if (onJoined) {
        onJoined(res);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to join debate arena. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "36px", maxWidth: "540px", margin: "0 auto", textAlign: "center" }}>
      <div style={{ display: "inline-block", background: "rgba(168, 85, 247, 0.15)", padding: "10px 18px", borderRadius: "var(--radius-full)", marginBottom: "16px", border: "1px solid var(--agent-a-border)", fontSize: "0.85rem", fontWeight: 700, color: "var(--agent-a)" }}>
        🎭 LIVE AI DEBATE ARENA
      </div>

      <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "8px" }} className="title-gradient">
        {debateData.topic}
      </h1>

      {debateData.description && (
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "20px" }}>
          {debateData.description}
        </p>
      )}

      {/* Matchup Tag */}
      <div style={{ background: "rgba(0, 0, 0, 0.35)", borderRadius: "var(--radius-md)", padding: "12px", marginBottom: "28px", display: "flex", justifyContent: "space-around", alignItems: "center" }}>
        <div>
          <span style={{ fontSize: "1.2rem", marginRight: "6px" }}>🦙</span>
          <span style={{ fontWeight: 700, color: "var(--agent-a)" }}>{debateData.agent_a_name || "Llama"}</span>
        </div>
        <span style={{ color: "var(--text-dim)", fontWeight: 900 }}>VS</span>
        <div>
          <span style={{ fontSize: "1.2rem", marginRight: "6px" }}>🐉</span>
          <span style={{ fontWeight: 700, color: "var(--agent-b)" }}>{debateData.agent_b_name || "Qwen"}</span>
        </div>
      </div>

      <form onSubmit={handleJoin}>
        {error && (
          <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid var(--accent-red)", padding: "10px", borderRadius: "var(--radius-sm)", color: "#fca5a5", marginBottom: "16px", fontSize: "0.85rem" }}>
            {error}
          </div>
        )}

        {/* Name input */}
        <div style={{ marginBottom: "20px", textAlign: "left" }}>
          <label style={{ display: "block", marginBottom: "6px", fontWeight: 600, fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Your Display Name
          </label>
          <input
            type="text"
            className="input-field"
            placeholder="e.g. Ali or Sarah"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={25}
            required
          />
        </div>

        {/* Emoji Avatar picker */}
        <div style={{ marginBottom: "28px", textAlign: "left" }}>
          <label style={{ display: "block", marginBottom: "8px", fontWeight: 600, fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Choose Your Avatar
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gap: "8px" }}>
            {AVATARS.map((emoji) => (
              <button
                type="button"
                key={emoji}
                onClick={() => setAvatar(emoji)}
                style={{
                  fontSize: "1.4rem",
                  padding: "8px",
                  borderRadius: "var(--radius-sm)",
                  background: avatar === emoji ? "rgba(168, 85, 247, 0.3)" : "rgba(15, 23, 42, 0.6)",
                  border: avatar === emoji ? "2px solid var(--agent-a)" : "1px solid rgba(255, 255, 255, 0.08)",
                  cursor: "pointer",
                  transition: "transform 0.15s, background 0.15s",
                  transform: avatar === emoji ? "scale(1.15)" : "scale(1)",
                }}
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>

        <button type="submit" className="btn-primary" style={{ width: "100%", padding: "14px" }} disabled={loading}>
          {loading ? "Entering..." : `Join as ${avatar} ${name.trim() || "Viewer"}`}
        </button>
      </form>
    </div>
  );
}
