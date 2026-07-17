# Card preferences

Users can shape how cards are made without editing any skill. Their preferences live
in a plain-English file that sync and triage load on every run.

## Where

`~/.pemstudy/preferences.md` — freeform Markdown, not a schema. Absent or fully
commented → no effect (plugin defaults apply). The starter template is
`${CLAUDE_PLUGIN_ROOT}/templates/preferences.md`.

## Loading it

At the start of a card-producing run (sync, or triage's promote-with-rewrite):

```bash
[ -f "$HOME/.pemstudy/preferences.md" ] && cat "$HOME/.pemstudy/preferences.md"
```

A **preference** is an uncommented bullet line — one that starts with `- `. Lines
starting with `#` (comments) and `##` (section headings) are not preferences; ignore
them. Apply every active bullet to every proposed card. If the file is missing or has
no active bullets, say nothing and use defaults.

## Precedence

Highest wins:

1. **Explicit instruction in this conversation** ("make these ones cloze") — overrides
   the file for this batch only.
2. **`preferences.md`** — the user's standing preferences.
3. **`card-quality.md`** — the plugin's defaults.

Preferences **refine** card quality; they never override the non-negotiables:
medical accuracy (never card something you believe is wrong), the note-vs-card /
provenance rules, dedup, or the safety contract. A preference that conflicts with one
of those → follow the rule and tell the user why.

## Persisting new preferences from chat

When the user gives a **durable** instruction mid-run — "from now on…", "always…",
"stop doing X" — offer to save it to `preferences.md` (don't auto-write). A one-off
("just this batch") is not persisted. Append under the closest existing section, or
add a new one; preserve the user's other lines and their comments.

The `/pemstudy:prefs` skill is the dedicated way to view and edit the file; you can
also edit it inline when the user asks during another skill.
