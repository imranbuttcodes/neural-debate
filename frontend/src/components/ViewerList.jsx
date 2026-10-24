"use client";

export default function ViewerList({ viewers = [], recentJoin = null }) {
  return (
    <div style={{ position: "relative" }}>
      {/* Recent join pop-up notification */}
      {recentJoin && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "rgba(15, 23, 42, 0.95)",
            border: "1px solid var(--agent-a)",
            borderRadius: "var(--radius-full)",
            padding: "8px 18px",
            boxShadow: "0 10px 25px rgba(0, 0, 0, 0.6)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "0.85rem",
            fontWeight: 700,
            zIndex: 1000,
            animation: "slide-in-up 0.3s ease",
          }}
        >
          <span>{recentJoin.avatar || "🦊"}</span>
          <span>{recentJoin.name} joined the arena!</span>
        </div>
      )}

      {/* Online viewers pill */}
      <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "var(--radius-full)", padding: "4px 14px" }}>
        <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--accent-green)" }} />
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>
          {viewers.length} {viewers.length === 1 ? "Audience Member" : "Audience Members"}
        </span>
      </div>
    </div>
  );
}
