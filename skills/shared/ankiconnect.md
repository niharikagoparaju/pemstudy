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
  "deck_root": "PEM Notes",
  "legacy_deck_root": "PEM Legacy",
  "legacy_decks": ["Old Deck A", "Old Deck B"],
  "ankiconnect_url": "http://127.0.0.1:8765"
}
```

`anki.py` reads `ankiconnect_url` itself. Skills read `vault_path` and `deck_root`.
`legacy_deck_root` (default `"PEM Legacy"` when absent) and `legacy_decks` are used
only by the triage skill.

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

- **Note ids vs card ids** — the single most error-prone thing in this API:
  - `findNotes`/`notes-info`/`delete-notes`/tag ops take **note** ids;
    `findCards`/`cards-info`/`change-deck`/`suspend`/`forget` take **card** ids.
  - **A cloze note produces one card per deletion.** `{{c1}}`–`{{c5}}` in one note = 5
    cards. So note count ≠ card count for any batch containing cloze, and a note's
    cards must always be moved as a set (`notes-info` → `cards`) or the note splits
    across decks.
  - **Count what you mean when verifying.** "I created 53 notes" must be checked with
    `findNotes`, not `findCards` — otherwise cloze expansion looks like a failure
    (53 notes legitimately returned 74 cards in testing, twice mistaken for a bug).
  - `anki.py find` = `findNotes`. Use `invoke findCards` when you want cards.
- **Duplicate detection**: `allowDuplicate: false` only catches *exact* first-field
  matches within the same note type. Semantic duplicates must be judged by reading
  existing cards (see the sync skill).
- **Tags are space-separated strings** in add-tags/remove-tags; a tag itself must not
  contain spaces. Use `::` for hierarchy (Anki renders it as a tree).
- **`tag:` search is hierarchical, `remove-tags` is not** (verified):
  - `tag:pem::outline::01-trauma` matches the bare tag **and every child**
    (`...::a-trauma-resuscitation`, etc.). This is usually what you want for a
    domain-wide search — don't "fix" it.
  - To match *only* the bare parent: `tag:foo -tag:foo::*`. Use this to find cards
    classified to a domain but not yet to a subdomain.
  - `remove-tags --tags foo` removes only the exact tag `foo`, leaving `foo::bar`
    intact. So verifying a tag removal with `find tag:foo` gives a false failure —
    read `notes-info` tags instead.
- **Media filenames**: prefix stored files descriptively (`pem-<topic>-<date>.<ext>`)
  to avoid colliding with the user's existing media. `storeMediaFile` silently
  overwrites an existing name.
- **HTML in fields**: fields are HTML. Escape `<`/`&` in medical text (e.g. "K+ <3.0"
  → `K+ &lt;3.0`), use `<br>` for line breaks, `<img src="...">` for media.
- **Search query quoting**: deck names with spaces need `deck:"Name With Spaces"`;
  wrap the whole query in single quotes for the shell. Deck names containing `(` `)`
  **must** be quoted — unquoted parens are query grouping operators, not literals.
- **`deck:` matches exact name + subdecks, never prefixes.** `deck:"PEM Boards"` does
  **not** match `PEM Boards (ABP)` (verified). This matters when a legacy deck's name
  is a prefix of the active deck's — they stay correctly separate — but always read
  deck names carefully before a mutating batch, because the two are easy to confuse
  by eye.
- **`null` results from add-notes** mean that specific note was rejected (usually a
  duplicate); the rest of the batch still succeeded.

## Safety rules (all skills)

1. Never call `delete-notes`, `deleteDecks`, or bulk `change-deck`/`update-note`
   without first showing the user exactly what will change and getting approval.
2. Before any destructive batch, `export-backup` to `~/.pemstudy/backups/` and tell
   the user the path.
3. Never touch decks outside `deck_root` unless the user explicitly asks.
