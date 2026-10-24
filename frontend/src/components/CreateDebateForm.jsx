"use client";

import { useState } from "react";
import { createDebate } from "../lib/api";

const TONES = [
  { id: "roasting", label: "🔥 Roasting", desc: "Savage wit, sarcasm & burns" },
  { id: "comedic", label: "😂 Comedic", desc: "Stand-up comedy style & punchlines" },
  { id: "aggressive", label: "⚔️ Aggressive", desc: "Fierce attacks & calculated dismantling" },
  { id: "devils_advocate", label: "😈 Devil's Advocate", desc: "Contrarian takes & shocking twists" },
];

const DURATIONS = [
  { label: "1 Min", value: 60 },
  { label: "3 Mins", value: 180 },
  { label: "5 Mins", value: 300 },
];

export default function CreateDebateForm({ onCreated }) {
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [tone, setTone] = useState("roasting");
  const [duration, setDuration] = useState(300);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError("Please enter a debate topic.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await createDebate({
        topic: topic.trim(),
        description: description.trim(),
        tone,
        duration_secs: duration,
      });
      if (onCreated) {
        onCreated(res);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to create debate. Check server connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: "32px", maxWidth: "680px", margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: "28px" }}>
        <h2 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "8px" }} className="title-neon">
          Create AI Debate
        </h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Pit two open-weight AI agents in an audience-powered verbal arena.
        </p>
      </div>

      {error && (
        <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid var(--accent-red)", padding: "12px", borderRadius: "var(--radius-sm)", color: "#fca5a5", marginBottom: "20px", fontSize: "0.9rem" }}>
          {error}
        </div>
      )}

      {/* Topic */}
      <div style={{ marginBottom: "20px" }}>
        <label style={{ display: "block", marginBottom: "8px", fontWeight: 600, fontSize: "0.9rem" }}>
          Debate Topic <span style={{ color: "var(--agent-a)" }}>*</span>
        </label>
        <input
          type="text"
          className="input-field"
          placeholder="e.g. Will AI make software engineers obsolete?"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          maxLength={150}
          required
        />
      </div>

      {/* Description */}
      <div style={{ marginBottom: "20px" }}>
        <label style={{ display: "block", marginBottom: "8px", fontWeight: 600, fontSize: "0.9rem" }}>
          Context / Constraints (optional)
        </label>
        <textarea
          className="input-field"
          style={{ minHeight: "80px", resize: "vertical" }}
          placeholder="e.g. Focus on junior vs senior devs, economic impact, and human creativity."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={300}
        />
      </div>

      {/* Tone Selection */}
      <div style={{ marginBottom: "24px" }}>
        <label style={{ display: "block", marginBottom: "10px", fontWeight: 600, fontSize: "0.9rem" }}>
          Debate Tone
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
          {TONES.map((t) => {
            const isSelected = tone === t.id;
            return (
              <button
                type="button"
                key={t.id}
                onClick={() => setTone(t.id)}
                style={{
                  background: isSelected ? "rgba(168, 85, 247, 0.2)" : "rgba(15, 23, 42, 0.5)",
                  border: isSelected ? "1px solid var(--agent-a)" : "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "var(--radius-md)",
                  padding: "12px 14px",
                  textAlign: "left",
                  cursor: "pointer",
                  color: "var(--text-main)",
                  transition: "all 0.2s ease",
                }}
              >
                <div style={{ fontWeight: 700, fontSize: "0.95rem", marginBottom: "2px" }}>{t.label}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Timer Selection */}
      <div style={{ marginBottom: "28px" }}>
        <label style={{ display: "block", marginBottom: "10px", fontWeight: 600, fontSize: "0.9rem" }}>
          Arena Timer
        </label>
        <div style={{ display: "flex", gap: "12px" }}>
          {DURATIONS.map((d) => (
            <button
              type="button"
              key={d.value}
              onClick={() => setDuration(d.value)}
              style={{
                flex: 1,
                padding: "10px",
                borderRadius: "var(--radius-sm)",
                background: duration === d.value ? "rgba(6, 182, 212, 0.2)" : "rgba(15, 23, 42, 0.4)",
                border: duration === d.value ? "1px solid var(--agent-b)" : "1px solid rgba(255, 255, 255, 0.08)",
                color: duration === d.value ? "var(--agent-b)" : "var(--text-muted)",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              ⏱️ {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* Agent Roster Preview */}
      <div style={{ background: "rgba(0, 0, 0, 0.3)", borderRadius: "var(--radius-md)", padding: "14px", marginBottom: "28px", display: "flex", justifyContent: "space-around", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.4rem" }}>🧠</div>
          <div style={{ fontWeight: 700, color: "var(--agent-a)", fontSize: "0.9rem" }}>GPT-OSS 120B</div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Proponent (FOR)</div>
        </div>
        <div style={{ fontWeight: 900, color: "var(--text-dim)", fontSize: "1.1rem" }}>VS</div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.4rem" }}>🐉</div>
          <div style={{ fontWeight: 700, color: "var(--agent-b)", fontSize: "0.9rem" }}>Qwen 3.8 27B</div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Opponent (AGAINST)</div>
        </div>
      </div>

      <button type="submit" className="btn-primary" style={{ width: "100%", padding: "14px" }} disabled={loading}>
        {loading ? "Generating Arena..." : "Enter The Arena & Get Invite Link 🚀"}
      </button>
    </form>
  );
}
