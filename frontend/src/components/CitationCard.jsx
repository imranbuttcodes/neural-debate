"use client";

export default function CitationCard({ index, title, snippet, url }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: "block",
        background: "rgba(15, 23, 42, 0.6)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "var(--radius-sm)",
        padding: "10px 14px",
        marginBottom: "8px",
        textDecoration: "none",
        color: "inherit",
        transition: "all 0.2s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "rgba(6, 182, 212, 0.4)";
        e.currentTarget.style.background = "rgba(30, 41, 59, 0.8)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
        e.currentTarget.style.background = "rgba(15, 23, 42, 0.6)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
        <span
          style={{
            background: "rgba(6, 182, 212, 0.2)",
            color: "var(--agent-b)",
            fontSize: "0.7rem",
            fontWeight: 800,
            padding: "2px 6px",
            borderRadius: "4px",
          }}
        >
          [{index}]
        </span>
        <span style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-main)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {title || "Web Citation"}
        </span>
        <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: "var(--text-dim)" }}>
          ↗
        </span>
      </div>
      {snippet && (
        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineClamp: 2, display: "-webkit-box", WebkitBoxOrient: "vertical", overflow: "hidden" }}>
          {snippet}
        </p>
      )}
    </a>
  );
}
