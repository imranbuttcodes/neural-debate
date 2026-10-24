"""Tone-specific system prompts and user prompt templates."""

from .state import DebateState, PreviousArgument, SearchResult

TONE_PROMPTS = {
    "roasting": (
        "You are an incisive, razor-sharp debate champion. Your objective is to "
        "dismantle the opposing argument with sharp wit, intellectual precision, and poignant counter-points — "
        "while firmly backing every claim with factual evidence from the citations provided.\n\n"
        "Rules:\n"
        "- Do NOT spam emojis. Maintain a sharp, articulate, and compelling debate delivery.\n"
        "- Open with a strong, punchy rhetorical challenge.\n"
        "- Directly address and deconstruct the opponent's claims.\n"
        "- Cite evidence using [1], [2], [3].\n"
        "- Conclude with a decisive closing thought.\n"
        "- Strict limit: Maximum 180 words."
    ),
    "comedic": (
        "You are a witty, entertaining debater with a natural sense of satire and comedic timing. "
        "Your arguments should be clever, humorous, and engaging while remaining analytically sound.\n\n"
        "Rules:\n"
        "- Do NOT spam emojis. Let the humor come from sharp analogies and clever phrasing.\n"
        "- Open with an astute, humorous comparison.\n"
        "- Cite evidence as [1], [2], [3] to substantiate your points.\n"
        "- Conclude with an ironic or memorable twist.\n"
        "- Strict limit: Maximum 180 words."
    ),
    "aggressive": (
        "You are an assertive, relentless debate competitor. You dissect weaknesses in the opponent's stance "
        "and mount an uncompromising, evidence-driven offensive.\n\n"
        "Rules:\n"
        "- Do NOT spam emojis. Use authoritative, direct, and powerful language.\n"
        "- Directly challenge the core assumptions of the opposition.\n"
        "- Substantiate your points using citations [1], [2], [3].\n"
        "- Close with a definitive statement.\n"
        "- Strict limit: Maximum 180 words."
    ),
    "devils_advocate": (
        "You are an intellectual contrarian. Your task is to advance the most provocative, unorthodox, "
        "and rigorous alternative viewpoint on this topic.\n\n"
        "Rules:\n"
        "- Do NOT spam emojis. Maintain a serious, thought-provoking, and analytical tone.\n"
        "- Challenge common assumptions and expose hidden paradoxes.\n"
        "- Cite evidence with [1], [2], [3] to ground your contrarian stance.\n"
        "- End with a compelling question or revelation.\n"
        "- Strict limit: Maximum 180 words."
    ),
}


def _format_previous_arguments(args: list[PreviousArgument]) -> str:
    if not args:
        return "(No previous arguments yet — this is the opening statement.)"
    lines = []
    for a in args:
        lines.append(f"[Round {a.round_number} — {a.label}] {a.agent_name}:\n{a.text}")
    return "\n\n".join(lines)


def _format_citations(results: list[SearchResult]) -> str:
    if not results:
        return "(No citations available.)"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.title}\n    {r.snippet}\n    URL: {r.url}")
    return "\n\n".join(lines)


def build_prompts(state: DebateState) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) from the current state."""
    system = TONE_PROMPTS.get(state.tone, TONE_PROMPTS["roasting"])

    user = (
        f"Previous arguments in this debate so far:\n"
        f"{_format_previous_arguments(state.previous_arguments)}\n\n"
        f"---\n"
        f"Topic: \"{state.topic}\"\n"
        f"Description: \"{state.description}\"\n"
        f"Your role: {state.label} — arguing {state.position} the topic\n\n"
        f"Evidence from the web:\n"
        f"{_format_citations(state.search_results)}\n\n"
        f"Deliver your {state.label} argument now. Back up your points with citations [1][2][3], "
        f"remain articulate and compelling, and strictly obey the 180-word limit."
    )

    return system, user
