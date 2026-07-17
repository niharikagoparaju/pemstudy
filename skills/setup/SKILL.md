---
name: setup
description: Use when wiring the pemstudy plugin to the user's Anki and Obsidian for the first time, when ~/.pemstudy/config.json is missing, when another pemstudy skill reports AnkiConnect/config errors, or when the user wants to change their vault path or deck root.
---

# pemstudy setup

Wire Anki (via AnkiConnect) and the user's Obsidian vault to the pemstudy plugin.
Idempotent — safe to re-run; it only creates what's missing.

Reference for all Anki calls: `${CLAUDE_PLUGIN_ROOT}/skills/shared/ankiconnect.md`.
Define `ANKI` as a shell function (works in bash and zsh, unlike a variable):

```bash
ANKI() { python3 "${CLAUDE_PLUGIN_ROOT}/scripts/anki.py" "$@"; }
```

## Steps

### 1. Verify AnkiConnect (and install it if missing)

```bash
ANKI ping        # → {"ankiconnect_version": 6} when working
```

If ping fails, walk this ladder:

1. **Anki not open** (connection refused, and the user confirms Anki is closed) → ask
   them to open Anki, re-ping.
2. **Anki open but still refused** → AnkiConnect isn't installed. Offer to install it
   automatically:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install_ankiconnect.py"
   ```

   It detects the OS, downloads the add-on, and unzips it into Anki's `addons21`
   folder (idempotent — safe if already present). Then **the user must fully quit and
   reopen Anki** for it to load. Re-ping after restart.
3. **Auto-install fails** (no internet, non-standard Anki dir, AnkiWeb hiccup) → fall
   back to manual: Anki → Tools → Add-ons → Get Add-ons… → paste `2055492159` →
   restart Anki. Re-ping.

Don't proceed past this step until `ping` succeeds — every later step needs Anki.

### 2. Locate the Obsidian vault

Look for existing config first (`~/.pemstudy/config.json` → `vault_path`). Otherwise:

```bash
find ~ -maxdepth 4 -name ".obsidian" -type d 2>/dev/null
```

- One hit → confirm it with the user.
- Multiple/zero → ask the user for the vault path. Verify it exists and contains
  Markdown files or an `.obsidian/` folder before accepting.

### 3. Choose the deck root

Default: `PEM Notes` — it says what the deck holds (cards from your notes), pairs with
`PEM Legacy`, and avoids colliding with a hand-built `PEM Boards` deck, which PEM
candidates commonly already have. Check for collision anyway:

```bash
ANKI decks
```

If a deck named like the chosen root **already exists** (the user may have a
hand-built tree), do NOT silently merge. Ask the user to choose:

1. **Adopt** — create the plugin's numbered domain subdecks under the existing root,
   alongside their current subdecks (existing cards untouched; the deck skill can
   reorganize them later).
2. **Separate root** — use a different name. Avoid near-identical names: a user in
   testing ended up with both `PEM Boards` and `PEM Boards (ABP)` and repeatedly
   confused them in the sidebar.

### 4. Create the domain subdecks

Read the 28 domains from `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml`.
For each, create `<deck_root>::<NN> <Domain Name>` where NN is the zero-padded id
from the `slug` (e.g. `PEM Notes::01 Trauma` … `PEM Notes::28 Core Knowledge in
Scholarly Activities`):

```bash
ANKI create-deck "PEM Notes::01 Trauma"   # idempotent, one per domain
```

### 5. Create note types

Check `ANKI models`; for each of `PEM Basic`, `PEM Cloze`, `PEM Image Identify`
that is missing, create it from the definitions file:

```bash
# extract one model's definition and pass it to create-model
python3 -c "import json; print(json.dumps(json.load(open('${CLAUDE_PLUGIN_ROOT}/skills/setup/models.json'))['PEM Basic']))" > /tmp/pem-model.json
ANKI create-model --json-file /tmp/pem-model.json
```

If a model already exists, leave it alone (createModel errors on duplicates —
that's fine, report it as "already present"). Verify fields afterward with
`ANKI model-fields "PEM Basic"`.

### 6. Write config

Write `~/.pemstudy/config.json` (create the directory; preserve unknown keys if the
file already exists):

```json
{
  "vault_path": "/Users/…/VaultName",
  "deck_root": "PEM Notes",
  "legacy_deck_root": "PEM Legacy",
  "legacy_decks": [],
  "ankiconnect_url": "http://127.0.0.1:8765"
}
```

`legacy_deck_root` and `legacy_decks` belong to the triage skill (for digesting a
pre-existing collection). Don't create the triage decks here — the triage skill
creates them lazily, so users with no legacy cards never see them. If the user has
pre-existing decks worth digesting, list them in `legacy_decks` and point the user
at the triage skill; otherwise leave it `[]`.

Also create `~/.pemstudy/backups/` (used by the deck skill before destructive ops).

### 7. Offer the note template and card preferences

- Offer to copy `${CLAUDE_PLUGIN_ROOT}/templates/rosh-session.md` into the vault
  (e.g. `<vault>/templates/`). Optional — the sync skill parses free-form notes; the
  template just gives their notes a head start. Don't copy without asking.
- Offer to seed card preferences by copying
  `${CLAUDE_PLUGIN_ROOT}/templates/preferences.md` → `~/.pemstudy/preferences.md`
  (all-commented, so a no-op until edited). Mention they can shape cards anytime by
  chatting or via `/pemstudy:prefs`. Don't overwrite an existing preferences file.

### 8. Verify and report

Confirm, then summarize to the user:

```bash
ANKI decks | grep -c "PEM Notes::"     # expect ≥ 28
ANKI models | grep "PEM"                # expect the 3 PEM models
```

Report: vault path, deck root (and collision choice if any), decks created vs
pre-existing, models created vs pre-existing, config path.

## Common mistakes

- Silently merging into a pre-existing deck root — always surface the collision.
- Recreating models that exist (breaks the user's existing cards' templates) —
  check `models` first, never delete/replace a model.
- Accepting a vault path without verifying it exists.
- Forgetting that deck creation is cheap and idempotent but model creation is not.
