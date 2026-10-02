#!/usr/bin/env python3
"""
session-optimizer: Les og komprimer Claude Code-sesjon for token-analyse.

Skriptet gjør INGEN API-kall selv. Det leser og komprimerer sesjonens JSONL
og skriver den til stdout slik at Claude Code kan analysere den i-sesjon.

Bruk:
  python session_optimizer.py                          # siste sesjon
  python session_optimizer.py --list                   # vis tilgjengelige sesjoner
  python session_optimizer.py --list --unanalyzed      # vis kun uanalyserte sesjoner
  python session_optimizer.py --session <uuid|sti>     # spesifikk sesjon
  python session_optimizer.py --analyze-all            # list alle uanalyserte (for skill-loop)
  python session_optimizer.py --mark-analyzed <uuid>   # marker sesjon som analysert
"""

import argparse
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Tving UTF-8 på stdout (Windows cp1252 feiler på norske tegn)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --- Konfig ---

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
HISTORY_FILE = CLAUDE_DIR / "session-optimizer-history.json"
MAX_TOOL_RESULT_CHARS = 300
MAX_TOOL_INPUT_CHARS = 400
MAX_TEXT_CHARS = 400


# --- Analysert-historikk ---

def load_history() -> dict:
    if not HISTORY_FILE.exists():
        return {"analyzed": {}}
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"analyzed": {}}


def save_history(history: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_analyzed(uuid: str, operation_type: str = "", memory_files: list[str] | None = None) -> None:
    history = load_history()
    history["analyzed"][uuid] = {
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "operation_type": operation_type,
        "memory_files": memory_files or [],
    }
    save_history(history)
    print(f"Markert som analysert: {uuid}")


def is_analyzed(uuid: str, history: dict) -> bool:
    return uuid in history.get("analyzed", {})


# --- Sesjonsfiler ---

def all_session_files() -> list[Path]:
    """Samle bruker-initierte JSONL-sesjonsfiler fra alle prosjektmapper."""
    if not PROJECTS_DIR.exists():
        return []
    return sorted(
        (f for f in PROJECTS_DIR.rglob("*.jsonl") if not f.stem.startswith("agent-")),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )


# --- Hjelpefunksjoner ---

def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"…[+{len(text)-max_chars}]"


def find_latest_session(unanalyzed_only: bool = False) -> Path | None:
    history = load_history() if unanalyzed_only else {}
    for f in all_session_files():
        if not unanalyzed_only or not is_analyzed(f.stem, history):
            return f
    return None


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


_TOPIC_PATTERNS = [
    (r"\btc\b|\btf\b|testcase|test case", "TC"),
    (r"\brn\b|release notes", "RN"),
    (r"release-tag|release tag|\blansering\b|\blanser\b", "release-tag"),
    (r"brukerdok", "brukerdok"),
    (r"log.sjekk|kubernetes|kubectl", "log-sjekk"),
    (r"vekstkurve|growthchart", "vekstkurve"),
    (r"retina", "retina"),
    (r"kjernejournal", "kjernejournal"),
    (r"gatconnector|gatcollector|gatimporter", "gat"),
    (r"ehrexport", "ehrexport"),
    (r"digitallyactive|digitalt aktiv", "digitallyactive"),
    (r"tilemanager|tile manager", "tilemanager"),
    (r"oracle|sql\b", "SQL"),
    (r"vibe.?code|hobby|privat", "privat"),
    (r"session.optim", "session-optimizer"),
]


def extract_keywords(jsonl_path: Path) -> list[str]:
    """Rask heuristisk skanning – returnerer 1-3 nøkkelord for sesjonen."""
    skills: list[str] = []
    work_items: list[str] = []
    topics: list[str] = []
    seen_topics: set[str] = set()

    try:
        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if obj.get("type") == "user":
                    content = obj.get("message", {}).get("content", "")
                    # Kun ren bruker-tekst – ikke tool_result-blokker
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        text = " ".join(
                            b.get("text", "")
                            for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        )
                    else:
                        text = ""
                    for pat, label in _TOPIC_PATTERNS:
                        if label not in seen_topics and re.search(pat, text, re.IGNORECASE):
                            topics.append(label)
                            seen_topics.add(label)
                    # Kun 6-sifrede ADO-tall i DIPS-området (7xxxxx)
                    for m in re.findall(r"\b(7\d{5})\b", text):
                        wi = f"PBI {m}"
                        if wi not in work_items:
                            work_items.append(wi)

                elif obj.get("type") == "assistant":
                    for block in obj.get("message", {}).get("content", []):
                        if block.get("type") == "tool_use" and block.get("name") == "Skill":
                            skill = block.get("input", {}).get("skill", "")
                            if skill and skill not in skills:
                                skills.append(skill)
    except OSError:
        pass

    result: list[str] = []
    # Skill-kall er mest informative
    result.extend(skills[:2])
    # PBI-numre (maks 2)
    for wi in work_items[:2]:
        if len(result) < 3:
            result.append(wi)
    # Emneord fra meldinger
    for t in topics:
        if t not in result and len(result) < 3:
            result.append(t)

    return result or ["(ukjent)"]


def format_size(bytes: int) -> str:
    if bytes < 1024:
        return f"{bytes} B"
    if bytes < 1024 ** 2:
        return f"{bytes / 1024:.0f} KB"
    return f"{bytes / 1024 ** 2:.1f} MB"


# --- Liste ---

def list_sessions(limit: int = 20, as_json: bool = False, sort_by_size: bool = False,
                  unanalyzed_only: bool = False) -> None:
    history = load_history()
    jsonl_files = all_session_files()

    if not jsonl_files:
        print("Ingen sesjoner funnet.", file=sys.stderr)
        return

    if unanalyzed_only:
        jsonl_files = [f for f in jsonl_files if not is_analyzed(f.stem, history)]

    if sort_by_size:
        jsonl_files = sorted(jsonl_files, key=lambda f: f.stat().st_size, reverse=True)

    shown = jsonl_files[:limit]
    remaining = len(jsonl_files) - len(shown)

    rows = []
    for i, f in enumerate(shown, 1):
        stat = f.stat()
        analyzed = is_analyzed(f.stem, history)
        analyzed_at = history["analyzed"].get(f.stem, {}).get("analyzed_at", "")
        op_type = history["analyzed"].get(f.stem, {}).get("operation_type", "")
        keywords = extract_keywords(f)
        rows.append({
            "index": i,
            "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "uuid": f.stem,
            "size": format_size(stat.st_size),
            "size_bytes": stat.st_size,
            "path": str(f),
            "first_message": first_user_message(f),
            "keywords": keywords,
            "analyzed": analyzed,
            "analyzed_at": analyzed_at,
            "operation_type": op_type,
        })

    if as_json:
        print(json.dumps({"sessions": rows, "remaining": remaining, "total": len(jsonl_files)},
                         ensure_ascii=False))
        return

    print(f"{'#':<3} {'':2} {'Dato':<17} {'Str':<8} {'UUID':<36}  Nøkkelord")
    print("-" * 115)
    for r in rows:
        check = "✓" if r["analyzed"] else " "
        kw = ", ".join(r["keywords"])
        print(f"{r['index']:<3} {check}  {r['date']:<17} {r['size']:<8} {r['uuid']:<36}  {kw}")

    if remaining > 0:
        label = "uanalyserte " if unanalyzed_only else ""
        print(f"\n... og {remaining} eldre {label}sesjoner. Bruk --limit {len(jsonl_files)} for å se alle.")


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

def resolve_session(value: str) -> Path:
    p = Path(value)
    if p.exists():
        return p
    stem = p.stem if p.suffix == ".jsonl" else value
    for f in all_session_files():
        if f.stem == stem:
            return f
    raise FileNotFoundError(f"Fant ikke sesjon: {value}")


def output_transcript(session_file: Path) -> None:
    events = parse_transcript(session_file)
    tool_calls = count_tool_calls(events)
    meta = {
        "session_file": str(session_file),
        "uuid": session_file.stem,
        "tool_calls": tool_calls,
        "total_events": len(events),
    }
    print(json.dumps(meta, ensure_ascii=False))
    print("---TRANSCRIPT---")
    print(build_summary(events))


def main():
    parser = argparse.ArgumentParser(
        description="Komprimer og skriv ut Claude Code-sesjon for analyse"
    )
    parser.add_argument("--session", help="UUID, filnavn eller full sti til sesjon (default: siste)")
    parser.add_argument("--list", action="store_true", help="Vis tilgjengelige sesjoner")
    parser.add_argument("--unanalyzed", action="store_true", help="Vis/hent kun uanalyserte sesjoner")
    parser.add_argument("--analyze-all", action="store_true", help="List alle uanalyserte sesjoner som JSON (for skill-loop)")
    parser.add_argument("--mark-analyzed", metavar="UUID", help="Marker sesjon som analysert")
    parser.add_argument("--operation-type", default="", help="Operasjonstype ved --mark-analyzed")
    parser.add_argument("--memory-files", default="", help="Kommaseparerte minnefiler ved --mark-analyzed")
    parser.add_argument("--limit", type=int, default=20, help="Maks antall sesjoner i listen (default: 20)")
    parser.add_argument("-s", "--sort-size", action="store_true", help="Sorter etter filstørrelse, største først")
    parser.add_argument("--json", action="store_true", help="Output som JSON (brukes av skill)")
    args = parser.parse_args()

    if args.mark_analyzed:
        memory_files = [m.strip() for m in args.memory_files.split(",") if m.strip()]
        mark_analyzed(args.mark_analyzed, args.operation_type, memory_files)
        return

    if args.analyze_all:
        history = load_history()
        unanalyzed = [f for f in all_session_files() if not is_analyzed(f.stem, history)]
        print(json.dumps({
            "unanalyzed_count": len(unanalyzed),
            "sessions": [{"uuid": f.stem, "path": str(f), "first_message": first_user_message(f)}
                         for f in unanalyzed]
        }, ensure_ascii=False))
        return

    if args.list:
        list_sessions(limit=args.limit, as_json=args.json, sort_by_size=args.sort_size,
                      unanalyzed_only=args.unanalyzed)
        return

    if args.session:
        try:
            session_file = resolve_session(args.session)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
    else:
        session_file = find_latest_session(unanalyzed_only=args.unanalyzed)

    if not session_file or not session_file.exists():
        print("Feil: Ingen sesjonsfil funnet.", file=sys.stderr)
        sys.exit(1)

    output_transcript(session_file)


if __name__ == "__main__":
    main()
