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

### 1. Verify AnkiConnect

```bash
ANKI ping
```

- Connection refused → ask the user to open Anki, then re-ping.
- Still refused → AnkiConnect isn't installed: have the user open Anki →
  Tools → Add-ons → Get Add-ons… → paste `2055492159` → restart Anki. Re-ping.

### 2. Locate the Obsidian vault

Look for existing config first (`~/.pemstudy/config.json` → `vault_path`). Otherwise:

```bash
find ~ -maxdepth 4 -name ".obsidian" -type d 2>/dev/null
```

- One hit → confirm it with the user.
- Multiple/zero → ask the user for the vault path. Verify it exists and contains
  Markdown files or an `.obsidian/` folder before accepting.

### 3. Choose the deck root

Default: `PEM Boards`. Check for collision:

```bash
ANKI decks
```

If a deck named like the chosen root **already exists** (the user may have a
hand-built tree), do NOT silently merge. Ask the user to choose:

1. **Adopt** — create the plugin's numbered domain subdecks under the existing root,
   alongside their current subdecks (existing cards untouched; the deck skill can
   reorganize them later).
2. **Separate root** — use a different name (e.g. `PEM Boards (ABP)`).

### 4. Create the domain subdecks

Read the 13 domains from `${CLAUDE_PLUGIN_ROOT}/data/pem-content-outline.yaml`.
For each, create `<deck_root>::<NN> <Domain Name>` where NN is the zero-padded id
from the `slug` (e.g. `PEM Boards::01 Emergency Conditions` … `PEM Boards::13 Core
Knowledge in Scholarly Activities`):

```bash
ANKI create-deck "PEM Boards::01 Emergency Conditions"   # idempotent, one per domain
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
  "deck_root": "PEM Boards",
  "ankiconnect_url": "http://127.0.0.1:8765"
}
```

Also create `~/.pemstudy/backups/` (used by the deck skill before destructive ops).

### 7. Offer the note template

Offer to copy `${CLAUDE_PLUGIN_ROOT}/templates/rosh-session.md` into the vault
(e.g. `<vault>/templates/`). Optional — the sync skill parses free-form notes; the
template just gives their notes a head start. Don't copy without asking.

### 8. Verify and report

Confirm, then summarize to the user:

```bash
ANKI decks | grep -c "PEM Boards::"     # expect ≥ 13
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
