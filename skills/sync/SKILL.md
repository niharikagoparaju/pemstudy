---
name: sync
description: Use when the user wants to turn Obsidian journal/study notes into Anki flashcards, sync their vault to their deck, or process notes from a question-bank session (e.g. "sync my notes", "make cards from what I studied", "update my anki from obsidian").
---

# pemstudy sync — journal notes → Anki cards

Parse new/changed vault notes, propose high-quality cards, dedupe against the
existing deck, create approved cards in Anki, and record sync state in the notes.

**REQUIRED READING before executing:**
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/ankiconnect.md` (CLI usage + safety)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/card-quality.md` (what to propose)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/note-convention.md` (parsing + sync state)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/dedupe.md` (duplicate judgment)
- `${CLAUDE_PLUGIN_ROOT}/skills/shared/preferences.md` (user card preferences)

Config from `~/.pemstudy/config.json` (missing → send the user to the setup skill).
Verify Anki is reachable (`ping`) before doing any work.

Load user card preferences once, up front, and apply them to every proposal in
step 2 (see `preferences.md` for precedence — they refine card-quality, never override
accuracy/dedup):

```bash
[ -f "$HOME/.pemstudy/preferences.md" ] && cat "$HOME/.pemstudy/preferences.md"
```

## Flow

### 1. Find sync candidates

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sync/scan.py"
```

Prints `CANDIDATE-NEW` / `CANDIDATE-EDITED` / `OK` per note (see its docstring).
Do not hand-roll this scan in shell — date/timezone parsing in shell is fragile.
List candidates to the user before proceeding; let them narrow the selection
("just the tox notes").

### 2. Parse and propose

For each candidate note:

1. Read it fully. Identify distinct question/topic chunks and any retain/skip markers.
2. For a previously-synced note, fetch its `pem_anki_notes` via `notes-info` and
   only propose cards for material not already covered by those cards.
3. Draft cards per the card-quality guide. For each card decide:
   - note type (PEM Basic / PEM Cloze / PEM Image Identify)
   - content-outline classification: pick the domain + subdomain from
     `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml` that best matches the
     medical content (folder name is a prior, content wins). Deck =
     `<deck_root>::<NN> <Domain Name>`; tag = `pem::outline::<domain-slug>::<subdomain-slug>`;
     Outline field = human-readable `Domain > Subdomain > Topic`.
   - for images: resolve per `note-convention.md` (vault embeds *and* remote
     question-bank URLs — most are remote). **Download and look at every image**
     before building a card from it: confirm it shows what the note implies, contains
     no patient-identifying information, and doesn't print the answer on its face
     (which rules out an identify-card). Unviewable → propose the card without the
     image and say why.
4. **Fact-check yourself**: card content must be medically accurate, not just a
   faithful copy of the note. Two failure modes seen in real notes, both of which
   must be surfaced rather than carded:
   - **The note contradicts its own pasted source** (e.g. two branches of an
     algorithm swapped). Show the user note-vs-source side by side and let them rule.
   - **Adult figures on a pediatric card** (e.g. adult ATLS thresholds, an UpToDate
     adult protocol). Flag the provenance; a peds-wrong number is a wrong answer.
   Never silently rewrite the user's medicine, and never silently card what you
   believe is false.

### 3. Dedupe against the existing deck

For each proposed card, search existing notes before adding and judge duplication per
`${CLAUDE_PLUGIN_ROOT}/skills/shared/dedupe.md` (search patterns and the keeper test
are there — don't re-derive them).

Duplicate → drop the proposal and note which existing card covers it. Near-duplicate
where the new card is better → propose *updating* the existing note instead of adding.

### 4. Batch review with the user

Present ALL proposals in one compact table before creating anything:

| # | Deck | Type | Front/Text | Back/Answer | Image | Note |
|---|------|------|------------|-------------|-------|------|

Plus: dropped duplicates (and why), skipped content (markers), flagged accuracy
concerns. Let the user approve all, drop by number, or edit wording. **No cards are
created before approval.**

If the user's edits are a **durable** preference ("from now on keep these terse",
"always cloze the doses"), offer to save it to `~/.pemstudy/preferences.md` so future
syncs honor it — don't auto-write, and don't persist a one-off ("just these").

### 5. Create

For approved cards, in order:

1. `store-media` each image first, named `pem-<topic>-<yyyymmdd>.<ext>`; reference
   as `<img src="...">` in the Image/Front field.
2. `add-notes` with the full batch (deckName, modelName, fields incl. `Source` =
   vault-relative path, `Outline`, tags: outline tag + `pem::source::<note-slug>`).
3. Check the returned ids: `null` entries = rejected notes — report them, don't
   silently swallow.

### 6. Write back sync state

For each processed note — **including zero-yield notes** (no card-worthy content),
so they stop showing up as candidates — update frontmatter (preserve all other keys):

```yaml
pem_synced: <timestamp — see below>
pem_anki_notes: [<existing ids…>, <new ids…>]   # omit for zero-yield notes
```

**Generate the timestamp — never hand-write it** (a wrong hand-written timezone
offset silently breaks candidate detection):

```bash
TS_TZ=$(date +%Y-%m-%dT%H:%M:%S%z)   # value for pem_synced
TS=$(date +%Y-%m-%dT%H:%M:%S)        # same wall-clock, for touch
```

After the frontmatter edit, reset the file's mtime to match — the edit itself
bumps mtime past `pem_synced`, which would re-candidate the note forever:

```bash
touch -m -d "$TS" "<note path>"
```

### 7. Report

Cards created per deck, duplicates dropped, accuracy flags, notes updated. Suggest
`ANKI export-backup` if this was a large batch.

## Common mistakes

- Creating cards before the user approved the batch.
- Trusting the note's folder over the card's actual content for outline classification.
- Attaching an image you never looked at.
- Carding everything in a note — the retain/skip markers and card-quality rules exist
  to keep the deck lean.
- Overwriting user frontmatter keys or dropping existing `pem_anki_notes` ids.
- Forgetting `store-media` before `add-notes` (broken `<img>` references).
