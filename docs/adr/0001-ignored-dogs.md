# ADR-0001: Ignored-dog tracking

## Status

Accepted

## Context

When browsing adoptable dogs across rescue sites, the user couldn't tell which
dogs they had already looked at and dismissed from which were new. Each run
returns an overlapping set of dogs, and the list grows stale as dogs are added
and removed from the live scrapes. Names are not a reliable identity — several
rescues list dogs with duplicate names (e.g. two "Milo", two "Tiny").

We wanted a lightweight way to mark a dog as "looked at and ignored" so the
next listing makes it obvious what is new versus already seen.

## Decision

- **Identity key is the dog's profile URL.** The `Dog.url` field is unique per
  dog (its profile page) and is already the cache's dedup key, so it is reused.
- **Storage is a new pipe-free text file `data/ignored.txt`**, one dog URL
  per line, managed by a new `IgnoredList` class in `ignore.py`. This
  mirrors the existing `too-far.txt` (`TooFarList`) and `excluded-breeds.txt`
  (`BreedExclusionList`) patterns. The file is gitignored like all cache data.
- **Listing annotates ignored dogs.** `list_dogs.py`:
  - terminal table appends a `[I]` marker to ignored rows;
  - HTML page dims ignored cards, strikes through the name, shows a
    "ignored" badge, and reports `N new / M ignored` in the header.
  - `--hide-ignored` filters ignored dogs out entirely.
  - `--ignore <url>` and `--un-ignore <url>` mark/unmark without listing.
- **Interactive CLI.** `cli.py` gains a "Browse & mark dogs" flow that numbers
  each listed dog; typing a number copies its URL to the system clipboard
  (`pbcopy`/`xclip`/`clip`, chosen by platform) so the user can paste it into a
  browser — important because the CLI is often run over SSH — and `d<num>`
  toggles that dog's ignored state. A "Manage ignored list" view lists,
  adds, and removes entries by hand.
- **Marking from the HTML page.** The generated page embeds a small script that
  detects whether it is served over HTTP. A tiny local server (`serve.py`,
  reachable via **List Dogs → Serve HTML in browser**) serves the page and
  exposes `GET /api/ignored` and `POST /api/ignored/toggle`. Each card
  carries a **Ignore / Un-ignore** button wired to that endpoint, so a
  click persists straight to `data/ignored.txt` and the page updates in
  place. Opened as a plain `file://` file, the buttons are disabled and only
  the static markers baked in at generation time are shown.

## Consequences

- The user can see at a glance which dogs are new versus already ignored.
- Ignored status is stored on the user's machine (local to this repo), not
  fetched from any rescue site.
- A dog that is re-listed later with the same URL stays marked until the user
  removes it. A dog whose URL changes is treated as new.
- No reason/note is recorded per ignored dog (kept intentionally simple);
  a note field could be added later if the need arises.
- The browser toggle updates the on-disk list on the machine running the
  server (the same local `data/ignored.txt` the CLI reads), keeping every
  view — terminal, HTML, and daily check — consistent.
