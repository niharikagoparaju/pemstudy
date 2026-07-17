# Journal note conventions and sync state

The journal is an Obsidian vault (plain Markdown). Notes are **free-form** — the sync
skill must parse whatever the user wrote. The conventions below are *hints the user
may use*, not requirements; honor them when present.

## Layout hints

- **Folders often mirror question-bank sections** (e.g. `Trauma/`, `Toxicology/`).
  Use the folder name as a prior for the content-outline domain, but classify each
  card by its actual content.
- A note may contain **one or many questions** from a study session.
- Embedded images use Obsidian syntax: `![[Pasted image 20260714194009.png]]` or
  `![alt](path.png)`. Resolve them relative to the vault root (Obsidian may also put
  them in an attachments subfolder — search the vault for the filename).

## Retain markers (user intent)

When the user marks content, respect it:

| Marker in note | Meaning |
|---|---|
| `**Keep:**`, `Retain:`, `Card:`, `#card` | Definitely make card(s) from this |
| `skip`, `#skip`, `%%skip%%`, "already know" | Do NOT make cards from this |
| No marker | Use judgment per the card-quality guide |

## Sync-state frontmatter (written by the sync skill)

After cards are created from a note, the sync skill writes YAML frontmatter:

```yaml
---
pem_synced: 2026-07-16T14:30:00-04:00   # ISO timestamp of last successful sync
pem_anki_notes: [1784258534639, 1784258534640]  # Anki note ids created from this note
---
```

Rules:

- A note is a **sync candidate** when `pem_synced` is missing, or the file's mtime is
  newer than `pem_synced` (the user edited it since the last sync).
- **After writing frontmatter, reset the file's mtime to match `pem_synced`**
  (`touch -m -d "<same wall-clock timestamp>" "<file>"`) — the frontmatter edit itself
  bumps mtime past `pem_synced`, which would make every synced note a perpetual
  candidate. Generate both timestamps from `date` in one shot; never hand-write them
  (a wrong timezone offset silently breaks candidate detection).
- **Zero-yield notes get `pem_synced` too.** A note processed and found to contain no
  card-worthy content (non-medical notes, empty files) is still marked synced (with no
  `pem_anki_notes`) so it stops appearing as a candidate; editing it re-candidates it
  via the mtime rule.
- On re-sync of an edited note: fetch the existing `pem_anki_notes` with `notes-info`
  first — only propose cards for *new* material; never recreate cards that already
  exist (some ids may have been deleted by the user in Anki; ignore missing ids).
- **Append** new note ids to `pem_anki_notes`; never drop existing ids.
- Preserve any other frontmatter keys the user has; only touch the two `pem_*` keys.
- Skip non-note files: anything in `.obsidian/`, `.trash/`, and templates. Skip
  empty files entirely (don't even mark them — nothing to record).

## Anki-side provenance

Every created Anki note carries:

- `Source` field: vault-relative note path (+ short question ref if the note has many)
- Tag `pem::source::<note-slug>` where `<note-slug>` is the note filename, lowercased,
  spaces → `-`, extension dropped (e.g. `Trauma/Burns day 2.md` → `pem::source::burns-day-2`)
- Tag `pem::outline::<domain-slug>::<subdomain-slug>` from
  `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml`

This makes every card traceable in both directions: note → `pem_anki_notes`,
card → `Source`/`pem::source::` tag.
