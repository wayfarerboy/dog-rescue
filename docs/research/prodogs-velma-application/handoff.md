# Handoff — Velma (Pro Dogs Direct) adoption application

## Where things stand

- The live adoption form is **fully mapped**: all 10 pages, every question, every option, field ids.
  See [`adoption-form-questions.md`](./adoption-form-questions.md) and [`README.md`](./README.md).
- The dog's rehoming thread and PDD's rehoming criteria are summarised in [`README.md`](./README.md).
- **Nothing has been submitted.** No account, no draft, no personal data entered anywhere.
  The scraper only ever sent dummy values to discover the questions.

## Next thing to do

Draft the application answers **with the user**, question by question, then show the complete draft for
approval before anything is typed into the real form. Work from the question list in page order so nothing
is missed (the form cannot be saved part-way and cannot be edited after submission).

### Bank of questions to ask the user (fills the gaps)

Page 2 — about you
- Full name, age of the adopting person.
- Email + phone (main and secondary), full address, county, postcode.
- Have you adopted from PDD before? If yes, dog's name and month/year.

Page 3 — home
- Owned / rented; house / flat / bungalow / other. If flat: which floor. If other: details.
- If renting: written landlord permission for a dog? (needed)
- Garden: private fully secure / private needs securing / communal / none.
- Lowest fence/wall/gate height the dog can reach (<4ft, 4–6ft, 6ft+).
- How will you manage toileting and exercise? (be specific: times, routes, garden, puppy pads?)
- Garden size, security and suitability in a sentence or two.

Page 4 — household & commitments
- Who else lives there (all adults 18+)? Names/ages/relationship.
- Children in the home (gender, ages); children who visit regularly.
- Any holiday / hospital / house move / fixed commitments in the next 8 weeks?
- Any disabilities or impairments needing extra support to meet the dog's needs?

Page 5 — time alone & work
- How many times a week would the dog be left alone (0–1, 2–3, 4–5, 6+)?
- Average hours per time?
- Do you work (full time / part time / no)? Job based from home or elsewhere?
- If WFH: written employer confirmation that it is permanent? Hours away from home per day?
- Other adults' working hours/location.

Page 6 — resident dogs
- Number of dogs (0–4+); for each: name, breed, age, gender, neutered? (if not, why).

Page 7 — home checks & other pets
- Home-checked by another rescue in the last 12 months? Details + OK to contact them?
- All other pets, by species (include the cats).

Page 8 — experience & why you
- Previous experience with dogs (own dogs, family dogs, breeds, ages — especially strong-willed small breeds).
- The daily routine you'd give Velma (walks, training class, play, rest, naps, crate?).
- Why this dog, against her written criteria (older children only, dog-tolerant resident dogs,
  bold dog-savvy cats, experience with opinionated little dogs, time for training, travel to Epsom, neutering).

Page 9 — declarations
- All 7 are mandatory: private transport to meet/collect; resident dogs present at meet-and-greet;
  home + ID check; post-adoption visit; return the dog to PDD if unable to keep her; truthfulness;
  GDPR / insurance data sharing. Confirm the user accepts each.

Page 10 — research/marketing (optional but required fields)
- Applied to other PDD dogs in the last 6 months? How many?
- Donated/supported PDD in the last 3 months? How?
- Follow PDD on social media? Which?
- Mailing list consent + email.

### Must-confirm eligibility facts (these decide shortlisting)

- Willing to travel to **Epsom, Surrey** to meet and collect her, by private transport.
- **Older children only** in/around the home, or none.
- Resident dogs must tolerate relentless, rude play.
- Cats must be bold and dog-savvy.
- Experience with opinionated small dogs; commitment to **training classes**.
- Accept the **£325–£600+** set donation without knowing the exact figure, plus a **deposit before the home check**
  (retained if the user withdraws; refunded unless the home check fails due to incorrect information).
- Agree to **neuter at the correct age** (reduced cost via PDD vets) and sign the adoption contract.

## Gotchas for whoever picks this up

- Form is Formidable Forms, id `53`, 10 pages, POST-based; the real form must be filled by a human in a
  browser — it cannot be saved part-way and cannot be edited after submit.
- `walk-form.js` needs: leave `item_meta[1919]` empty and omit `ak_hp_textarea`, or Akismet rejects the POST
  as spam. It also sleeps before posting to avoid the spam check.
- The dog's page: <https://prodogsdirect.org.uk/velma-corgi-cross/> — check her status before applying;
  if she shows *Reserved*, the application window is effectively closed.

## Suggested skills

- `grilling` — stress-test the draft answers and the "why our dog would choose you" text before submitting.
- `writing-for-agents` — only if these research docs are edited further.
