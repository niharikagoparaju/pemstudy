# pemstudy

A Claude Code plugin for pediatric emergency medicine (PEM) board prep. It wires your **Obsidian** study journal to your **Anki** collection so Claude can:

1. **Sync** — parse the notes you take while doing question banks (e.g., RoshReview), propose high-quality spaced-repetition flashcards (including image-identification cards from images pasted into your vault), dedupe them against your existing deck, and create them in Anki.
2. **Triage** — digest a pre-existing pile of old cards slowly, without ever flooding your daily queue.
3. **Manage** — organize, prune, dedupe, and fact-check your Anki decks conversationally, with dry-run previews and automatic backups before anything destructive.
4. **Audit** — compare your card coverage against the [ABP PEM content outline](https://www.abp.org/) exam weights and see where you're thin.

## The two-deck model

The plugin keeps **two separate deck trees**, because the thing that kills board prep is opening Anki to 1,500 due cards and closing it again.

```
Obsidian vault ──sync──▶  PEM Notes::NN <Domain>     ← cards from YOUR notes, only
 (daily habit)

your old decks ──stage──▶  PEM Legacy::NN <Domain>          ← cards from your old collection, only
                             suspended   = not yet triaged
                             unsuspended = approved, in rotation   ◀── promote (in place)
```

- **The note deck** is fed daily by `sync` from the notes you're actually writing. It contains nothing else, so it's an honest measure of what you've studied.
- **The legacy deck** holds your old cards, organized by the content outline and **suspended** — a suspended card cannot enter review no matter which deck you click. They wait indefinitely at zero cost.
- **Promotion unsuspends in place**, one domain at a time, after a card has been deduped, fact-checked, and judged worth your review time. Promoted cards are **reset to new**, so they trickle in at your new-cards/day limit instead of landing due in a heap.
- **No card ever crosses between the trees.** Two trees means two independent new-cards/day dials: run notes at 20/day and legacy at 5/day, and the note habit always wins.

Old cards therefore never ambush you, and the junk (duplicates, broken cards, off-outline material) gets filtered out during triage rather than living in your deck forever.

## Prerequisites

- [Anki desktop](https://apps.ankiweb.net/) (open while syncing)
- An [Obsidian](https://obsidian.md/) vault (or any folder of Markdown notes) where you keep study notes
- Python 3 (ships with macOS; any 3.9+ works — the bundled scripts are stdlib-only)

You do **not** need to install AnkiConnect yourself — setup offers to do it for you.

## Install & first run

```
/plugin marketplace add redscales/pemstudy
/plugin install pemstudy@pemstudy
```

(For a local checkout: `claude plugin marketplace add /path/to/pemstudy` then the same install command.)

The first time you open Claude Code after installing, the plugin notices it isn't configured yet and offers to run setup. Or start it yourself:

```
/pemstudy:setup
```

Setup will, in order:

1. **Check AnkiConnect** and, if it's missing, offer to install it automatically (downloads the add-on and drops it into Anki's add-ons folder — then you restart Anki). Falls back to a guided manual install if needed.
2. **Ask for your Obsidian vault** folder (it tries to auto-detect it first).
3. **Create the deck tree** (`PEM Notes`, one subdeck per content-outline domain) and the plugin's note types.
4. Optionally seed a note template and a card-preferences file.

Everything user-specific lives in `~/.pemstudy/` (config, preferences, backups) — nothing about your setup is committed to the repo.

## Workflow

1. Do questions in your question bank. When you get one wrong (or don't fully understand an answer choice), jot a note in your vault — free-form is fine; paste in images worth remembering (rashes, ECGs, X-rays).
2. Periodically run `/pemstudy:sync`. Claude reads new/changed notes, proposes cards, shows you the batch for approval, and files them into the right domain subdeck with content-outline tags.
3. Review your cards in Anki as usual.
4. Occasionally run `/pemstudy:deck` to dedupe/prune/reorganize, and `/pemstudy:audit` to see coverage vs. exam weights.

If you're bringing an existing collection: run `/pemstudy:triage` once per old subdeck to stage it (`"stage my PBR Cardiology deck"`), then chip away with `"let's triage some trauma"` whenever you have appetite. `/pemstudy:audit` shows which domains have cards waiting to be triaged versus which need new question blocks.

## Card preferences

You can shape how cards are made without editing anything. Just tell Claude — *"from now on keep cards to one line"*, *"always cloze the doses"*, *"add mnemonics when they exist"*, *"prefer image-ID cards for rashes"* — and it saves the instruction to `~/.pemstudy/preferences.md`, which `sync` and `triage` read on every run. View or edit them anytime with `/pemstudy:prefs`. Preferences shape style and selection; they never override medical accuracy or the safety checks.

## Skills

| Skill | What it does |
|---|---|
| `/pemstudy:setup` | Wire Anki + Obsidian: install/verify AnkiConnect, write config, create decks and note types |
| `/pemstudy:sync` | Journal notes → proposed flashcards → dedupe → create in Anki |
| `/pemstudy:triage` | Stage old decks into `PEM Legacy` (suspended), then approve the worthy ones into rotation |
| `/pemstudy:prefs` | View or edit your card preferences (`~/.pemstudy/preferences.md`) |
| `/pemstudy:deck` | Conversational deck management: dedupe, prune, accuracy review, retagging |
| `/pemstudy:audit` | Card coverage vs. ABP PEM content outline exam weights, plus triage backlog |

Every mutating operation follows the same contract: **dry-run table → your approval → `.apkg` backup → execute → verify.** Backups land in `~/.pemstudy/backups/`.

## Layout

- `scripts/anki.py` — stdlib-only AnkiConnect CLI used by all skills
- `scripts/install_ankiconnect.py` — stdlib cross-platform AnkiConnect add-on installer (used by setup)
- `hooks/` — SessionStart hook that nudges first-time users toward `/pemstudy:setup`
- `skills/sync/scan.py` — stdlib vault scanner (finds notes needing sync via `pem_synced` frontmatter vs mtime)
- `data/pem-content-outline.yaml` — the full ABP PEM content outline (domains, subdomains, topics, exam weights)
- `templates/` — optional Obsidian note templates
- `skills/shared/` — reference docs the skills lean on (AnkiConnect cookbook, card-quality guide, note conventions)

Configuration lives in `~/.pemstudy/config.json` (created by setup); pre-mutation
deck backups land in `~/.pemstudy/backups/`.

## How syncing stays idempotent

The sync skill stamps each processed note's frontmatter with `pem_synced` and the
Anki note ids it created (`pem_anki_notes`), then resets the file's mtime to match.
Re-running sync only picks up new notes and notes edited after their stamp; cards
carry `pem::source::<note>` and `pem::outline::<domain>::<subdomain>` tags plus a
`Source` field, so everything is traceable in both directions.

## License

MIT
