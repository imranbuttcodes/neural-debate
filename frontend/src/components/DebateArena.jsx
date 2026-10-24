"use client";

import AgentPanel from "./AgentPanel";
import CountdownTimer from "./CountdownTimer";
import RoundBadge from "./RoundBadge";
import ViewerList from "./ViewerList";
import VoteSection from "./VoteSection";

export default function DebateArena({
  debateData,
  activeRound,
  activeAgent, // "A" or "B"
  roundLabel,
  activeModel,
  isThinking,
  thinkingMessage,
  currentStreamText,
  roundsHistory,
  secondsLeft,
  totalSeconds,
  voteCounts,
  currentViewerVote,
  onVoteChanged,
  isVotingOpen,
  viewers,
  recentJoin,
  viewerId,
}) {
  const agentAName = debateData?.agent_a_name || "Llama";
  const agentBName = debateData?.agent_b_name || "Qwen";
  const currentTurnName = activeAgent === "A" ? agentAName : agentBName;

  // Filter history for each agent
  const historyA = roundsHistory.filter((r) => r.agent === "A");
  const historyB = roundsHistory.filter((r) => r.agent === "B");

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "16px", width: "100%" }}>
      {/* Top Header Bar */}
      <div
        className="glass-panel"
        style={{
          padding: "16px 24px",
          marginBottom: "16px",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
        }}
      >
        <div style={{ flex: 1, minWidth: "260px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "2px" }}>
            Debate Topic
          </div>
          <h1 style={{ fontSize: "1.2rem", fontWeight: 800, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} className="title-gradient">
            {debateData?.topic}
          </h1>
        </div>

        {/* Center Round Indicator */}
        <RoundBadge
          round={activeRound}
          label={roundLabel}
          agentName={currentTurnName}
        />

        {/* Right Timer & Viewers */}
        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <CountdownTimer
            secondsLeft={secondsLeft}
            totalSeconds={totalSeconds || debateData?.duration_secs || 300}
          />
          <ViewerList viewers={viewers} recentJoin={recentJoin} />
        </div>
      </div>

      {/* Main Split Grid for Agents */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "20px",
          minHeight: "520px",
          marginBottom: "16px",
        }}
      >
        {/* Agent A Panel */}
        <AgentPanel
          agent="A"
          name={agentAName}
          emoji="🧠"
          model={debateData?.model_a || "openai/gpt-oss-120b"}
          position="FOR"
          isActive={activeAgent === "A"}
          isThinking={activeAgent === "A" && isThinking}
          thinkingMessage={thinkingMessage}
          currentStreamText={activeAgent === "A" ? currentStreamText : ""}
          roundsHistory={historyA}
        />

        {/* Agent B Panel */}
        <AgentPanel
          agent="B"
          name={agentBName}
          emoji="🐉"
          model={debateData?.model_b || "qwen/qwen3.8-27b"}
          position="AGAINST"
          isActive={activeAgent === "B"}
          isThinking={activeAgent === "B" && isThinking}
          thinkingMessage={thinkingMessage}
          currentStreamText={activeAgent === "B" ? currentStreamText : ""}
          roundsHistory={historyB}
        />
      </div>

      {/* Audience Voting Bar */}
      <VoteSection
        debateId={debateData?.id}
        viewerId={viewerId}
        currentVote={currentViewerVote}
        onVoteChanged={onVoteChanged}
        voteCounts={voteCounts}
        agentAName={agentAName}
        agentBName={agentBName}
        isVotingOpen={isVotingOpen}
      />
    </div>
  );
}
