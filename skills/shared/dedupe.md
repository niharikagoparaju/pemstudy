# Judging duplicate cards

Used by the sync, deck, and triage skills. Duplication is **semantic**, not textual.

## The test

Two cards are duplicates when **answering one teaches you the answer to the other**.
Wording, note type, and direction don't matter:

| Card A | Card B | Verdict |
|---|---|---|
| "First-line treatment for anaphylaxis?" → "IM epinephrine" | "Anaphylaxis: give {{c1::IM epinephrine}} first" | **Duplicate** — same fact, Q&A vs cloze |
| "Epinephrine dose in anaphylaxis?" → "0.01 mg/kg IM (max 0.5 mg)" | "First-line treatment for anaphylaxis?" → "IM epinephrine" | **Not duplicate** — dose vs drug choice are separate retrievals |
| "Most common cause of X?" → "Y" | "Y causes which condition?" → "X" | **Duplicate-ish** — reverse of the same association; keep one unless reversal is genuinely worth drilling |
| Image of a rash → "SJS" | "Mucosal involvement + target lesions → diagnosis?" → "SJS" | **Not duplicate** — visual recognition vs verbal reasoning are different skills |

**`allowDuplicate: false` does not do this job.** AnkiConnect only blocks byte-identical
first fields within the same note type, so it misses nearly every real duplicate. Always
judge by reading.

## Finding candidates before adding/promoting

Search narrow-to-wide; the outline tag is the cheapest filter:

```bash
ANKI find '"deck:<deck_root>" tag:pem::outline::<domain-slug>::<subdomain-slug>'
ANKI find '"deck:<deck_root>" tag:pem::outline::<domain-slug>'      # domain-level
ANKI find '"deck:<deck_root>" <distinctive keyword>'                # e.g. a drug name
```

Then `notes-info` the hits and read them. A keyword search on the distinctive noun
(drug, organism, eponym) catches duplicates that were filed under a different domain.

## Choosing the keeper

When a group duplicates, keep the card that is:

1. **Better written** per `card-quality.md` (atomic, retrieval-forcing, board-framed)
2. **Better sourced** — has `Source`/`Outline` populated, or richer `Extra`
3. **More mature** — real scheduling history beats a fresh duplicate. If the weaker
   card has the history, prefer editing its text over deleting it and losing the
   history.

Merge anything worth keeping from the losers (a clarifying `Extra`, a better image)
into the keeper before dropping them.

## Rules

- Never delete a duplicate without showing the user the group and the keeper choice.
- Near-duplicates that test genuinely different things are **not** duplicates — the
  cost of a false merge (a lost distinction) exceeds the cost of one extra card.
- When unsure, keep both and say so. The user's review time is the scarce resource,
  but so is their trust.
