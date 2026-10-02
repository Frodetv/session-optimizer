#!/usr/bin/env python3
"""
session-optimizer: Les og komprimer Claude Code-sesjon for token-analyse.

Skriptet gjør INGEN API-kall selv. Det leser og komprimerer sesjonens JSONL
og skriver den til stdout slik at Claude Code kan analysere den i-sesjon.

Bruk:
  python session_optimizer.py [--session <path>] [--project-dir <path>]
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

def main():
    parser = argparse.ArgumentParser(
        description="Komprimer og skriv ut Claude Code-sesjon for analyse"
    )
    parser.add_argument("--session", type=Path, help="Sti til JSONL-fil (default: siste sesjon)")
    parser.add_argument("--project-dir", type=Path, default=DEFAULT_PROJECT_DIR)
    args = parser.parse_args()

    session_file = args.session or find_latest_session(args.project_dir)

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
