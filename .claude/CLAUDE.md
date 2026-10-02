# session-optimizer

Tool that analyzes Claude Code sessions and updates memory files to save tokens next time.

## Setup

1. `pip install -e .` to install the `session-optimizer` CLI command
2. Run `.\install.ps1` to copy the skill to `~/.claude/skills/`

**Requirements:** Python 3.11+

## Usage

```bash
# Latest session:
session-optimizer

# Specific session:
session-optimizer --session <uuid>

# List sessions (sorted by size):
session-optimizer --list -s

# Mark a session as analyzed:
session-optimizer --mark-analyzed <uuid> --operation-type deploy --memory-files file.md
```

Without `pip install`, use `python /path/to/session_optimizer.py` instead.

## Session files

Stored in `~/.claude/projects/<project>/*.jsonl`. Latest session is selected automatically by mtime.
