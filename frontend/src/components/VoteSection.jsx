"use client";

import { useState } from "react";
import { submitVote } from "../lib/api";
import LiveVoteBar from "./LiveVoteBar";

export default function VoteSection({
  debateId,
  viewerId,
  currentVote,
  onVoteChanged,
  voteCounts,
  agentAName = "Llama",
  agentBName = "Qwen",
  isVotingOpen = true,
}) {
  const [loadingVote, setLoadingVote] = useState(null);

  const handleVote = async (choice) => {
    if (!viewerId) return;
    try {
      setLoadingVote(choice);
      await submitVote({
        debate_id: debateId,
        vote: choice,
        viewer_id: viewerId,
      });
      if (onVoteChanged) onVoteChanged(choice);
    } catch (err) {
      console.error("Failed to submit vote:", err);
    } finally {
      setLoadingVote(null);
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: "20px 24px",
        margin: "20px 0",
        border: "1px solid rgba(255, 255, 255, 0.12)",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: "8px" }}>
        <span
          style={{
            fontSize: "0.85rem",
            fontWeight: 800,
            textTransform: "uppercase",
            letterSpacing: "1px",
            color: isVotingOpen ? "var(--accent-gold)" : "var(--text-dim)",
          }}
        >
          {isVotingOpen ? "Live Audience Voting — Cast or Switch Anytime" : "Votes Locked"}
        </span>
      </div>

      {/* Animated Live Bar */}
      <LiveVoteBar
        votes={voteCounts}
        agentAName={agentAName}
        agentBName={agentBName}
      />

      {/* Vote Action Buttons */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px" }}>
        {/* Vote Agent A */}
        <button
          type="button"
          onClick={() => handleVote("A")}
          disabled={loadingVote !== null}
          style={{
            background: currentVote === "A" ? "rgba(168, 85, 247, 0.3)" : "rgba(15, 23, 42, 0.6)",
            border: currentVote === "A" ? "2px solid var(--agent-a)" : "1px solid var(--agent-a-border)",
            borderRadius: "var(--radius-md)",
            padding: "14px",
            cursor: "pointer",
            color: "var(--text-main)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
            transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: currentVote === "A" ? "0 0 20px var(--agent-a-glow)" : "none",
            transform: currentVote === "A" ? "scale(1.02)" : "scale(1)",
          }}
        >
          <span style={{ fontWeight: 800, fontSize: "1.05rem", color: "var(--agent-a)" }}>
            Vote {agentAName}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {currentVote === "A" ? "✓ Your Current Vote" : "Tap to vote or switch"}
          </span>
        </button>

        {/* Vote Agent B */}
        <button
          type="button"
          onClick={() => handleVote("B")}
          disabled={loadingVote !== null}
          style={{
            background: currentVote === "B" ? "rgba(6, 182, 212, 0.3)" : "rgba(15, 23, 42, 0.6)",
            border: currentVote === "B" ? "2px solid var(--agent-b)" : "1px solid var(--agent-b-border)",
            borderRadius: "var(--radius-md)",
            padding: "14px",
            cursor: "pointer",
            color: "var(--text-main)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
            transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: currentVote === "B" ? "0 0 20px var(--agent-b-glow)" : "none",
            transform: currentVote === "B" ? "scale(1.02)" : "scale(1)",
          }}
        >
          <span style={{ fontWeight: 800, fontSize: "1.05rem", color: "var(--agent-b)" }}>
            Vote {agentBName}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {currentVote === "B" ? "✓ Your Current Vote" : "Tap to vote or switch"}
          </span>
        </button>
      </div>
    </div>
  );
}
