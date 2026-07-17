# AnkiConnect cookbook for pemstudy skills

All Anki access goes through `${CLAUDE_PLUGIN_ROOT}/scripts/anki.py` (Python 3 stdlib only).
Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/anki.py" --help` for the full subcommand list.

## Preconditions

- Anki desktop must be **open** with the right profile loaded.
- AnkiConnect add-on installed (code `2055492159`). `ping` verifies both:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/anki.py" ping
# → {"ankiconnect_version": 6}   on success
# → clear error on stderr, exit 1, when Anki is closed or the add-on is missing
```

If ping fails: ask the user to open Anki. If it still fails, the add-on is missing —
have them install it (Tools → Add-ons → Get Add-ons → `2055492159` → restart Anki),
then re-ping.

## Config

`~/.pemstudy/config.json` (created by the setup skill):

```json
{
  "vault_path": "/path/to/obsidian/vault",
  "deck_root": "PEM Boards",
  "ankiconnect_url": "http://127.0.0.1:8765"
}
```

`anki.py` reads `ankiconnect_url` itself. Skills read `vault_path` and `deck_root`.

## Common operations

Define a shell *function* (not a variable — variables don't word-split under zsh):

```bash
ANKI() { python3 "${CLAUDE_PLUGIN_ROOT}/scripts/anki.py" "$@"; }

# Deck / model discovery
ANKI decks
ANKI models
ANKI model-fields "PEM Basic"

# Search (Anki query syntax; quote the whole query)
ANKI find 'deck:"PEM Boards::01 Trauma"'
ANKI find 'tag:pem::outline::07-toxicology::a-toxicology-concepts'
ANKI find '"deck:PEM Boards" added:7'          # added in last 7 days
ANKI notes-info 1234567890 1234567891           # fields + tags for note ids
ANKI cards-info 1234567890                      # deck, scheduling info for card ids

# Create
ANKI create-deck "PEM Boards::07 Toxicology"    # idempotent; :: nests
ANKI add-note --json '{
  "deckName": "PEM Boards::07 Toxicology",
  "modelName": "PEM Basic",
  "fields": {"Front": "...", "Back": "...", "Extra": "", "Source": "...", "Outline": "..."},
  "tags": ["pem::outline::07-toxicology::a-toxicology-concepts", "pem::source::2026-07-15-tox"],
  "options": {"allowDuplicate": false}
}'
ANKI add-notes --json '[ {note}, {note} ]'      # returns list of ids; null = rejected (e.g. exact dup)

# Media: store BEFORE adding the note that references it
ANKI store-media "/vault/Pasted image 20260714194009.png" --name "pem-sjs-rash-20260714.png"
# then reference in a field as: <img src="pem-sjs-rash-20260714.png">

# Modify
ANKI update-note --json '{"id": 123, "fields": {"Back": "..."}, "tags": ["..."]}'
ANKI add-tags --notes 123,456 --tags "pem::flagged::inaccurate"
ANKI remove-tags --notes 123,456 --tags "pem::flagged::inaccurate"
ANKI change-deck --cards 123,456 --deck "PEM Boards::01 Trauma"   # takes CARD ids, not note ids

# Destructive — ALWAYS export a backup first (see Safety)
ANKI export-backup "$HOME/.pemstudy/backups/pre-prune-$(date +%Y%m%d-%H%M%S).apkg" --deck "PEM Boards"
ANKI delete-notes 123 456

# Escape hatch for any other AnkiConnect action
ANKI invoke deleteDecks --json '{"decks":["Some Deck"],"cardsToo":true}'
ANKI invoke getTags
ANKI invoke findCards --json '{"query":"deck:current"}'
```

## Gotchas

- **Note ids vs card ids**: `find`/`notes-info`/`delete-notes`/tag ops use *note* ids;
  `cards-info`/`change-deck` use *card* ids. For our note types they are usually equal
  (one card per note) but never assume — get card ids from `notes-info` → `cards`.
- **Duplicate detection**: `allowDuplicate: false` only catches *exact* first-field
  matches within the same note type. Semantic duplicates must be judged by reading
  existing cards (see the sync skill).
- **Tags are space-separated strings** in add-tags/remove-tags; a tag itself must not
  contain spaces. Use `::` for hierarchy (Anki renders it as a tree).
- **Media filenames**: prefix stored files descriptively (`pem-<topic>-<date>.<ext>`)
  to avoid colliding with the user's existing media. `storeMediaFile` silently
  overwrites an existing name.
- **HTML in fields**: fields are HTML. Escape `<`/`&` in medical text (e.g. "K+ <3.0"
  → `K+ &lt;3.0`), use `<br>` for line breaks, `<img src="...">` for media.
- **Search query quoting**: deck names with spaces need `deck:"Name With Spaces"`;
  wrap the whole query in single quotes for the shell.
- **`null` results from add-notes** mean that specific note was rejected (usually a
  duplicate); the rest of the batch still succeeded.

## Safety rules (all skills)

1. Never call `delete-notes`, `deleteDecks`, or bulk `change-deck`/`update-note`
   without first showing the user exactly what will change and getting approval.
2. Before any destructive batch, `export-backup` to `~/.pemstudy/backups/` and tell
   the user the path.
3. Never touch decks outside `deck_root` unless the user explicitly asks.
