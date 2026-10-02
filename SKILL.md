---
name: session-optimize
description: Analyze the current session for token savings and update memory files. Use this skill when the user asks to analyze the session, find token savings, optimize the next session, save learnings, or analyze all sessions. Triggered by phrases like "analyze session", "optimize", "save learnings", "token savings", "session-optimize", "analyze all sessions".
---

# Session Optimizer

Analyze what was done in the session and update memory files with shortcuts for next time.

> **Setup:** Install with `pip install -e /path/to/session-optimizer` so the `session-optimizer`
> command is available. Alternatively, replace `session-optimizer` below with
> `python /path/to/session_optimizer.py`.

## Steps

### Step 0 – Choose mode

**A) Analyze latest session (default)**
Go directly to Step 1.

**B) Analyze all unanalyzed sessions (`--analyze-all`)**
Run:
```bash
session-optimizer --analyze-all
```
Read the JSON with the list of unanalyzed sessions.

**Before starting – estimate and ask the user:**
- Count the number of unanalyzed sessions (`unanalyzed_count`)
- Estimate time: ~1–2 minutes per session
- Present the options and ask what the user wants to do:

  > "There are **N unanalyzed sessions** (~X–Y minutes to analyze all). What would you like to do?
  > 1. Analyze all (oldest first)
  > 2. Start with the largest sessions (most token savings)
  > 3. Choose how many to analyze now (e.g. the last 5)
  > 4. Cancel"

For option 2: use `session-optimizer --list --json -s` and match UUIDs against unanalyzed sessions.
Skip sessions with fewer than 3 tool calls — don't count them in the estimate.
Work through the selected sessions one by one (Steps 1–5 for each).

**C) User wants to choose a session from the list**
Run:
```bash
session-optimizer --list --json
```
Present the list as a markdown table with columns: `#`, `✓`, `Date`, `Size`, `Keywords`, `Open`.
- `✓` column: show ✓ if `analyzed == true` in JSON, blank otherwise
- `Open`: clickable file link `[open](file:///<path>)` (replace `\` with `/`)

Ask which session the user wants to analyze.

---

### Step 1 – Extract the session transcript

```bash
# Latest (or latest unanalyzed):
session-optimizer

# Specific session:
session-optimizer --session <uuid>
```

Output: one line of metadata (JSON including `uuid` field), then `---TRANSCRIPT---` followed by the compressed transcript.

### Step 2 – Analyze the transcript

1. **Operation type**: What was done? (e.g. "deploy-backend", "debug-auth-flow")
2. **Redundant steps**: Which tool calls were unnecessary?
3. **Pre-loadable context**: Concrete values, paths, rules that should have been known upfront
4. **Proposed memory files**: Concrete memory file updates

### Step 3 – Present findings

| | |
|---|---|
| Operation type | … |
| Redundant steps | (list) |
| Can be pre-loaded | (list with concrete values) |

### Step 4 – Confirm and save

Ask: **"Should I save these learnings to the memory files?"**

If yes:
1. Write memory files to `~/.claude/projects/<project>/memory/<filename>.md`
2. Update `~/.claude/projects/<project>/memory/MEMORY.md`
3. **Mark the session as analyzed:**

```bash
session-optimizer \
  --mark-analyzed <uuid> \
  --operation-type <operation-type> \
  --memory-files <filename1.md,filename2.md>
```

UUID is found in the metadata line from Step 1 (`"uuid": "..."`).

Memory file format:
```markdown
---
name: short-kebab-slug
description: One line – used to decide relevance in future conversations
metadata:
  type: project
---

Content with concrete values, paths, and rules.
```

### Step 5 – Report

Tell the user what was saved, which session was marked as analyzed, and what token savings this gives next time.

For `--analyze-all`: continue with the next unanalyzed session.

---

## Important notes

- The script makes no API calls – Claude analyzes in-session
- Sessions with fewer than 3 tool calls are not worth analyzing – skip them
- `~/.claude/session-optimizer-history.json` tracks which sessions have been analyzed
- Memory files are automatically loaded in the next session via the MEMORY.md index
- `--list` shows ✓ for already-analyzed sessions
