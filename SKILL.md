---
name: session-optimize
description: Analyser gjeldende sesjon for token-besparelser og oppdater minnefiler. Bruk denne skillen når brukeren ber om å analysere sesjonen, finne token-besparelser, optimalisere neste sesjon, lagre lærdommer, eller analysere alle sesjoner. Triggres av fraser som "analyser sesjonen", "optimaliser", "lagre lærdommer", "token-besparelser", "session-optimize", "analyser alle sesjoner".
---

# Session Optimizer

Analyser hva som ble gjort i sesjonen og oppdater minnefiler med kortveier for neste gang.

## Fremgangsmåte

### Steg 0 – Velg modus

**A) Analyser siste sesjon (default)**
Gå rett til Steg 1.

**B) Analyser alle uanalyserte sesjoner (`--analyze-all`)**
Kjør:
```bash
python C:/DIPS/_git/session-optimizer/session_optimizer.py --analyze-all
```
Les JSON med liste over uanalyserte sesjoner.

**Før du starter – estimer og spør brukeren:**
- Tell antall uanalyserte sesjoner (`unanalyzed_count`)
- Estimer tid: ca. 1–2 minutter per sesjon
- Presenter alternativene og spør hva brukeren vil gjøre:

  > "Det er **N uanalyserte sesjoner** (~X–Y minutter å analysere alle). Hva vil du gjøre?
  > 1. Analyser alle (eldste først)
  > 2. Start med de største sesjonene (flest token-besparelser)
  > 3. Velg antall å analysere nå (f.eks. de 5 siste)
  > 4. Avbryt"

Sorter ved alternativ 2: bruk `--list --json -s` og match UUID-er mot uanalyserte.
Hopp over sesjoner med færre enn 3 tool calls – tell dem ikke med i estimatet.
Gå gjennom valgte sesjoner én etter én (Steg 1–5 for hver).

**C) Brukeren vil velge sesjon fra liste**
Kjør:
```bash
python C:/DIPS/_git/session-optimizer/session_optimizer.py --list --json
```
Presenter listen som markdown-tabell med kolonner: `#`, `✓`, `Dato`, `Str`, `Første melding`, `Åpne`.
- `✓`-kolonnen: vis ✓ hvis `analyzed == true` i JSON, blank ellers
- `Åpne`: klikkbar fillenke `[åpne](file:///<path>)` (erstatt `\` med `/`)

Spør hvilken sesjon brukeren vil analysere.

---

### Steg 1 – Ekstraher sesjonstranskripsjonen

```bash
# Siste (eller siste uanalyserte):
python C:/DIPS/_git/session-optimizer/session_optimizer.py

# Spesifikk sesjon:
python C:/DIPS/_git/session-optimizer/session_optimizer.py --session <uuid>
```

Output: én linje med metadata (JSON inkl. `uuid`-felt), deretter `---TRANSCRIPT---` etterfulgt av komprimert transkripsjon.

### Steg 2 – Analyser transkripsjonen

1. **Operasjonstype**: Hva ble gjort? (f.eks. "tc-og-rn-retina", "release-tag-gatconnector")
2. **Redundante steg**: Hvilke tool calls var overflødige?
3. **Forhåndslastbar kontekst**: Konkrete verdier, stier, regler som burde vært kjent
4. **Foreslåtte minnefiler**: Konkrete minnefil-oppdateringer

### Steg 3 – Presenter funn

Vis for brukeren:

| | |
|---|---|
| Operasjonstype | … |
| Redundante steg | (liste) |
| Kan forhåndslastes | (liste med konkrete verdier) |

### Steg 4 – Bekreft og lagre

Spør: **"Skal jeg lagre disse lærdommene til minnefilene?"**

Hvis ja:
1. Skriv minnefiler til `C:/Users/frtv/.claude/projects/C--Users-frtv/memory/<filnavn>.md`
2. Oppdater `C:/Users/frtv/.claude/projects/C--Users-frtv/memory/MEMORY.md`
3. **Marker sesjonen som analysert:**

```bash
python C:/DIPS/_git/session-optimizer/session_optimizer.py \
  --mark-analyzed <uuid> \
  --operation-type <operasjonstype> \
  --memory-files <filnavn1.md,filnavn2.md>
```

UUID finnes i metadata-linjen fra Steg 1 (`"uuid": "..."`).

Minnefil-format:
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

Fortell hva som ble lagret, hvilken sesjon som ble markert som analysert, og hvilke token-besparelser dette gir neste gang.

Ved `--analyze-all`: fortsett med neste uanalyserte sesjon.

---

## Viktige noter

- Skriptet gjør ingen API-kall – Claude analyserer selv i sesjonen
- Sesjoner med færre enn 3 tool calls er ikke verdt å analysere – hopp over
- `~/.claude/session-optimizer-history.json` sporer hvilke sesjoner som er analysert
- Minnefilene leses automatisk i neste sesjon via MEMORY.md-indeksen
- `--list` viser ✓ for allerede analyserte sesjoner
