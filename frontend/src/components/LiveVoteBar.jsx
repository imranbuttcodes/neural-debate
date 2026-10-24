"use client";

export default function LiveVoteBar({
  votes = { A: 0, B: 0, total: 0, percent_A: 50, percent_B: 50 },
  agentAName = "Llama",
  agentBName = "Qwen",
}) {
  const percentA = votes.total > 0 ? votes.percent_A : 50;
  const percentB = votes.total > 0 ? votes.percent_B : 50;

  return (
    <div style={{ width: "100%", margin: "16px 0" }}>
      {/* Header labels */}
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", fontWeight: 700, marginBottom: "8px" }}>
        <div style={{ color: "var(--agent-a)", display: "flex", alignItems: "center", gap: "6px" }}>
          <span>{agentAName}</span>
          <span style={{ fontFamily: "var(--font-mono)", opacity: 0.9 }}>
            {votes.A} ({percentA}%)
          </span>
        </div>

        <div style={{ color: "var(--text-dim)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "1px" }}>
          {votes.total} {votes.total === 1 ? "Vote" : "Votes"} Cast
        </div>

        <div style={{ color: "var(--agent-b)", display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontFamily: "var(--font-mono)", opacity: 0.9 }}>
            ({percentB}%) {votes.B}
          </span>
          <span>{agentBName}</span>
        </div>
      </div>

      {/* Bar container */}
      <div
        style={{
          height: "12px",
          background: "rgba(255, 255, 255, 0.08)",
          borderRadius: "var(--radius-full)",
          overflow: "hidden",
          display: "flex",
          boxShadow: "inset 0 2px 4px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${percentA}%`,
            background: "linear-gradient(90deg, #9333ea, #c084fc)",
            transition: "width 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: "0 0 12px var(--agent-a-glow)",
          }}
        />
        <div
          style={{
            height: "100%",
            width: `${percentB}%`,
            background: "linear-gradient(90deg, #38bdf8, #06b6d4)",
            transition: "width 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: "0 0 12px var(--agent-b-glow)",
          }}
        />
      </div>
    </div>
  );
}
