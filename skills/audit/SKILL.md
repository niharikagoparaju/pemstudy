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

For each of the 13 domains, count notes in its subdeck (plugin-managed cards) —
one `find` per domain:

```bash
ANKI find '"deck:<deck_root>::01 Emergency Conditions"'   # count ids per domain
```

If the user also wants legacy/hand-built decks counted, they must name them; map
each named deck to a domain by content and say what mapping was assumed.

### 2. Subdomain resolution (Domain 1 and on request)

Domain 1 is a third of the exam and has weighted subdomains — always break it down
by tag:

```bash
ANKI find 'tag:pem::outline::01-emergency-conditions::h-infectious-disease'
```

Cards missing outline tags: count them as "unclassified" and suggest the deck
skill's retagging operation.

### 3. Report

Render one table, sorted by (exam weight − card share) descending — biggest gaps
first:

| Domain | Exam weight | Cards | Card share | Δ |
|---|---|---|---|---|

- **Card share** = domain cards / total cards (show `0` rows too — untouched
  domains are the headline).
- Flag domains with zero cards and subdomains of Domain 1 with zero cards.
- Include review-state color if the user asks (e.g. `is:new` vs mature counts per
  domain via `find` with `-is:new` etc.).

### 4. Recommend

Close with 2–4 concrete suggestions tied to the data, e.g. "Trauma is 17.5% of the
exam and you have 0 cards — prioritize trauma question blocks next" or "Infectious
disease (5% weight) has 40% of your Domain-1 cards — coverage is lopsided, not
wrong". Keep it descriptive; the user decides what to study.

## Interpretation cautions

- Card count ≈ effort, not mastery. Don't present the table as a readiness score.
- Small collections make percentages noisy — report absolute counts alongside.
- Exam weight parity is not the goal per se (some domains need fewer cards per
  point); the deltas surface *neglect*, not a quota.
