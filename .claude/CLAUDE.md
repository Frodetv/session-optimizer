# session-optimizer

Tool that analyzes Claude Code sessions and updates memory files to save tokens next time.

## Setup

Run `.\install.ps1` to install the skill, or copy `SKILL.md` manually to `~/.claude/skills/session-optimize/SKILL.md`.

**Requirements:** Python 3.11+

## Usage

```bash
# Latest session:
python session_optimizer.py

# Specific session:
python session_optimizer.py --session <uuid>

# List sessions (sorted by size):
python session_optimizer.py --list -s

# Mark a session as analyzed:
python session_optimizer.py --mark-analyzed <uuid> --operation-type deploy --memory-files file.md
```

## Session files

Stored in `~/.claude/projects/<project>/*.jsonl`. Latest session is selected automatically by mtime.
