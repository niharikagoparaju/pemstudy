---
name: triage
description: Use when working through pre-existing/legacy Anki cards that predate the plugin — staging old decks into the triage holding pen, organizing them by the content outline, or promoting worthy cards into the active study deck ("triage my old cards", "let's do trauma", "promote these", "what's left to triage").
---

# pemstudy triage — legacy cards → active deck

A one-way gate that lets a large legacy collection be digested slowly without ever
flooding the daily review queue.

```
legacy source decks ──stage──▶ PEM Triage::NN <Domain>  ──promote──▶ PEM Boards (ABP)::NN <Domain>
                               (suspended, never reviewed)            (active; also fed by sync)
```

**REQUIRED READING:**
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/ankiconnect.md` — CLI usage, safety rules,
  note-id vs card-id
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/dedupe.md` — duplicate judgment (promote)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/card-quality.md` — is this card worth keeping
- `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml` — domains, subdomains,
  competency descriptions (the descriptions are the best classification signal)

Config: `~/.pemstudy/config.json` → `deck_root` (active), `triage_deck_root`
(default `"PEM Triage"` when absent), `legacy_decks` (source decks; ask the user if
absent). `ping` before any work.

## The invariant

**Everything in the triage deck is suspended. Promotion is what unsuspends it.**

A suspended card cannot enter review no matter which deck gets clicked or how deck
options are set. Never unsuspend a triage card except as part of an approved promote.
Never `create-deck` a triage subdeck without immediately suspending what lands in it.

## Safety contract

Same as the deck skill: **dry-run → explicit approval → backup → execute → verify.**
Back up before every mutating batch:

```bash
ANKI export-backup "$HOME/.pemstudy/backups/pre-<op>-$(date +%Y%m%d-%H%M%S).apkg" --deck "<source or triage deck>"
```

Scope is the configured legacy source decks + the triage root + the active root.
Nothing else.

## Operation: stage (one-time, per source subdeck)

Work **one source subdeck at a time** — the subdeck name is a strong prior
(`PBR Cardiology` → Domain 10) so most notes are mechanical and only misfits need
deliberation.

1. **Pull the subdeck's own cards** (not its children):

   ```bash
   ANKI invoke findCards --json '{"query":"\"deck:PED BOARDS::PBR Cardiology\" -\"deck:PED BOARDS::PBR Cardiology::*\""}'
   ```

   Then `notes-info` on the *note* ids to read content.

2. **Classify each NOTE to one domain** (domain-level only — subdomain waits for
   promote). Match content against the outline's competency descriptions. The source
   subdeck is a prior, not an answer: a "PBR Cardiology" card about syncope belongs to
   Domain 02 Resuscitation (F. Syncope and loss of consciousness).

   **No-fit → skip it.** Cards outside the PEM outline (developmental milestones,
   vaccines, well-child guidance) stay untouched in their source deck. Staging is not
   a place to park things "just in case" — an unstaged card costs nothing, a staged
   one costs triage attention later.

3. **Dry-run table**: source subdeck → per-domain counts, plus the skip list with
   reasons. Show representative examples, not all 90 rows.

4. **On approval**: backup → `create-deck` only the `PEM Triage::NN <Domain>` decks
   this batch actually needs → for each note, gather **all** its card ids
   (`notes-info` → `cards`) → `change-deck` them together → `suspend` them →
   `add-tags`:
   - `pem::outline::<domain-slug>` (domain-level)
   - `pem::legacy::<source-deck-slug>` (provenance: lowercase, non-alphanumerics → `-`,
     e.g. `PED BOARDS::PBR Cardiology` → `pem::legacy::pbr-cardiology`)

5. **Verify**: `are-suspended` on the moved cards returns all true; source subdeck
   count dropped by exactly the staged count; report both.

## Operation: promote (recurring, one domain at a time)

1. **Pick the batch**: remaining work in a domain is

   ```bash
   ANKI find '"deck:PEM Triage::01 Trauma" -tag:pem::triage::rejected'
   ```

   Take ~40–60 notes. More than that and judgment degrades; say how many remain.

2. **Judge each note**, reading it fully:
   - **Duplicate** of an active card or of another note in this batch → drop
     (per `dedupe.md`; name the card that covers it)
   - **Inaccurate / outdated** → drop, or propose a corrected version to promote.
     High confidence bar; cite the specific problem. Never silently rewrite medicine.
   - **Low value** per `card-quality.md` (non-atomic, recognition-only, trivia) → drop,
     or propose a rewrite
   - **Keep** → assign the subdomain from the outline
3. **Dry-run table**: promote (with subdomain) / drop-duplicate / drop-inaccurate /
   drop-low-value / needs-edit. The user approves, narrows, or overrides any row.
4. **On approval**, per promoted note: backup → `change-deck` all its cards to
   `<deck_root>::NN <Domain>` → `unsuspend` → `forget` (reset to new, so it enters via
   the new-cards/day limit instead of landing due) → retag:
   - `remove-tags` the domain-level `pem::outline::<domain-slug>`
   - `add-tags` `pem::outline::<domain-slug>::<subdomain-slug>`
   - keep `pem::legacy::<source>` (provenance survives promotion)
5. **Dropped notes**: `add-tags pem::triage::rejected`. They stay in triage, suspended
   — non-destructive and revisitable. Deleting them is a separate, explicit request.
6. **Verify and report**: promoted cards are `type: 0` / `interval: 0` in `cards-info`;
   count still awaiting triage in this domain; count promoted to date.

## Common mistakes

- **Moving some of a note's cards but not all** — a Cloze note has one card per
  deletion; `change-deck` takes card ids. Always classify per note and move the whole
  set from `notes-info` → `cards`, or the note splits across decks.
- Unsuspending anything outside an approved promote — that silently breaks the one
  guarantee this whole design provides.
- Preserving scheduling on promote. `forget` is deliberate: legacy cards are lapsed,
  their intervals are meaningless, and skipping the reset dumps them straight into the
  due queue — exactly what the triage deck exists to prevent.
- Staging borderline cards to "decide later" — decide now, skip if no fit.
- Trusting the source subdeck name over card content for classification.
- Converting note types during promotion. Promoted cards keep their native type
  (Basic/Cloze/genanki variants); the `pem::outline::*` tags carry what audit and
  dedupe need. Conversion is a separate opt-in operation.
- Promoting a whole domain in one sitting because it "looks easy" — the batch limit
  protects judgment quality, which is the only thing making this better than an import.
