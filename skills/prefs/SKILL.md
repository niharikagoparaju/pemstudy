---
name: prefs
description: Use when the user wants to view or change how their flashcards are made — card style/format preferences, "keep my cards terse", "always cloze doses", "add mnemonics", "stop making X kind of card", or asks what their current card preferences are.
---

# pemstudy prefs — view and edit card preferences

Manage `~/.pemstudy/preferences.md`, the plain-English file that sync and triage read
to shape every card. See `${CLAUDE_PLUGIN_ROOT}/skills/shared/preferences.md` for how
preferences are loaded and applied.

## View

```bash
cat "$HOME/.pemstudy/preferences.md" 2>/dev/null
```

- File exists → show it; summarize which lines are **active** (uncommented `- `
  bullets) vs examples (commented), so the user sees what's actually in effect.
- Missing → tell the user they have none yet and offer to create it (next section).

## Create (first time)

Seed from the template, then let the user turn lines on or add their own:

```bash
mkdir -p "$HOME/.pemstudy"
cp "${CLAUDE_PLUGIN_ROOT}/templates/preferences.md" "$HOME/.pemstudy/preferences.md"
```

The template is all-commented (a no-op) — nothing changes until the user activates a
line or adds one.

## Edit

Translate the user's request into a concrete preference line and write it:

- "keep cards terse" → `- Keep card fronts and backs terse — one line each where possible.`
- "always cloze doses" → `- Prefer cloze deletions for doses, thresholds, and numeric values.`
- "add mnemonics" → `- When a well-known mnemonic exists, put it in the Extra field.`

Rules:
- **Confirm the exact wording** you'll write before saving — the user should recognize
  their intent.
- **Preserve everything else** in the file (their other lines, their comments, section
  order). Append under the closest section heading, or add a new one.
- To **remove** a preference, delete or re-comment that line; show the before/after.
- Keep each preference one imperative line. If a request is really two rules, write two.

## Guardrails

- Preferences shape *style and selection*, not correctness. If the user asks for
  something that would make cards wrong or unsafe ("skip the fact-check", "always trust
  my note's doses"), decline and explain — those are non-negotiables from
  `card-quality.md` / the sync fact-check, not preferences.
- After editing, remind the user the change applies to the **next** sync/triage run,
  not retroactively to existing cards (offer the deck skill if they want existing cards
  reworked).

## Common mistakes

- Auto-writing a one-off ("just make these ones cloze") as a standing preference — only
  persist durable "from now on" instructions.
- Overwriting the file instead of editing it — never clobber the user's other lines.
- Silently changing wording the user didn't confirm.
