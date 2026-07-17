---
name: audit
description: Use when the user wants to see how their Anki deck coverage compares to the PEM boards exam blueprint — coverage reports, weak/thin domains, what to study next, "am I covering the right things", or progress stats against the content outline.
---

# pemstudy audit — coverage vs the exam blueprint

Compare the user's card distribution against the ABP content-outline exam weights
and show where they're thin.

Inputs: `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml` (domains, weights,
subdomains) and the live collection via
`${CLAUDE_PLUGIN_ROOT}/skills/shared/ankiconnect.md` conventions. Config from
`~/.pemstudy/config.json`; `ping` first.

## Flow

### 1. Count cards per domain

For each of the 28 domains, count notes in its subdeck (plugin-managed cards) —
one `find` per domain:

```bash
ANKI find '"deck:<deck_root>::01 Trauma"'   # count ids per domain
```

If the user also wants legacy/hand-built decks counted, they must name them; map
each named deck to a domain by content and say what mapping was assumed.

### 2. Count the triage backlog per domain

If a `PEM Triage` tree exists (see the triage skill), count what's still waiting:

```bash
ANKI find '"deck:<triage_deck_root>::01 Trauma" -tag:pem::triage::rejected'
```

Report it as its own column — it answers "which domain should I promote next",
which is usually the more actionable question than the gap itself. Skip this
section entirely when no triage deck exists.

### 3. Subdomain resolution (top-weighted domains and on request)

Subdomains carry no individual weights in this outline, so don't invent shares for
them. Break down the heaviest domains — Trauma (17%), Resuscitation (10%),
Infectious Diseases (8%) — so lopsided coverage inside a big domain is visible.

**Always scope tag queries by deck.** A bare `tag:` query also matches suspended
triage cards (which carry outline tags) and silently inflates the report:

```bash
ANKI find '"deck:<deck_root>" tag:pem::outline::01-trauma::e-head-brain-injuries'
```

Two kinds of gap are worth reporting separately:

```bash
# no outline tag at all -> deck skill's retagging operation
ANKI find '"deck:<deck_root>" -tag:pem::outline::*'
# domain-tagged but never subdomain-classified (tag: search is hierarchical, so the
# -tag:...::* exclusion is what isolates the bare parent)
ANKI find '"deck:<deck_root>" tag:pem::outline::01-trauma -tag:pem::outline::01-trauma::*'
```

(Triage cards carry only a domain-level tag until promoted — that's by design, not a
gap, and the deck scoping above already excludes them.)

### 4. Report

Render one table, sorted by (exam weight − card share) descending — biggest gaps
first. Drop the Triage column when there's no triage deck:

| Domain | Exam weight | Cards | Card share | Δ | Triage |
|---|---|---|---|---|---|

- **Card share** = active-deck domain cards / total active cards (show `0` rows too —
  untouched domains are the headline).
- Flag domains with zero cards.
- **Triage** = notes awaiting promotion. A domain with a big gap *and* a big triage
  backlog is cheap to fix (promote); a big gap with an empty backlog needs new
  question blocks. That distinction is the point of the column.
- Include review-state color if the user asks (e.g. `is:new` vs mature counts per
  domain via `find` with `-is:new` etc.).

### 5. Recommend

Close with 2–4 concrete suggestions tied to the data, distinguishing the two fixes:
"Trauma is 17% of the exam, you have 4 cards, and 143 are waiting in triage —
promote, don't grind new questions" vs "Resuscitation is 10% with 0 cards and an
empty backlog — needs question blocks". Keep it descriptive; the user decides.

## Interpretation cautions

- Card count ≈ effort, not mastery. Don't present the table as a readiness score.
- Small collections make percentages noisy — report absolute counts alongside.
- Exam weight parity is not the goal per se (some domains need fewer cards per
  point); the deltas surface *neglect*, not a quota.
