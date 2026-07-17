---
name: triage
description: Use when working through pre-existing/legacy Anki cards that predate the plugin — staging old decks into the legacy deck, organizing them by the content outline, or approving worthy cards into review ("triage my old cards", "let's do trauma", "promote these", "what's left to triage").
---

# pemstudy triage — digesting a legacy collection

Lets a large legacy collection be digested slowly without ever flooding the daily
review queue, and **without ever mixing legacy cards into the note-derived deck**.

```
legacy source decks ──stage──▶  PEM Legacy::NN <Domain>
                                  suspended  = not yet triaged
                                  unsuspended = approved, in rotation   ◀── promote (in place)

PEM Notes::NN <Domain>          ← note-derived cards ONLY, fed by sync from Obsidian
```

**The two trees never exchange cards.** `deck_root` holds exactly what came from the
vault; `legacy_deck_root` holds exactly what came from the old collection. Promotion
does **not** move a card between trees — it unsuspends it where it sits. This keeps
each source's review load on its own new-cards/day dial and makes provenance
obvious at a glance.

**REQUIRED READING:**
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/ankiconnect.md` — CLI usage, safety rules,
  note-id vs card-id
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/dedupe.md` — duplicate judgment (promote)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/card-quality.md` — is this card worth keeping
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/preferences.md` — user card preferences (apply
  when proposing rewrites/corrections during promote)
- `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml` — domains, subdomains,
  competency descriptions (the descriptions are the best classification signal)

Config: `~/.pemstudy/config.json` → `deck_root` (note-derived deck — **never write to
it here**), `legacy_deck_root` (default `"PEM Legacy"` when absent), `legacy_decks`
(source decks; ask the user if absent). `ping` before any work.

## The invariants

1. **Staged cards land suspended. Promotion is what unsuspends them.** A suspended
   card cannot enter review no matter which deck gets clicked or how deck options are
   set. Never unsuspend a legacy card except as part of an approved promote, and never
   `create-deck` a legacy subdeck without immediately suspending what lands in it.
2. **Never put a legacy card into `deck_root`.** That deck is note-derived only. If a
   legacy card would duplicate or improve a note-derived card, say so and let the user
   decide — don't move it across.

Within the legacy tree, state is carried by the suspend flag, not by the deck:

| Query | Meaning |
|---|---|
| `"deck:<legacy_deck_root>" is:suspended -tag:pem::triage::rejected` | awaiting triage |
| `"deck:<legacy_deck_root>" -is:suspended` | approved, in rotation |
| `"deck:<legacy_deck_root>" tag:pem::triage::rejected` | rejected (suspended, kept for reference) |

## Safety contract

Same as the deck skill: **dry-run → explicit approval → backup → execute → verify.**
Back up before every mutating batch:

```bash
ANKI export-backup "$HOME/.pemstudy/backups/pre-<op>-$(date +%Y%m%d-%H%M%S).apkg" --deck "<source or legacy deck>"
```

Scope is the configured legacy source decks + `legacy_deck_root`. **`deck_root` is
read-only here** — the only reason to query it is duplicate-checking during promote.

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

4. **On approval**: backup → `create-deck` only the `<legacy_deck_root>::NN <Domain>`
   decks this batch actually needs → for each note, gather **all** its card ids
   (`notes-info` → `cards`) → `change-deck` them together → `suspend` them →
   `add-tags`:
   - `pem::outline::<domain-slug>` (domain-level)
   - `pem::legacy::<source-deck-slug>` (provenance: lowercase, non-alphanumerics → `-`,
     e.g. `PED BOARDS::PBR Cardiology` → `pem::legacy::pbr-cardiology`)

5. **Verify**: `are-suspended` on the moved cards returns all true; source subdeck
   count dropped by exactly the staged count; report both.

## Operation: promote (recurring, one domain at a time)

Promotion **unsuspends in place**. No card moves between deck trees.

1. **Pick the batch**: remaining work in a domain is

   ```bash
   ANKI find '"deck:PEM Legacy::01 Trauma" is:suspended -tag:pem::triage::rejected'
   ```

   Take ~40–60 notes. More than that and judgment degrades; say how many remain.

2. **Judge each note**, reading it fully:
   - **Broken** — empty back / no answer. Common in imported decks (20% of one real
     source subdeck). Reject unless the question is worth rewriting; list them either
     way, since many are good questions with a missing answer.
   - **Duplicate** of another legacy note, or of a note-derived card in `deck_root`
     → reject (per `dedupe.md`; name the card that covers it). A legacy card that is
     *better* than its `deck_root` twin is a judgment call for the user — surface it,
     never silently move it across trees.
   - **Inaccurate / outdated** → reject, or propose a correction to apply before
     promoting. High confidence bar; cite the specific problem. Never silently rewrite
     medicine.
   - **Low value** per `card-quality.md` (non-atomic, recognition-only, trivia)
     → reject, or propose a rewrite
   - **Keep** → assign the subdomain from the outline
3. **Dry-run table**: promote (with subdomain) / reject-broken / reject-duplicate /
   reject-inaccurate / reject-low-value / needs-edit. The user approves, narrows, or
   overrides any row.
4. **On approval**, per promoted note: backup → `unsuspend` all its cards → `forget`
   (reset to new, so it enters via the new-cards/day limit instead of landing due)
   → retag:
   - `remove-tags` the domain-level `pem::outline::<domain-slug>`
   - `add-tags` `pem::outline::<domain-slug>::<subdomain-slug>`
   - keep `pem::legacy::<source>` (provenance is permanent)
5. **Rejected notes**: `add-tags pem::triage::rejected`, leave suspended in place —
   non-destructive and revisitable. Deleting them is a separate, explicit request.
6. **Verify and report**: promoted cards are `type: 0` / `interval: 0` and unsuspended
   in `cards-info`; count still awaiting triage in this domain; count promoted to date.
   Confirm `deck_root` is unchanged.

## Common mistakes

- **Promoting a card INTO `deck_root`.** The two trees stay separate; promotion
  unsuspends in place. Mixing sources in one deck destroys both the provenance
  signal and the ability to pace each source independently.
- **Moving some of a note's cards but not all** — a Cloze note has one card per
  deletion; `change-deck` takes card ids. Always classify per note and move the whole
  set from `notes-info` → `cards`, or the note splits across decks.
- Unsuspending anything outside an approved promote — that silently breaks the one
  guarantee this whole design provides.
- Preserving scheduling on promote. `forget` is deliberate: legacy cards are lapsed,
  their intervals are meaningless, and skipping the reset dumps them straight into the
  due queue — exactly what the legacy deck's suspend gate exists to prevent.
- Staging borderline cards to "decide later" — decide now, skip if no fit.
- Trusting the source subdeck name over card content for classification. Measured on
  real decks: only ~26% of a "PBR Dermatology" subdeck was actually Dermatologic (most
  was Infectious Diseases), and a "PEM ATLS" subdeck was 24% non-Trauma.
- Converting note types during promotion. Promoted cards keep their native type
  (Basic/Cloze/genanki variants); the `pem::outline::*` tags carry what audit and
  dedupe need. Conversion is a separate opt-in operation.
- Promoting a whole domain in one sitting because it "looks easy" — the batch limit
  protects judgment quality, which is the only thing making this better than an import.
