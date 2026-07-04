"""Command-line test harness for the ZeroDelay backend (front-end not required).

Examples:
  python -m backend.cli build-index
  python -m backend.cli info
  python -m backend.cli retrieve "the airlock won't depressurize"
  python -m backend.cli ask "coolant loop pressure is dropping, what do I do?"
  python -m backend.cli converse MarsMind/astronaut_query.wav
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config


def cmd_build_index(_args) -> None:
    from .index.build_index import build

    summary = build()
    print("Index built:")
    print(json.dumps(summary, indent=2))


def cmd_info(_args) -> None:
    from .data_loader import load_corpus

    corpus = load_corpus()
    print(f"Procedures: {len(corpus.procedures)}")
    for p in corpus.procedures.values():
        print(f"  - {p.procedure_id}: {p.title} ({len(p.steps)} steps)")
    print(f"Diagrams: {len(corpus.diagrams)}")
    missing = [d.diagram_id for d in corpus.diagrams.values() if not d.image_exists]
    if missing:
        print(f"  (PNG not yet generated for: {', '.join(missing)})")
    print(f"Reference files: {', '.join(corpus.reference.keys())}")


def cmd_retrieve(args) -> None:
    from .index.retriever import Retriever

    result = Retriever().retrieve(args.query)
    print(f"Query: {args.query}")
    print("Procedures:")
    for p in result.procedures:
        print(f"  - {p.procedure_id}: {p.title} (score {p.score})")
    print("Diagrams:")
    for d in result.diagrams:
        flag = "img" if d.image_exists else "no-img"
        print(f"  - {d.diagram_id}: {d.title} ({flag}, score {d.score})")


def cmd_ask(args) -> None:
    from .agent.orchestrator import Orchestrator

    result = Orchestrator().process_text(args.query, speak=not args.no_speak)
    _print_result(result)


def cmd_converse(args) -> None:
    from .agent.orchestrator import Orchestrator
    from .models import vad

    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")
    norm = vad.prepare_audio(audio_path)
    result = Orchestrator().process_audio(
        norm, live_image_path=args.image, speak=not args.no_speak
    )
    _print_result(result)


def _print_result(result: dict) -> None:
    print("\n=== Query ===")
    print(result.get("query"))
    print("\n=== Decision ===")
    print(json.dumps(result.get("decision"), indent=2))
    if result.get("tool_calls"):
        print("\n=== Tool calls ===")
        print(json.dumps(result["tool_calls"], indent=2))
    if result.get("tts_path"):
        print(f"\nSpoken response written to: {result['tts_path']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ZeroDelay backend CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("build-index").set_defaults(func=cmd_build_index)
    sub.add_parser("info").set_defaults(func=cmd_info)

    p_ret = sub.add_parser("retrieve")
    p_ret.add_argument("query")
    p_ret.set_defaults(func=cmd_retrieve)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("query")
    p_ask.add_argument("--no-speak", action="store_true")
    p_ask.set_defaults(func=cmd_ask)

    p_conv = sub.add_parser("converse")
    p_conv.add_argument(
        "audio", nargs="?", default=str(config.REPO_ROOT / "MarsMind" / "astronaut_query.wav")
    )
    p_conv.add_argument("--image", default=None)
    p_conv.add_argument("--no-speak", action="store_true")
    p_conv.set_defaults(func=cmd_converse)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
