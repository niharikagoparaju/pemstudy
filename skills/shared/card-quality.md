# What makes a good pemstudy flashcard

Board-prep cards compete for review time. Every card must earn its place.

## The rules

1. **Minimum information principle** — one card tests exactly one fact, association,
   or decision. A Rosh explanation paragraph usually yields 1–4 cards, not one big card.
2. **Test retrieval, not recognition** — the front must force recall. "What is the
   first-line treatment for X?" not "Tell me about X".
3. **Board-relevant framing** — phrase cards the way the exam discriminates:
   classic presentations, first-line vs contraindicated, age-specific cutoffs, doses
   only when the exam tests them (epinephrine, defibrillation J/kg, etc.).
4. **Cloze for numbers, lists, and thresholds** — `{{c1::15}} mg/kg` beats a Q&A card
   for a dose. For a 3-item list, one cloze per item ({{c1::}}, {{c2::}}, {{c3::}})
   so each is retrieved separately.
5. **Image cards for visual diagnoses** — rashes, ECGs, X-rays, US stills. Front shows
   only the image + a minimal stem ("Identify the condition" / "What is the rhythm?");
   the answer and a short description go on the back. Never leak the answer in the stem.
6. **Context tags, not context prose** — the outline tag and Source field carry the
   "where does this belong" metadata; don't pad the card text with it.
7. **Atomic wording** — short front, short back. If the back needs more than ~2
   sentences, the extra nuance goes in the Extra field (shown on the back, not tested).

## Choosing the note type

| Content in the journal note | Note type | Shape |
|---|---|---|
| Fact, association, classic presentation, next-step-in-management | PEM Basic | Question front / answer back |
| Dose, cutoff, score component, ordered list, criteria set | PEM Cloze | Sentence with `{{c1::...}}` deletions |
| Embedded vault image of a findable diagnosis (rash, ECG, imaging) | PEM Image Identify | Image front / diagnosis + description back |

## What NOT to card

- Facts the user already marked as known or trivial
- Question-bank trivia with no board relevance (e.g., "which answer choice was B")
- Duplicates of existing cards (semantic, not just literal — check before adding)
- Whole differential lists longer than ~4 items as a single card
- Anything the user's note marked to skip

## Worked example

Journal note fragment:

> Missed this one — kid with hypopyon after minor trauma. Answer was traumatic iritis,
> tx topical cycloplegic + steroids (ophtho first). I always mix up hyphema vs hypopyon.
> ![[Pasted image 20260714.png]] (slit lamp pic)

Good yield (3 cards):

1. **PEM Basic** — Front: "Layered white cells in the anterior chamber — what is this
   finding called?" Back: "Hypopyon". Extra: "vs hyphema = layered *blood* in the
   anterior chamber."
2. **PEM Basic** — Front: "First-line treatment for traumatic iritis?" Back: "Topical
   cycloplegic + topical corticosteroids (with ophthalmology involvement)."
3. **PEM Image Identify** — Image: the slit-lamp photo. Question: "Name the finding."
   Answer: "Hypopyon". Description: "Layered leukocytes in the anterior chamber;
   here following minor ocular trauma (traumatic iritis)."

Bad yield (one card): "Tell me about the kid with the eye trauma question" — narrative,
multi-fact, recognition-based.
