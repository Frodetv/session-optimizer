#!/usr/bin/env python3
"""
session-optimizer: Les og komprimer Claude Code-sesjon for token-analyse.

Skriptet gjør INGEN API-kall selv. Det leser og komprimerer sesjonens JSONL
og skriver den til stdout slik at Claude Code kan analysere den i-sesjon.

Bruk:
  python session_optimizer.py                        # siste sesjon
  python session_optimizer.py --list                 # vis tilgjengelige sesjoner
  python session_optimizer.py --session <uuid|sti>   # spesifikk sesjon
"""

import argparse
import io
import json
import sys
from pathlib import Path

# Tving UTF-8 på stdout (Windows cp1252 feiler på norske tegn)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --- Konfig ---

DEFAULT_PROJECT_DIR = Path.home() / ".claude" / "projects" / "C--Users-frtv"
MAX_TOOL_RESULT_CHARS = 300
MAX_TOOL_INPUT_CHARS = 400
MAX_TEXT_CHARS = 400


# --- Hjelpefunksjoner ---

def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"…[+{len(text)-max_chars}]"


def find_latest_session(project_dir: Path) -> Path | None:
    jsonl_files = list(project_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)


def first_user_message(jsonl_path: Path) -> str:
    GREETINGS = {"hei", "hei!", "hei :)", "hello", "hi", "hey", "yo", "hei :)"}
    best = "(ukjent)"
    try:
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("type") == "user":
                        content = obj.get("message", {}).get("content", "")
                        if isinstance(content, str):
                            text = content.strip()
                            if text and text.lower() not in GREETINGS:
                                return text[:80]
                            elif text and best == "(ukjent)":
                                best = text[:80]
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return best


def list_sessions(project_dir: Path) -> None:
    from datetime import datetime
    jsonl_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not jsonl_files:
        print("Ingen sesjoner funnet.", file=sys.stderr)
        return

    print(f"{'#':<3} {'Dato':<17} {'UUID':<36}  Første melding")
    print("-" * 100)
    for i, f in enumerate(jsonl_files, 1):
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        uuid = f.stem
        first = first_user_message(f)
        print(f"{i:<3} {mtime:<17} {uuid:<36}  {first}")


# --- Parsing ---

def parse_transcript(jsonl_path: Path) -> list[dict]:
    events = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = obj.get("type")

            if event_type == "user":
                content = obj.get("message", {}).get("content", "")
                if isinstance(content, str) and content.strip():
                    events.append({"role": "user", "text": truncate(content, MAX_TEXT_CHARS)})
                elif isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_result":
                            raw = block.get("content", "")
                            if isinstance(raw, list):
                                raw = " ".join(
                                    b.get("text", "") for b in raw if isinstance(b, dict)
                                )
                            events.append({
                                "role": "tool_result",
                                "tool_use_id": block.get("tool_use_id", ""),
                                "is_error": block.get("is_error", False),
                                "content": truncate(str(raw), MAX_TOOL_RESULT_CHARS),
                            })

            elif event_type == "assistant":
                content = obj.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if len(text) > 20:
                            events.append({
                                "role": "assistant_text",
                                "text": truncate(text, MAX_TEXT_CHARS),
                            })
                    elif block.get("type") == "tool_use":
                        compressed_input = {
                            k: truncate(str(v), MAX_TOOL_INPUT_CHARS)
                            for k, v in block.get("input", {}).items()
                        }
                        events.append({
                            "role": "tool_use",
                            "id": block.get("id", ""),
                            "name": block.get("name", ""),
                            "input": compressed_input,
                        })

    return events


def build_summary(events: list[dict]) -> str:
    lines = []
    tool_id_to_name: dict[str, str] = {}

    for ev in events:
        role = ev["role"]
        if role == "user":
            lines.append(f"[BRUKER] {ev['text']}")
        elif role == "assistant_text":
            lines.append(f"[CLAUDE] {ev['text']}")
        elif role == "tool_use":
            tool_id_to_name[ev["id"]] = ev["name"]
            input_summary = ", ".join(f"{k}={v}" for k, v in list(ev["input"].items())[:3])
            lines.append(f"[TOOL] {ev['name']}({input_summary})")
        elif role == "tool_result":
            tool_name = tool_id_to_name.get(ev["tool_use_id"], "?")
            status = "FEIL" if ev["is_error"] else "OK"
            lines.append(f"[RESULT:{status}] ({tool_name}) {ev['content']}")

    return "\n".join(lines)


def count_tool_calls(events: list[dict]) -> int:
    return sum(1 for ev in events if ev["role"] == "tool_use")


# --- Main ---

def resolve_session(value: str, project_dir: Path) -> Path:
    p = Path(value)
    if p.exists():
        return p
    # Prøv som UUID (med eller uten .jsonl)
    stem = p.stem if p.suffix == ".jsonl" else value
    candidate = project_dir / f"{stem}.jsonl"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Fant ikke sesjon: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Komprimer og skriv ut Claude Code-sesjon for analyse"
    )
    parser.add_argument("--session", help="UUID, filnavn eller full sti til sesjon (default: siste)")
    parser.add_argument("--list", action="store_true", help="Vis tilgjengelige sesjoner")
    parser.add_argument("--project-dir", type=Path, default=DEFAULT_PROJECT_DIR)
    args = parser.parse_args()

    if args.list:
        list_sessions(args.project_dir)
        return

    if args.session:
        try:
            session_file = resolve_session(args.session, args.project_dir)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
    else:
        session_file = find_latest_session(args.project_dir)

    if not session_file or not session_file.exists():
        print("Feil: Ingen sesjonsfil funnet.", file=sys.stderr)
        sys.exit(1)

    events = parse_transcript(session_file)
    tool_calls = count_tool_calls(events)

    meta = {
        "session_file": str(session_file),
        "tool_calls": tool_calls,
        "total_events": len(events),
    }
    print(json.dumps(meta, ensure_ascii=False))
    print("---TRANSCRIPT---")
    print(build_summary(events))


if __name__ == "__main__":
    main()
