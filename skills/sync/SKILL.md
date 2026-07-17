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

Config from `~/.pemstudy/config.json` (missing → send the user to the setup skill).
Verify Anki is reachable (`ping`) before doing any work.

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
   - for images: resolve `![[...]]` to a real file in the vault (search by filename —
     Obsidian may store attachments in a subfolder). **Look at the image** before
     using it: confirm it actually shows what the note implies and contains no
     patient-identifying information (names, MRNs, faces). Unverifiable → propose the
     card without the image and say why.
4. **Fact-check yourself**: card content must be medically accurate, not just a
   faithful copy of the note. If the note contradicts established guidance
   (typo'd dose, swapped terms), flag it to the user instead of carding the error.

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
