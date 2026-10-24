"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { getDebateByInvite } from "../../../lib/api";
import { connectDebateWS } from "../../../lib/ws";
import JoinLobby from "../../../components/JoinLobby";
import WaitingRoom from "../../../components/WaitingRoom";
import DebateArena from "../../../components/DebateArena";
import WinnerScreen from "../../../components/WinnerScreen";

export default function JoinArenaPage() {
  const { uuid } = useParams();

  const [loading, setLoading] = useState(true);
  const [debate, setDebate] = useState(null);
  const [viewer, setViewer] = useState(null);
  const [viewersList, setViewersList] = useState([]);
  const [recentJoin, setRecentJoin] = useState(null);

  // Debate live state
  const [arenaStatus, setArenaStatus] = useState("draft"); // draft | running | finished
  const [activeRound, setActiveRound] = useState(1);
  const [activeAgent, setActiveAgent] = useState("A");
  const [roundLabel, setRoundLabel] = useState("Opening");
  const [activeModel, setActiveModel] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingMessage, setThinkingMessage] = useState("");
  const [currentStreamText, setCurrentStreamText] = useState("");
  const [roundsHistory, setRoundsHistory] = useState([]);
  const [secondsLeft, setSecondsLeft] = useState(300);
  const [totalSeconds, setTotalSeconds] = useState(300);
  const [isVotingOpen, setIsVotingOpen] = useState(true);
  const [voteCounts, setVoteCounts] = useState({ A: 0, B: 0, total: 0, percent_A: 50, percent_B: 50 });
  const [currentViewerVote, setCurrentViewerVote] = useState(null);

  // Winner data
  const [winnerData, setWinnerData] = useState(null);

  const wsRef = useRef(null);

  // 1. Initial Load: Fetch debate metadata & check localStorage for existing viewer
  useEffect(() => {
    if (!uuid) return;

    getDebateByInvite(uuid)
      .then((data) => {
        setDebate(data);
        setArenaStatus(data.status);
        setTotalSeconds(data.duration_secs || 300);
        setSecondsLeft(data.duration_secs || 300);

        // Check localStorage for saved viewer session
        const stored = localStorage.getItem(`viewer_${data.id}`);
        if (stored) {
          try {
            setViewer(JSON.parse(stored));
          } catch (e) {
            console.error(e);
          }
        }
      })
      .catch((err) => console.error("Error loading debate by invite:", err))
      .finally(() => setLoading(false));
  }, [uuid]);

  // 2. Connect WebSocket once debate and viewer are ready
  useEffect(() => {
    if (!debate?.id || !viewer?.viewer_id) return;

    const ws = connectDebateWS(debate.id, viewer.viewer_id, {
      onMessage: (msg) => {
        handleWSEvent(msg);
      },
    });

    wsRef.current = ws;

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [debate?.id, viewer?.viewer_id]);

  // Central event router
  const handleWSEvent = (msg) => {
    switch (msg.type) {
      case "state_snapshot":
        if (msg.debate) {
          setArenaStatus(msg.debate.status);
          setSecondsLeft(msg.debate.seconds_left ?? 300);
          setTotalSeconds(msg.debate.total_seconds ?? 300);
        }
        if (msg.rounds_so_far) {
          setRoundsHistory(msg.rounds_so_far);
        }
        if (msg.current_vote_counts) {
          setVoteCounts(msg.current_vote_counts);
        }
        if (msg.viewer_vote) {
          setCurrentViewerVote(msg.viewer_vote);
        }
        break;

      case "debate_started":
        setArenaStatus("running");
        break;

      case "timer_tick":
        setSecondsLeft(msg.seconds_left);
        if (msg.total_seconds) setTotalSeconds(msg.total_seconds);
        break;

      case "round_start":
        setArenaStatus("running");
        setActiveRound(msg.round);
        setActiveAgent(msg.agent);
        setRoundLabel(msg.label);
        setActiveModel(msg.model || "");
        setCurrentStreamText("");
        setIsThinking(false);
        break;

      case "agent_thinking":
        setIsThinking(true);
        setActiveAgent(msg.agent);
        setThinkingMessage(msg.message || "Searching the web and reasoning...");
        break;

      case "argument_token":
        setIsThinking(false);
        setActiveAgent(msg.agent);
        setCurrentStreamText((prev) => prev + msg.token);
        break;

      case "argument_done":
        setIsThinking(false);
        setCurrentStreamText("");
        setRoundsHistory((prev) => [
          ...prev,
          {
            round: msg.round,
            label: roundLabel,
            agent: msg.agent,
            argument: msg.full_text,
            citations: msg.citations || [],
          },
        ]);
        break;

      case "voting_open":
        setIsVotingOpen(true);
        break;

      case "voting_closed":
        setIsVotingOpen(false);
        break;

      case "live_vote_update":
        setVoteCounts({
          A: msg.A,
          B: msg.B,
          total: msg.total,
          percent_A: msg.percent_A,
          percent_B: msg.percent_B,
        });
        break;

      case "viewer_joined":
        setViewersList((prev) => {
          if (prev.some((v) => v.id === msg.viewer_id)) return prev;
          return [...prev, { id: msg.viewer_id, name: msg.name, avatar: msg.avatar }];
        });
        setRecentJoin({ name: msg.name, avatar: msg.avatar });
        setTimeout(() => setRecentJoin(null), 3500);
        break;

      case "viewer_left":
        setViewersList((prev) => prev.filter((v) => v.name !== msg.name));
        break;

      case "finished":
        setArenaStatus("finished");
        setWinnerData(msg);
        break;

      default:
        break;
    }
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-muted)" }}>
          Connecting to Arena...
        </div>
      </div>
    );
  }

  if (!debate) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center" }}>
        <div className="glass-panel" style={{ padding: "40px" }}>
          <h2>Arena Not Found</h2>
          <p style={{ color: "var(--text-muted)", margin: "12px 0 24px" }}>
            This debate link may be invalid or has expired.
          </p>
          <a href="/" className="btn-primary" style={{ textDecoration: "none" }}>
            Return Home
          </a>
        </div>
      </div>
    );
  }

  // 1. Viewer hasn't joined yet
  if (!viewer) {
    return (
      <main style={{ flex: 1, padding: "40px 16px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <JoinLobby debateData={debate} onJoined={(v) => setViewer(v)} />
      </main>
    );
  }

  // 2. Waiting Room (debate is in draft status)
  if (arenaStatus === "draft") {
    return (
      <main style={{ flex: 1, padding: "40px 16px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <WaitingRoom debateData={debate} viewer={viewer} totalViewers={viewersList.length || 1} />
      </main>
    );
  }

  // 3. Winner Screen (debate concluded)
  if (arenaStatus === "finished" && winnerData) {
    return (
      <main style={{ flex: 1, padding: "40px 16px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <WinnerScreen
          winner={winnerData.winner}
          winnerName={winnerData.winner_name}
          isTie={winnerData.is_tie}
          finalVotes={winnerData.final_votes}
          roundsBreakdown={winnerData.rounds_breakdown || []}
          topic={debate.topic}
        />
      </main>
    );
  }

  // 4. Live Arena (debate is running)
  return (
    <main style={{ flex: 1, padding: "20px 0" }}>
      <DebateArena
        debateData={debate}
        activeRound={activeRound}
        activeAgent={activeAgent}
        roundLabel={roundLabel}
        activeModel={activeModel}
        isThinking={isThinking}
        thinkingMessage={thinkingMessage}
        currentStreamText={currentStreamText}
        roundsHistory={roundsHistory}
        secondsLeft={secondsLeft}
        totalSeconds={totalSeconds}
        voteCounts={voteCounts}
        currentViewerVote={currentViewerVote}
        onVoteChanged={(choice) => setCurrentViewerVote(choice)}
        isVotingOpen={isVotingOpen}
        viewers={viewersList}
        recentJoin={recentJoin}
        viewerId={viewer.viewer_id}
      />
    </main>
  );
}
