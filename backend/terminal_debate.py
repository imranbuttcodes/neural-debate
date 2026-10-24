#!/usr/bin/env python3
"""Watch two LangGraph agents debate in the terminal.

    cd backend
    .venv/bin/python terminal_debate.py                 # 60-second debate
    .venv/bin/python terminal_debate.py --graph         # print + render the graphs
"""

from __future__ import annotations

import argparse
import sys

from app.debate import run_debate, show_graphs
from app.debate.graph import ENV_PATH, MAX_TURNS, SECONDS

DEFAULT_TOPIC = (
    "AI coding assistants will make junior software engineers obsolete within five years"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent-vs-agent LangGraph debate.")
    parser.add_argument("--topic", "-t", default=DEFAULT_TOPIC, help="debate motion")
    parser.add_argument(
        "--seconds", "-s", type=float, default=SECONDS, help="time budget (default 60)"
    )
    parser.add_argument(
        "--turns", "-n", type=int, default=MAX_TURNS, help="max turns (default 16)"
    )
    parser.add_argument(
        "--graph", action="store_true", help="print the graphs and save PNGs"
    )
    args = parser.parse_args(argv)

    try:
        if args.graph:
            show_graphs("graphs")
            return 0
        if args.seconds < 5 or args.turns < 1 or not args.topic.strip():
            print("error: need --seconds >= 5, --turns >= 1 and a topic", file=sys.stderr)
            return 2
        final = run_debate(
            topic=args.topic.strip(),
            seconds=args.seconds,
            max_turns=args.turns,
        )
    except RuntimeError as exc:  # missing key / config problem
        print(f"error: {exc}", file=sys.stderr)
        print(f"hint: check {ENV_PATH}", file=sys.stderr)
        return 1

    return 0 if final.get("transcript") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\ninterrupted")
        raise SystemExit(130)
