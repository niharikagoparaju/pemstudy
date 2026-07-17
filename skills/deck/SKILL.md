---
name: deck
description: Use when the user wants to manage, organize, clean up, or fact-check their Anki decks — find duplicate cards, prune or delete cards, flag inaccurate cards, retag or move cards, reorganize deck structure, or check cards against the PEM boards content outline.
---

# pemstudy deck — conversational deck management

Operate on the user's Anki collection per their instructions, safely.

**REQUIRED READING:** `${CLAUDE_PLUGIN_ROOT}/skills/shared/ankiconnect.md` — especially
the safety rules and the note-id vs card-id gotcha. Card standards:
`${CLAUDE_PLUGIN_ROOT}/skills/shared/card-quality.md`. Outline taxonomy:
`${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml`.

Config from `~/.pemstudy/config.json`; `ping` before any work.

## The safety contract (non-negotiable)

Every mutating operation follows **dry-run → approve → backup → execute → verify**:

1. **Dry-run**: fetch and show the user exactly which notes/cards will change —
   a table with note id, front/first line, deck, and the planned action.
2. **Approve**: explicit user approval of that list (or a narrowed subset).
   No approval, no mutation.
3. **Backup** (destructive ops — delete, bulk field edits, bulk moves):
   ```bash
   ANKI export-backup "$HOME/.pemstudy/backups/pre-<op>-$(date +%Y%m%d-%H%M%S).apkg" --deck "<deck_root>"
   ```
   Tell the user the backup path and that File → Import restores it.
4. **Execute**, then **verify** with a fresh query and report actual counts.

Scope: only decks under `deck_root` unless the user explicitly names another deck.
When the user asks for something in their other decks (e.g. a hand-built legacy
tree), confirm the deck name back to them before touching it.

## Operations

### Duplicate scan

1. Pull candidates: `ANKI find '"deck:<deck_root or subdeck>"'` → `notes-info`
   in batches (~100).
2. Judge **semantic** duplication: same fact tested, even with different wording,
   different note types, or Q&A vs cloze form. Group duplicates together.
3. For each group recommend a keeper (better wording per card-quality guide, richer
   Extra/Source) and losers. If the loser has scheduling history worth keeping
   (mature card vs brand-new duplicate), keep the mature one's note and merge wording.
4. Dry-run table → approval → backup → `delete-notes` the losers.

### Accuracy review

1. Fetch notes in the scope the user names (subdeck, tag, or "everything recent").
2. Check each card's medical claim against your knowledge. **Only flag what you are
   confident is wrong or outdated** (wrong dose, swapped terms, superseded guideline);
   cite why. Uncertain → say so, don't guess; suggest the user verify.
3. Never silently "fix" medical content: present current text vs proposed text side
   by side, get approval, then `update-note`.
4. Tag anything the user wants to revisit later: `pem::flagged::inaccurate`.

### Outline fit / retagging

1. For cards missing `pem::outline::*` tags (e.g. imported or legacy cards), classify
   content against the outline YAML and propose: tag + move to the matching domain
   subdeck.
2. Cards that fit no domain: list them as off-outline; the user decides
   (keep-as-is, move to a non-board deck, or delete).
3. Apply with `add-tags` / `change-deck` (remember: change-deck takes **card** ids
   from `notes-info` → `cards`).

### Prune / reorganize per instruction

For ad-hoc requests ("delete everything I've suspended", "merge these two subdecks",
"move all bronchiolitis cards to Pulmonary"): translate to queries (Anki search
syntax: `is:suspended`, `added:30`, `rated:7:1`, `tag:...`, `deck:...`), then run the
safety contract. For operations `anki.py` lacks a subcommand for, use
`ANKI invoke <action>` (e.g. `guiBrowse` to show the user a selection in Anki's own
browser before acting).

## Common mistakes

- Mutating anything without the dry-run table being approved first.
- Skipping the backup because the batch "is small".
- Passing note ids to `change-deck`/`cards-info` (they take card ids).
- Flagging cards as inaccurate on weak grounds — confidence threshold is high;
  the user's review time is the scarce resource.
- Treating literal-text difference as non-duplicate — duplication is semantic.
- Touching decks outside `deck_root` without explicit naming + confirmation.
