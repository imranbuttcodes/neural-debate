"use client";

export default function CountdownTimer({ secondsLeft = 300, totalSeconds = 300 }) {
  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const formatted = `${mins}:${secs < 10 ? "0" : ""}${secs}`;

  const percent = totalSeconds > 0 ? Math.max(0, Math.min(100, (secondsLeft / totalSeconds) * 100)) : 0;
  const isUrgent = secondsLeft > 0 && secondsLeft <= 30;

  return (
    <div style={{ textAlign: "center", width: "100%", maxWidth: "420px", margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "6px" }}>
        <span style={{ fontSize: "0.8rem", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "1px", fontWeight: 700 }}>
          Arena Timer
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "1.4rem",
            fontWeight: 800,
            color: isUrgent ? "var(--accent-red)" : "var(--text-main)",
            animation: isUrgent ? "pulse-glow 1s infinite" : "none",
          }}
        >
          {formatted}
        </span>
      </div>

      {/* Progress track */}
      <div style={{ height: "6px", background: "rgba(255, 255, 255, 0.1)", borderRadius: "var(--radius-full)", overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${percent}%`,
            background: isUrgent
              ? "linear-gradient(90deg, #f59e0b, #ef4444)"
              : "linear-gradient(90deg, var(--agent-a), var(--agent-b))",
            transition: "width 1s linear, background 0.3s ease",
            borderRadius: "var(--radius-full)",
          }}
        />
      </div>
    </div>
  );
}
