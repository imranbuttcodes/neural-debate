"use client";

import { useState } from "react";
import CreateDebateForm from "../components/CreateDebateForm";
import InviteScreen from "../components/InviteScreen";

export default function HomePage() {
  const [createdData, setCreatedData] = useState(null);

  return (
    <main style={{ flex: 1, padding: "40px 16px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      {/* Header Title */}
      <div style={{ textAlign: "center", marginBottom: "32px" }}>
        <h1 style={{ fontSize: "2.8rem", fontWeight: 900, letterSpacing: "-0.5px", marginBottom: "8px" }} className="title-neon">
          AI DEBATE ARENA
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>
          Live Open-Weight Multi-Agent Debates Powered by Real-Time Audience Voting
        </p>
      </div>

      {!createdData ? (
        <CreateDebateForm onCreated={(res) => setCreatedData(res)} />
      ) : (
        <InviteScreen
          debateData={createdData}
          onDebateStarted={() => {
            window.location.href = createdData.invite_url;
          }}
        />
      )}
    </main>
  );
}
