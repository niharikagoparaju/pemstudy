# pemstudy

A Claude Code plugin for pediatric emergency medicine (PEM) board prep. It wires your **Obsidian** study journal to your **Anki** collection so Claude can:

1. **Sync** — parse the notes you take while doing question banks (e.g., RoshReview), propose high-quality spaced-repetition flashcards (including image-identification cards from images pasted into your vault), dedupe them against your existing deck, and create them in Anki.
2. **Manage** — organize, prune, dedupe, and fact-check your Anki decks conversationally, with dry-run previews and automatic backups before anything destructive.
3. **Audit** — compare your card coverage against the [ABP PEM content outline](https://www.abp.org/) exam weights and see where you're thin.

## Prerequisites

- [Anki desktop](https://apps.ankiweb.net/)
- [AnkiConnect add-on](https://ankiweb.net/shared/info/2055492159) (add-on code `2055492159`) — the setup skill walks you through this
- An [Obsidian](https://obsidian.md/) vault (or any folder of Markdown notes) where you keep study notes
- Python 3 (ships with macOS; any 3.9+ works — the bundled scripts are stdlib-only)

## Install

```
/plugin marketplace add redscales/pemstudy
/plugin install pemstudy@pemstudy
```

(For a local checkout: `claude plugin marketplace add /path/to/pemstudy` then the
same install command.)

Then in Claude Code:

```
/pemstudy:setup
```

Setup verifies AnkiConnect, records your vault path, creates the `PEM Boards` deck tree (one subdeck per content-outline domain), and installs the plugin's note types.

## Workflow

1. Do questions in your question bank. When you get one wrong (or don't fully understand an answer choice), jot a note in your vault — free-form is fine; paste in images worth remembering (rashes, ECGs, X-rays).
2. Periodically run `/pemstudy:sync`. Claude reads new/changed notes, proposes cards, shows you the batch for approval, and files them into the right domain subdeck with content-outline tags.
3. Review your cards in Anki as usual.
4. Occasionally run `/pemstudy:deck` to dedupe/prune/reorganize, and `/pemstudy:audit` to see coverage vs. exam weights.

## Skills

| Skill | What it does |
|---|---|
| `/pemstudy:setup` | Wire Anki + Obsidian: verify AnkiConnect, write config, create decks and note types |
| `/pemstudy:sync` | Journal notes → proposed flashcards → dedupe → create in Anki |
| `/pemstudy:deck` | Conversational deck management: dedupe, prune, accuracy review, retagging |
| `/pemstudy:audit` | Card coverage vs. ABP PEM content outline exam weights |

## Layout

- `scripts/anki.py` — stdlib-only AnkiConnect CLI used by all skills
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
