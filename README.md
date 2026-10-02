# session-optimizer

A Claude Code skill that analyzes your AI session after the fact, identifies redundant steps, and updates your memory files with shortcuts — so the next time you run the same operation, Claude uses fewer tokens.

![session-optimize skill in Claude Code](Session-optimize.png)

## How it works

When you invoke `/session-optimize`, Claude:

1. Runs a Python script that reads and compresses the current session's JSONL transcript
2. Analyzes the transcript in-session (no external API key needed)
3. Identifies which tool calls were redundant or could have been skipped
4. Proposes memory file updates with concrete shortcuts
5. Writes the approved updates to `~/.claude/memory/`

The memory files are automatically loaded in future sessions, so Claude skips the discovery steps it already knows the answers to.

## Installation

**Requirements:** Python 3.11+, Claude Code

**1. Clone the repo**
```bash
git clone https://github.com/Frodetv/session-optimizer.git
cd session-optimizer
```

**2. Install the skill**

PowerShell:
```powershell
.\install.ps1
```

Or manually copy `SKILL.md` to your Claude skills folder:
```
~/.claude/skills/session-optimize/SKILL.md
```

**3. Restart Claude Code** to activate the skill.

## Usage

Run `/session-optimize` at the end of any session where you performed a repeatable operation.

```
/session-optimize
```

Claude will present the analysis and ask for confirmation before writing anything to disk.

### Analyze all unanalyzed sessions

```
/session-optimize --analyze-all
```

Claude estimates how long it will take and asks whether to analyze all sessions, start with the largest ones, or pick a number.

### List sessions

```bash
python session_optimizer.py --list
```

```
#      Dato              Str      UUID                                  Nøkkelord
-------------------------------------------------------------------------------------------------------------------
1   ✓  2026-10-02 12:07  1.9 MB   c2e5b651-...                          ado-release-notes, session-optimize, PBI 746192
2      2026-09-29 08:50  1.0 MB   44c55850-...                          PBI 744825, TC, kjernejournal
3      2026-09-21 12:36  545 KB   5180cb8d-...                          brukerdok, release-tag, PBI 743755
```

- `✓` marks sessions that have already been analyzed
- Keywords are extracted automatically from skill calls, ADO work item IDs, and topic words in user messages
- Greetings are skipped — keywords describe what was actually done

Sort by file size (largest sessions = most to save):
```bash
python session_optimizer.py --list -s
```

Show only unanalyzed sessions:
```bash
python session_optimizer.py --list --unanalyzed
```

Analyze a specific session by UUID:
```bash
python session_optimizer.py --session e5f6a7b8-0000-0000-0000-000000000000
```

## Session tracking

Analyzed sessions are recorded in `~/.claude/session-optimizer-history.json` with timestamp, operation type, and which memory files were updated. The `--list` output shows `✓` for sessions already processed.

When saving memory files, the skill calls:
```bash
python session_optimizer.py \
  --mark-analyzed <uuid> \
  --operation-type <type> \
  --memory-files <file1.md,file2.md>
```

## What gets saved

Learnings are saved as Markdown files in `~/.claude/projects/<project>/memory/` following the standard Claude Code memory format. Each file includes a frontmatter slug and description so Claude can decide when to load it.

Example output for a "create release notes" operation:

```
Operation type : release-notes-backend
Summary        : Created release notes and test cases for a backend API change

Redundant steps:
  - Searched for documentation file (path is already known for this component)
  - Ran git grep to find delivery artifact (already known from previous sessions)

Can be preloaded:
  + DeliveryArtifact = my-service
  + ProductName = My Product Name
  + Docs path: docs/my-component.md (skip search)

Proposed memory updates:
  [create] project_myservice_shortcuts.md — Shortcuts for release notes on MyService
```

## Files

| File | Purpose |
|------|---------|
| `session_optimizer.py` | Reads and compresses the session JSONL transcript |
| `SKILL.md` | Claude Code skill definition |
| `install.ps1` | Copies SKILL.md to `~/.claude/skills/` |
| `pyproject.toml` | Project metadata |
