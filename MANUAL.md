# Dog Rescue — User Manual

This tool monitors dog adoption sites for dogs that match your criteria
(female, under 1 year), filters them by driving distance from home, and helps
you track which ones you've already looked at.

## Single point of entry

Launch the interactive menu from the repo root:

```bash
./dogs
```

That's the only command you need. Everything lives inside the menu — no need to
remember script names or flags.

### What if `./dogs` doesn't work?

```bash
uv run python cli.py     # if uv is installed
python3 cli.py           # fallback
```

## How to navigate the menus

- Type the **letter/number** shown next to an option, then press **Enter**.
- **`q`** (or **`0`**) at any submenu returns to the previous menu.
- **`q`** at the main menu exits.
- Press **Help (1)** at the main menu any time to see this guidance on screen.

## Menu map

```
Dog Rescue CLI
├─ 1  Help / How to use
├─ 2  Daily Check + Email        fetch all sites → filter by distance → email new dogs
├─ 3  List Dogs                  see currently available dogs
│    ├─ 1  Live fetch → terminal table
│    ├─ 2  Cached data → terminal table
│    ├─ 3  Live fetch → HTML file (dogs.html)
│    ├─ 4  Cached data → HTML file
│    ├─ 5  Open dogs.html in browser
│    └─ 6  List only unseen (cached, hide discounted)
├─ 4  Manage Discounted Dogs     track dogs you've looked at and dismissed
│    ├─ 1  Browse & mark (interactive)
│    └─ 2  View / manage discounted list
├─ 5  Cache Management           populate / repair / browse per-site cache files
├─ 6  Distance & Location        distances, too-far list, breed exclusions
├─ 7  Discover New Rescues       search for new rescue sites (Places API)
├─ 8  Tests & Diagnostics        run tests, lint, audit, environment info
└─ 0  Exit
```

## Your daily workflow

1. **Daily Check + Email (2)** — fetches every site, applies filters, and
   emails you any new dogs. Run this first.
2. **List Dogs (3)** — see what's currently available as a terminal table or
   an HTML page you can open in a browser.
3. **Browse & mark (4 → 1)** — step through the dogs. This is where you tell
   the tool which ones you've already decided against.

## Browsing & marking dogs as "discounted"

In **Manage Discounted Dogs → Browse & mark**, each dog is numbered and shown
with its details and profile URL:

- Type a **number** → that dog's URL is **copied to your system clipboard**
  (uses `pbcopy` on macOS, `xclip`/`xsel` on Linux, `clip` on Windows). Paste
  it into a browser to look at the dog. This works over SSH because the copy
  happens on the machine running the CLI.
- Type **`d<number>`** (e.g. `d7`) → toggles that dog as **discounted**
  (looked at and dismissed).
- **`r`** → re-fetch. **`0`/`q`** → back.

### Where discounted dogs appear

- **Terminal table:** discounted rows are tagged `[D]`.
- **HTML page:** discounted cards are dimmed, the name is struck through, and
  a "discounted" badge is shown. The header reports `N new / M discounted`.
- **List only unseen (3 → 6):** hides every dog you've already discounted so
  only new ones remain.

Discounted status is stored locally in `data/discounted.txt`, keyed by the
dog's **profile URL** (names aren't unique). A dog is treated as new again if
its URL changes, or if you remove it via **Manage Discounted (4 → 2)**.

## Other tools

- **Cache Management (5)** — rebuild the per-site cache from scratch
  (populate), fix entries by re-scraping profile pages (repair), or browse the
  raw cache files.
- **Distance & Location (6)** — view cached driving distances from home,
  maintain the too-far list (centres beyond the maximum distance), look up a
  single centre, auto-detect too-far rescues, and manage breed exclusions.
- **Discover New Rescues (7)** — search Google Places for new rescue sites.
- **Tests & Diagnostics (8)** — run the test suite, linting, a cache audit,
  and environment info.

## Configuration

Settings live in `.env` (see `.env.example`). `./dogs` reads them
automatically. Key variables: `EMAIL`, `SUBJECT`, `GOOGLE_MAPS_API_KEY`,
`MAX_DISTANCE_MILES`.
