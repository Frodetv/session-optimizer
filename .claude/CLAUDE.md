# session-optimizer

Verktøy som analyserer Claude Code-sesjoner og oppdaterer minnefiler for å spare tokens neste gang.

## Oppsett

```
pip install anthropic
```

## Bruk

```bash
# Test hva som ville blitt gjort (ingen endringer):
python session_optimizer.py --dry-run

# Analyser og lagre:
python session_optimizer.py

# Spesifiser sesjonsfil manuelt:
python session_optimizer.py --session C:/Users/frtv/.claude/projects/C--Users-frtv/<uuid>.jsonl
```

## Installere skillen

```powershell
.\install.ps1
```

Eller manuelt: kopier `SKILL.md` til `~/.claude/skills/session-optimize/SKILL.md`.

## Avhengigheter

- `ANTHROPIC_API_KEY` i miljøvariabel (settes automatisk av Claude Code)
- Python 3.11+
- `anthropic` pakke

## Sesjonsfiler

Lagres i: `C:/Users/frtv/.claude/projects/C--Users-frtv/*.jsonl`  
Siste sesjon velges automatisk basert på mtime.
