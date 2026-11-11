# pemstudy as a Claude Desktop extension — design

Date: 2026-11-11
Status: draft, awaiting approval

## Why

pemstudy today is a Claude Code plugin. To use it, someone needs Claude Code, Python 3,
an Obsidian vault, and a terminal-driven setup. That's fine for its author, but the
people we want to share it with — **PEM fellows prepping for boards** — typically have
**Claude Desktop and Anki**, and make their flashcards **by hand**. Asking them to
install Obsidian, the right Python, and wire it all together means they won't.

The goal is a **one-step install** for that fellow, while keeping the author's existing
Obsidian-sync workflow working in the same package.

## Who it's for and what success looks like

**Primary user (basic mode):** a PEM fellow with Claude Desktop + Anki desktop. Their
real workflow: finish a RoshReview block, review the incorrects, and for each one paste
the question stem, answer choices, the explanation, and some reasoning into Claude.
Together they work out *which aspects are worth carding* — answer choices they didn't
know the meaning of, management steps they weren't familiar with, thresholds and doses
they'd fumble. Approved cards should land in Anki without copy-pasting.

Success: the fellow installs one file, restarts Anki once, and is making cards from chat
within a few minutes, without touching a terminal, Python, or Obsidian.

**Secondary user (notes mode):** the author, who keeps study notes in an Obsidian vault
and today runs `/pemstudy:sync` etc. in Claude Code. They are fine moving that workflow
to Claude Desktop chat.

## Goals

1. Ship pemstudy as a single **Claude Desktop extension** (`.mcpb` bundle) installable
   by double-click / drag into Settings → Extensions.
2. **Zero runtime prerequisites** beyond Claude Desktop and Anki desktop: no Python,
   no Node install, no Obsidian, no terminal.
3. **Basic mode (default):** chat-driven card creation from pasted question-bank
   material, plus deck management, legacy triage, coverage audit, and card preferences.
4. **Notes mode (opt-in):** setting a notes-folder path in the extension's settings
   enables the existing Obsidian sync workflow, with behavior equivalent to today's
   `sync` skill.
5. Carry over the judgment that makes the plugin valuable: card-quality rules,
   fact-checking (incl. adult-vs-pediatric figures), dedupe, outline classification,
   and user card preferences.
6. Auto-install AnkiConnect for the user when it's missing (then they restart Anki).

## Non-goals

- Supporting Desktop's **Cowork** mode. It runs in a sandboxed VM and reports conflict
  on whether it can reach `localhost` on the host; target normal Desktop chat only.
- Maintaining the Claude Code plugin in parallel. The Code plugin is **retired** once
  the extension covers the author's workflow (the repo keeps it in git history).
- AnkiWeb / mobile sync, or working without Anki desktop open.
- Submission to Anthropic's extension directory in v1 (possible later).

## Anti-goals (failure even if it "works")

- Any install step that requires a terminal, Python, Node, or Obsidian for basic mode.
- Cards created without the user approving them first.
- Destructive operations (delete, move, suspend/unsuspend in bulk, retag) without the
  existing contract: **dry-run table → approval → `.apkg` backup → execute → verify**.
- Silently carding medicine believed to be wrong, or silently "fixing" the user's
  medicine. Surface it; let the user rule.
- A typo in the deck setting silently creating a stray deck.
- Flooding the user's daily review queue (the reason the two-deck model exists).

## Constraints and facts the design rests on

- **Claude Desktop extensions** run as a local process with the user's normal
  permissions. Desktop **bundles a Node.js runtime**, so a Node extension needs nothing
  installed; Python extensions would reintroduce the Python prerequisite. → **Rewrite in
  Node.** (Sources: Anthropic's Desktop Extensions post, the MCPB spec repo. Most
  secondary sources are third-party; verify against the current MCPB spec while
  building.)
- **AnkiConnect** is an HTTP server inside Anki at `http://127.0.0.1:8765` (add-on code
  `2055492159`). Language-agnostic; Node's built-in `fetch` speaks it. It is the one
  unavoidable Anki-side dependency.
- **AnkiWeb add-on download** needs `?v=2.1&p=<numeric point version>` params (learned
  the hard way; see `scripts/install_ankiconnect.py`). Node has no built-in unzip, so
  bundle a small zip library.
- **Desktop's Claude has no shell or file tools.** Everything today's skills do via
  `python3`, `cat`, `touch`, `date`, `find`, and Claude Code's Read tool must be exposed
  as extension tools.
- **The install-time settings form is static** (text/number/boolean/directory fields).
  It can't show a dropdown of the user's existing decks.
- **Chat-pasted images:** Claude can see an image pasted into chat, but an extension
  tool cannot receive its bytes. Image cards therefore need the image as a **file path
  or URL** the extension can read/fetch. MCP tool results *can* return image content,
  so the extension can let Claude look at a fetched/read image before carding it.
- AnkiConnect has no `renameDeck` (rename = create + changeDeck + deleteDecks).

## Decided design (as agreed in conversation)

### One extension, two modes

- **Basic mode** is the default. No notes folder configured.
- **Notes mode** turns on when the user sets a notes-folder path in the extension's
  settings. Same extension, same tools, plus the vault-reading/sync tools.
- **Legacy triage and coverage audit are available in basic mode** (neither needs
  Obsidian; a fellow with old decks will want triage). Triage has two modes; see below.

### Triage: two modes

Today's triage assumes a **dormant** pile (lapsed, all due): it stages cards into
`PEM Legacy` suspended, and promotion unsuspends and resets them to new. That would
wreck a deck a fellow is actively reviewing, so triage gets a second mode (decided by
the author):

- **Stage mode (dormant decks):** today's behavior, unchanged. Move into `PEM Legacy`,
  suspend, promote one domain at a time with `forget`.
- **Tidy-in-place mode (active decks):** cards **stay in their deck**, keep their
  scheduling, and are **never suspended or reset**. Triage works through them by
  domain:
  - Dedupe: duplicates proposed for deletion, keeper chosen per `dedupe.md`.
  - Fact-check, including adult figures on pediatric cards. Problems are flagged or
    fixed with approval.
  - Fix or flag broken cards: empty backs (about 20% of one legacy deck had them), dead
    media.
  - Add outline tags so the audit counts them.

  Any edit, delete, or retag goes through the full mutation contract. Moving cards to
  another deck is out of scope for this mode; that's a separate deck-management request.
- **Choosing the mode** *(our call)*: before starting on a deck, check its review
  history. If it has recent reviews, recommend tidy-in-place. If it's dormant,
  recommend stage. Either way, say why, and let the user confirm or switch.

### Install-time settings (extension `user_config`)

| Setting | Type | Default | Notes |
|---|---|---|---|
| Deck for new cards | text | `PEM Notes` | See deck behavior below. Changeable later in settings or by telling Claude. |
| Notes folder | directory, optional | *(blank)* | Blank = basic mode. Set = notes mode. |
| Legacy deck | text | `PEM Legacy` | Where triage stages old cards. Created lazily. |
| AnkiConnect URL | text | `http://127.0.0.1:8765` | Advanced; rarely changed. |

### Deck behavior

- **Default `PEM Notes`:** cards go into per-domain subdecks
  `PEM Notes::NN <Domain>` (28 domains from `data/pem-content-outline.yaml`), as today.
- **User names their own deck** (e.g. `Rosh Misses`): cards go **flat into that deck**;
  no domain subdecks are created under it. Outline tags still go on every card so the
  audit and later reorganizing work.
- **Deck name doesn't exist yet:** the extension creates it, but on first use Claude
  confirms ("I'll put cards in *Rosh Misses* — that's a new deck, OK?") to catch typos.
- Notes mode uses the same deck setting. The legacy tree stays separate
  (`PEM Legacy`), and **no card ever crosses between trees** (existing two-deck model).
- **Existing deck with hand-made cards in it** *(our call)*: allowed, and expected,
  since a fellow will often name the deck they already card into. Extension cards
  share it with their hand-made ones; nothing existing is moved or retagged. The audit
  counts coverage from outline-tagged cards, so untagged hand-made cards don't distort
  it (the audit may mention how many untagged cards the deck holds). A deck that is the
  target for new cards cannot also be a triage source. Refuse that combination.
- **Dedupe scope** *(our call)*: search the **whole collection**, not just the
  extension's decks. The fellow's own hand-made cards are the likeliest duplicates.
- **Changing the deck** *(our call)*: the Settings value is the single source of truth.
  Telling Claude "put these in X" overrides it for that conversation only, and Claude
  reminds the user to change Settings for a permanent switch. Changing the deck never
  moves existing cards. Moving them is a separate deck-management request that goes
  through the full mutation contract.

### Basic-mode card flow (the fellow's loop)

1. Fellow pastes a missed question (stem, choices, explanation, their reasoning;
   optionally an image path/URL).
2. Claude identifies what's worth carding — unfamiliar distractors, unfamiliar
   management, thresholds/doses — applying the card-quality rules and the user's
   preferences, and fact-checks (incl. adult figures on a pediatric card).
3. Claude dedupes against the existing collection (per `skills/shared/dedupe.md`).
4. Claude shows a compact proposal table; user approves / drops / edits.
5. Approved cards are created (media stored first), with outline tag, outline field,
   and a source tag/field identifying the session (no vault path in basic mode).
6. Durable style feedback ("always cloze doses") → offer to save to preferences.

### Carried over unchanged

- Note types `PEM Basic`, `PEM Cloze`, `PEM Image Identify` (`skills/setup/models.json`);
  never delete/replace an existing model.
- Two-deck model; promotion unsuspends in place and resets to new (`forget`).
- Mutation contract: dry-run → approve → `.apkg` backup (to `~/.pemstudy/backups/`) →
  execute → verify.
- Preferences file `~/.pemstudy/preferences.md` and its precedence rules
  (`skills/shared/preferences.md`).
- Notes mode: `pem_synced` / `pem_anki_notes` frontmatter stamping, zero-yield notes
  stamped too, mtime reset after the write, **timestamps generated by code, never
  hand-written**; candidate detection equivalent to `skills/sync/scan.py`.

### Platforms

- **macOS and Windows are both supported.** The author wants both but has only a Mac to
  test on.
- **macOS** is the tested platform: manual end-to-end testing against real Anki.
- **Windows** is supported but has not been tested by hand. To keep it working:
  - Write everything cross-platform: Node `path`, no shell-outs, no POSIX-only calls.
    Anki's add-ons folder on Windows is under `%APPDATA%\Anki2\addons21`.
  - Mark the platform-sensitive logic (Anki folder detection, AnkiConnect install,
    notes-folder path handling and mtime reset, frontmatter line endings) for
    automated tests.
  - Run those tests in CI on a Windows runner (e.g. GitHub Actions `windows-latest`)
    against a mocked AnkiConnect.
  - The README says Windows hasn't been tested by hand and asks Windows users to
    report problems. A Windows-using fellow doing a beta install is the real test.
- Linux: not targeted. It costs nothing if the code stays cross-platform, but it isn't
  declared or tested.

### Technology

- **Node**, packaged as an `.mcpb` Desktop extension, dependencies bundled. (Our call,
  forced by Desktop bundling Node but not Python.)
- `scripts/anki.py`, `scripts/install_ankiconnect.py`, and `skills/sync/scan.py` are
  replaced by Node equivalents inside the extension.
- **Distribution:** a GitHub release on `niharikagoparaju/pemstudy` with the `.mcpb`
  file attached. Desktop will likely show an "unverified extension" warning; the README
  should say so and say it's expected.

## Left to the builder

- **How the guidance reaches Desktop's Claude.** Today it lives in `SKILL.md` and
  `skills/shared/*.md`. Requirement: the card-quality, dedupe, fact-check,
  preferences, and per-workflow rules must reliably shape Claude's behavior without the
  user installing anything else (no separate Desktop "skills" upload). Candidates: MCP
  server `instructions`, MCP prompts, rich tool descriptions, and a tool that returns a
  named guide on demand (e.g. a guide per workflow: cards, sync, triage, deck, audit,
  prefs). Choose what Desktop actually honors; verify empirically.
- **Tool surface.** Roughly: Anki operations mirroring today's `anki.py` subcommands
  (consider a few higher-level tools — e.g. "create approved cards" doing media +
  addNotes + null-id reporting — to reduce error-prone multi-call sequences), plus
  setup/health, preferences read/write, backup, outline lookup, and notes-mode tools
  (scan candidates, read note, write sync stamp incl. mtime reset, resolve/fetch image).
  Notes-mode tools must refuse paths outside the configured notes folder.
- **First-run / setup flow** in chat: ping → AnkiConnect auto-install ladder (open
  Anki → auto-install → manual fallback with code `2055492159`) → create deck/subdecks
  and note types idempotently → report. Equivalent to today's `setup` skill, minus the
  vault auto-detect (the settings form handles it).
- **Migration** of an existing `~/.pemstudy/config.json` (the author has one with
  `vault_path`, `deck_root`, `legacy_decks`, `legacy_deck_root`). Extension settings
  become the source of truth; reading the old file once to suggest values is fine.
  Where `legacy_decks` (the list of old source decks) lives now is the builder's call.
- Image handling details within the constraint above (file path, URL; a "most recent
  screenshot" convenience is optional).
- Test strategy, project layout, and build tooling.
- **First step should be a throwaway spike**: a bare extension that installs in Desktop,
  pings AnkiConnect, and lists decks — to confirm the Node-runtime and localhost
  assumptions before the rewrite.
- **Go/no-go gate after the spike** *(our call)*: if the spike fails (bundled Node can't
  run the extension or can't reach `127.0.0.1`), or a guidance-delivery check shows
  Desktop doesn't reliably apply the card-quality rules, stop and bring options back
  to the author before building further. No compiled-binary or "set up a Project too"
  fallback without their say-so.
- **Quality bar** *(our call)*: build a small reference set before the rewrite. Use a
  few of the author's real vault notes plus a few realistic pasted Rosh-style
  incorrects, run them through the current Claude Code plugin, and keep the outputs.
  The extension must match them on card selection, fact-check flags, and dedupe. The
  Code plugin is retired only once it does.

## Open risks

- Desktop extension behavior (bundled Node version, settings-form field types, how
  server instructions/prompts surface) is documented mostly by third parties; the
  spike should confirm.
- Guidance fidelity: Claude Code reads skill files explicitly; in Desktop, guidance
  delivery is less direct. Quality could regress if the guidance doesn't land.
- Unsigned-extension warning may put off some fellows.
