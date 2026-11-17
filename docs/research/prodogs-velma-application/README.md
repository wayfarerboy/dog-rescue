# Velma (Pro Dogs Direct) — adoption application research

Research into adopting **Velma**, a 12-week-old female Corgi cross fostered in Epsom, Surrey, via
[Pro Dogs Direct](https://prodogsdirect.org.uk/velma-corgi-cross/) (registered charity 1115647).

Goal: understand the application form well enough to answer every question truthfully and
in a way that matches the dog's stated rehoming criteria, then draft the answers with the user.

## Artifacts

| File | What it is |
| --- | --- |
| [`adoption-form-questions.md`](./adoption-form-questions.md) | Every question on all 10 pages of the live form, in order, with options and field ids |
| [`walk-form.js`](./walk-form.js) | Node script that walks the live form with dummy data to regenerate the question list |
| [`handoff.md`](./handoff.md) | Handoff notes for the next session |

## The dog (from her rehoming thread)

- 12 weeks old, female, Corgi cross, fostered in Epsom, Surrey.
- Adores people, "a people magnet", nothing fazes her.
- **Children:** older children used to dogs only — she is a nippy, needle-toothed puppy.
- **Dogs:** loves other dogs, but relentlessly playful; resident dogs must tolerate rude play.
- **Cats:** in foster with bold, dog-savvy cats; a nervous cat would not cope.
- **Health:** no known issues. 1st vaccination, microchipped, flea/wormed. **Neutering is part of
  the adoption agreement** (reduced-cost neutering at PDD vets).
- **Training:** not fully vaccinated yet, so lead training and socialisation continue in the new home.
  Housetraining in progress. Vocal (play, noises, wanting attention).
- **Home wanted:** experienced with "opinionated little doggies", time and energy for a puppy,
  committed to training classes. Final size unknown. Will chew, pee, poop.
- **Travel:** adopters must travel to Epsom, Surrey to meet her.
- Applications are **rejected** if they do not match the rehoming criteria as written.

## How the process works (from the form's preamble)

1. Apply for one named, currently-available dog (a separate form per dog). General applications ignored.
2. Form is long, cannot be saved part-way, **cannot be edited after submission**. Set time aside.
3. Shortlisted applicants are phoned for an interview. Not shortlisted = no contact.
4. Watch the dog's status: if it flips to *Reserved* and you have not been contacted, you were unsuccessful.
5. Deposit is requested **before** the home check. Refunded if PDD declines after the check, *unless* the
   check failed because of incorrect information supplied. Withdrawing at any point = deposit retained.
6. Home check + ID check, then a legally binding adoption contract must be read and signed before collection.
7. Collection must be from the foster home, by private transport.
8. Set donation usually **£325–£600**, higher for puppies. The form only lets you continue if you accept
   the range without knowing the exact figure (option 1 on page 1).

## Form structure (10 pages)

1. **Eligibility/commitment gate** — dog name, breed, age band, owned a puppy before?, researched puppies?,
   time?, space?, breed experience?, can afford?, accept donation range. *Only option 1 answers keep you in.*
2. **About you** — name, age, email (twice), two phone numbers, address, county, postcode,
   adopted from PDD before? (+ previous dog name/month/year).
3. **Your home** — owned/rented house/flat/bungalow/other (+ flat floor, + other details), landlord
   written permission, garden type, lowest fence height, how you'll manage toileting/exercise, garden description.
4. **Household & commitments** — other adults + list, children in home + details, regular visiting children +
   details, holiday/hospital/moving/commitments in next 8 weeks + details, disabilities/impairments + details.
5. **Time alone & work** — times left alone per week, hours per time, work status (full/part/none),
   job based from home or elsewhere, written employer confirmation of permanent WFH, hours away per day,
   other adults' working hours/location.
6. **Resident dogs** — number of dogs (0–4+), then name/breed/age/gender/neutered/reason-not-neutered for
   each (up to 4 + free text for more).
7. **Home checks & other pets** — home-checked by another rescue in last 12 months? + details,
   all other pets incl. species.
8. **Your experience & why you** — previous experience with dogs, the routine you'd have, and
   "based on their re-homing criteria, why our dog would choose you".
9. **Declarations** — 7 mandatory agreements: private transport, resident dogs at meet-and-greet,
   home + ID check, post-adoption visit, return the dog to PDD if needed, truthfulness, GDPR/insurance sharing.
10. **Research/marketing (optional, charity use)** — applied to other PDD dogs in 6 months?, how many,
    donated/supported in 3 months?, how, social media followed?, which, mailing-list consent + email.

Conditional logic: page 3 shows flat questions only for flats, "other details" only for Other, landlord
permission only when rented; page 5 shows employer/WFH questions based on work status; page 6 shows a
block per resident dog; page 7's details box follows the home-check answer.

## Notes for filling it in truthfully

- Answers must be **genuine**; the form says false/misleading information → immediate rejection.
- The form rewards specificity in the free-text boxes: routine, training plan, how the puppy is never
  left too long, secure garden, and why this particular dog fits this particular household.
- Match Velma's criteria exactly: older dog-savvy children, tolerant resident dogs, bold dog-savvy cats
  (or no cats), experience with strong-willed small breeds, time for training classes, ability to travel
  to Epsom, agreement to neuter.
