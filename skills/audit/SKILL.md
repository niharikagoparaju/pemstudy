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

### 2. Count the legacy tree per domain

If a `PEM Legacy` tree exists (see the triage skill), count both of its states —
they mean different things:

```bash
# approved and in rotation (counts toward what you're actually studying)
ANKI find '"deck:<legacy_deck_root>::01 Trauma" -is:suspended'
# still waiting to be triaged
ANKI find '"deck:<legacy_deck_root>::01 Trauma" is:suspended -tag:pem::triage::rejected'
```

Report **Live** and **Waiting** as separate columns. "Waiting" answers "which domain
should I triage next", which is usually more actionable than the gap itself. Skip this
section entirely when no legacy deck exists.

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

Render one table, sorted by (exam weight − note-derived share) descending — biggest
gaps first. Drop the last two columns when there's no legacy deck:

| Domain | Exam weight | Notes | Share | Δ | Legacy live | Waiting |
|---|---|---|---|---|---|---|

- **Notes / Share** = the note-derived deck (`deck_root`) only — that's the deck the
  user's daily habit builds, so it's the honest measure of their own coverage. Show
  `0` rows too; untouched domains are the headline.
- **Legacy live** = approved legacy cards in rotation. Real study volume, but not
  something the user wrote — keep it a separate column, never folded into Share.
- **Waiting** = staged but untriaged. A domain with a big gap *and* a big waiting
  pile is cheap to fix (triage it); a big gap with nothing waiting needs new question
  blocks. That distinction is the point of these columns.
- Flag domains with zero cards of any kind.
- Include review-state color if the user asks (e.g. `is:new` vs mature counts per
  domain via `find` with `-is:new` etc.).

### 5. Recommend

Close with 2–4 concrete suggestions tied to the data, distinguishing the two fixes:
"Trauma is 17% of the exam, you have 4 cards, and 143 are waiting in the legacy deck —
triage those, don't grind new questions" vs "Resuscitation is 10% with 0 cards and
nothing waiting — needs question blocks". Keep it descriptive; the user decides.

## Interpretation cautions

- Card count ≈ effort, not mastery. Don't present the table as a readiness score.
- Small collections make percentages noisy — report absolute counts alongside.
- Exam weight parity is not the goal per se (some domains need fewer cards per
  point); the deltas surface *neglect*, not a quota.
