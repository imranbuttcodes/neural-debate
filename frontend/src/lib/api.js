const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createDebate({ topic, description, tone, duration_secs = 300 }) {
  const res = await fetch(`${API_BASE}/api/debates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, description, tone, duration_secs }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDebate(id) {
  const res = await fetch(`${API_BASE}/api/debates/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDebateByInvite(uuid) {
  const res = await fetch(`${API_BASE}/api/debates/invite/${uuid}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDebateState(id, viewerId) {
  const url = viewerId
    ? `${API_BASE}/api/debates/${id}/state?viewer_id=${encodeURIComponent(viewerId)}`
    : `${API_BASE}/api/debates/${id}/state`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function startDebate(id, creatorToken) {
  const res = await fetch(`${API_BASE}/api/debates/${id}/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Creator-Token": creatorToken,
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function registerViewer({ debate_id, display_name, avatar_emoji }) {
  const res = await fetch(`${API_BASE}/api/viewers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ debate_id, display_name, avatar_emoji }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitVote({ debate_id, vote, viewer_id }) {
  const res = await fetch(`${API_BASE}/api/votes`, {
    method: "PATCH", // UPSERT is idempotent
    headers: {
      "Content-Type": "application/json",
      "X-Viewer-Id": viewer_id,
    },
    body: JSON.stringify({ debate_id, vote }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getVotes(debateId) {
  const res = await fetch(`${API_BASE}/api/votes/${debateId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
