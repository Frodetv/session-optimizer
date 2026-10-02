# session-optimizer

A Claude Code skill that analyzes your AI session after the fact, identifies redundant steps, and updates your memory files with shortcuts — so the next time you run the same operation, Claude uses fewer tokens.

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

**2. Install the CLI command** (optional, but recommended)

This makes the `session-optimizer` command available everywhere:
```bash
pip install -e .
```

Without this step, replace `session-optimizer` with `python /path/to/session_optimizer.py` in the skill instructions.

**3. Install the skill**

PowerShell:
```powershell
.\install.ps1
```

Or manually copy `SKILL.md` to your Claude skills folder:
```
~/.claude/skills/session-optimize/SKILL.md
```

**4. Restart Claude Code** to activate the skill.

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
session-optimizer --list
```

```
#      Date              Size     UUID                                  Keywords
-------------------------------------------------------------------------------------------------------------------
1   ✓  2026-10-02 12:07  1.9 MB   a1b2c3d4-...                          deploy, release-notes, #1042
2      2026-09-29 08:50  1.0 MB   e5f6a7b8-...                          debug, auth
3      2026-09-21 12:36  545 KB   c9d0e1f2-...                          docs, release-tag
```

- `✓` marks sessions that have already been analyzed
- Keywords are extracted automatically from skill calls, work item IDs, and topic words in user messages
- Greetings are skipped — keywords describe what was actually done

Sort by file size (largest sessions = most to save):
```bash
session-optimizer --list -s
```

Show only unanalyzed sessions:
```bash
session-optimizer --list --unanalyzed
```

Analyze a specific session by UUID:
```bash
session-optimizer --session e5f6a7b8-0000-0000-0000-000000000000
```

## Session tracking

Analyzed sessions are recorded in `~/.claude/session-optimizer-history.json` with timestamp, operation type, and which memory files were updated. The `--list` output shows `✓` for sessions already processed.

When saving memory files, the skill calls:
```bash
session-optimizer \
  --mark-analyzed <uuid> \
  --operation-type <type> \
  --memory-files <file1.md,file2.md>
```

## What gets saved

Learnings are saved as Markdown files in `~/.claude/projects/<project>/memory/` following the standard Claude Code memory format. Each file includes a frontmatter slug and description so Claude can decide when to load it.

Example output for a "create release notes" operation:

```
Operation type : deploy-backend-service

Redundant steps:
  - Searched for config file (path is already known for this component)
  - Looked up artifact name via grep (already known from previous sessions)

Can be preloaded:
  + ArtifactName = my-service
  + ProductName = My Product
  + Config path: deploy/my-service/values.yaml (skip search)

Proposed memory updates:
  [create] project_myservice_shortcuts.md — Shortcuts for deploying MyService
```

## Files

| File | Purpose |
|------|---------|
| `session_optimizer.py` | Reads and compresses the session JSONL transcript |
| `SKILL.md` | Claude Code skill definition |
| `install.ps1` | Copies SKILL.md to `~/.claude/skills/` |
| `pyproject.toml` | Project metadata |
