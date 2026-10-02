---
name: session-optimize
description: Analyser gjeldende sesjon for token-besparelser og oppdater minnefiler. Bruk denne skillen når brukeren ber om å analysere sesjonen, finne token-besparelser, optimalisere neste sesjon, eller lagre lærdommer. Triggres av fraser som "analyser sesjonen", "optimaliser", "lagre lærdommer", "token-besparelser", "session-optimize".
---

# Session Optimizer

Analyser hva som ble gjort i sesjonen og oppdater minnefiler med kortveier for neste gang.

## Fremgangsmåte

### Steg 0 – Hvis brukeren vil velge sesjon (valgfritt)

Hvis brukeren vil analysere en tidligere sesjon og ikke den siste, kjør:

```bash
python C:/DIPS/_git/session-optimizer/session_optimizer.py --list --json
```

Les JSON-output og presenter listen som en **formatert markdown-tabell** i svaret ditt (ikke vis rå Bash-output).
- Kolonner: `#`, `Dato`, `Str` (filstørrelse), `Første melding`, `Åpne`
- Lag en klikkbar fillenke i `Åpne`-kolonnen: `[åpne](file:///<path>)` der `<path>` er `path`-feltet fra JSON (erstatt `\` med `/` og legg til `file:///` foran)

Eksempel-output:

| # | Dato | Str | Første melding | Åpne |
|---|------|-----|----------------|------|
| 1 | 2026-10-02 10:42 | 48 KB | tc og rn for 746192 | [åpne](file:///C:/Users/frtv/.claude/projects/C--Users-frtv/c2e5b651-....jsonl) |
| 2 | 2026-10-01 09:24 | 12 KB | ok | [åpne](file:///C:/Users/frtv/.claude/projects/C--Users-frtv/1e0e4a99-....jsonl) |

Spør deretter hvilken sesjon brukeren vil analysere (nummer eller UUID).

### Steg 1 – Ekstraher sesjonstranskripsjonen

Kjør skriptet for å lese og komprimere sesjonens JSONL:

```bash
# Siste sesjon:
python C:/DIPS/_git/session-optimizer/session_optimizer.py

# Spesifikk sesjon (UUID fra listen):
python C:/DIPS/_git/session-optimizer/session_optimizer.py --session <uuid>
```

Output: én linje med metadata (JSON), deretter `---TRANSCRIPT---` etterfulgt av komprimert transkripsjon.

### Steg 2 – Analyser transkripsjonen

Les output fra skriptet og analyser:

1. **Operasjonstype**: Hva ble egentlig gjort? (f.eks. "tc-og-rn-retina", "release-tag-gatconnector")
2. **Redundante steg**: Hvilke tool calls var overflødige fordi svaret allerede er kjent?
   - Eksempel: grep etter retina-filer når vi vet hvilken fil det er
   - Eksempel: oppdage DeliveryArtifact ved å søke når det allerede er kjent
3. **Forhåndslastbar kontekst**: Hva burde vært i en minnefil fra start?
   - Konkrete verdier: stier, felt-verdier, regler
4. **Foreslåtte minnefiler**: Skriv konkrete minnefil-oppdateringer

### Steg 3 – Presenter funn

Vis for brukeren:

| | |
|---|---|
| Operasjonstype | … |
| Redundante steg | (liste) |
| Kan forhåndslastes | (liste med konkrete verdier) |

Og foreslåtte minnefiler med innhold.

### Steg 4 – Bekreft og lagre

Spør: **"Skal jeg lagre disse lærdommene til minnefilene?"**

Hvis ja: Bruk Write-verktøyet til å:
1. Skrive nye minnefiler til `C:/Users/frtv/.claude/projects/C--Users-frtv/memory/<filnavn>.md`
2. Legge til peker i `C:/Users/frtv/.claude/projects/C--Users-frtv/memory/MEMORY.md`

**Minnefil-format:**
```markdown
---
name: kort-kebab-slug
description: Én linje – brukes til å avgjøre relevans i fremtidige samtaler
metadata:
  type: project
---

Innhold med konkrete verdier, stier og regler.
```

### Steg 5 – Rapporter

Fortell hva som ble lagret og hvilke token-besparelser dette gir neste gang.

## Viktige noter

- Skriptet gjør ingen API-kall – Claude analyserer selv i sesjonen
- Hvis sesjonsfilen har færre enn 3 tool calls, er analysen ikke nyttig
- Minnefilene leses automatisk i neste sesjon via MEMORY.md-indeksen
- Kjør `pip install anthropic` er IKKE nødvendig (brukes ikke lenger)
