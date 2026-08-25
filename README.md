# Dog Rescue

Checks 13 dog adoption websites for new dogs matching criteria
(female, under 1 year old), filters by driving distance from Worcester,
and sends email notifications via msmtp.

## Quick start

```bash
./dogs
```

That single command launches the interactive menu — the one point of entry for
everything (list dogs, browse & mark ignored dogs, daily email check, cache
management, distances, tests). Full walkthrough in [`MANUAL.md`](MANUAL.md);
on-screen help is also one keypress away inside the menu (option **1**).

## Sites monitored

| Site | Method |
|------|--------|
| **All Dogs Matter** | HTML scrape → content filter |
| **Cotswolds Dogs & Cats Home** | HTML scrape → detail pages |
| **Dogs Trust** | GraphQL API |
| **Jerry Green Dog Rescue** | HTML scrape |
| **Many Tears Rescue** | URL query params → HTML scrape |
| **Paws2Rescue** | WP REST API |
| **Pro Dogs Direct** | HTML scrape |
| **Raystede** | JSON API |
| **RSPCA Brighton** | HTML scrape → detail pages |
| **RSPCA Leeds & Wakefield** | HTML scrape → detail pages |
| **Second Chance Spaniel Rescue** | HTML scrape |
| **South East Dog Rescue** | HTML scrape → detail pages |
| **Spaniel Aid** | HTML scrape |

## Setup

```bash
uv sync
cp .env.example .env   # edit with your email + Google Maps API key
brew install msmtp      # for sending email
```

### `.env` config

| Variable | Description |
|----------|-------------|
| `EMAIL` | Your email address for notifications |
| `SUBJECT` | Email subject line |
| `GOOGLE_MAPS_API_KEY` | Google Maps Distance Matrix API key |
| `MAX_DISTANCE_MILES` | Max driving distance from Worcester (default: 120) |

## Usage

### Everything through the menu (recommended)

```bash
./dogs
```

Interactive menu covering: daily check + email, listing dogs, browsing & marking
dogs as ignored, cache management, distances, discovery, and tests.

### Daily check + email

```bash
uv run python dog_rescue.py
```

Fetches all sites live, filters by distance, caches results in `data/`,
and emails new dogs. Dogs from centers beyond `MAX_DISTANCE_MILES` are excluded.

### Terminal listing

```bash
uv run python list_dogs.py             # live-fetch all sites
uv run python list_dogs.py --cached    # read from cache files
```

Prints a pipe-delimited table of all available dogs. Dogs you've marked as
ignored are tagged `[I]`.

### HTML web page

```bash
uv run python list_dogs.py --html             # live-fetch → dogs.html
uv run python list_dogs.py --html --cached    # cache → dogs.html
```

Writes a self-contained `dogs.html` with styled cards, grouped by rescue,
with photo thumbnails and profile links. No external CSS/JS/fonts needed.
Ignored dogs are dimmed and struck through with a badge; the header shows
`N new / M ignored`.

### Ignored-dog tracking

Mark a dog as "looked at and dismissed" so new dogs stand out next time.
Ignored status is stored locally in `data/ignored.txt` (keyed by URL).

```bash
uv run python list_dogs.py --ignore <url>      # mark a dog as ignored
uv run python list_dogs.py --un-ignore <url>   # un-mark
uv run python list_dogs.py --hide-ignored     # only show unseen dogs
```

Or use the interactive CLI (`uv run python cli.py`):
- **Manage Ignored → Browse & mark** — type a dog's number to copy its URL
  to the clipboard (`pbcopy`/`xclip`/`clip`) so you can open it in a browser
  over SSH, and type `d<num>` to toggle it as ignored.
- **List Dogs → Serve HTML in browser** — opens the page in a browser where
  each card has a **Ignore / Un-ignore** button that saves straight back
  to `data/ignored.txt`, so marking from the page updates the system.
  (`uv run python serve.py` works too; press Ctrl-C to stop.)

### Cache management

```bash
uv run python populate_caches.py           # build baseline caches for all 13 sites
uv run python repair_cache.py              # repair entries by scraping profile pages
uv run python repair_cache.py --dry-run    # preview repairs without fetching
```

### Cron (daily at 8am)

```
0 8 * * * cd /Users/alpagan/Documents/dog-rescue && /Users/alpagan/.local/bin/uv run python dog_rescue.py
```

## Structure

```
.
├── dogs                  # Single entry point: ./dogs (launches cli.py)
├── cli.py                # Interactive menu hub
├── MANUAL.md             # User manual
├── dog_rescue.py         # Main orchestrator (fetch → filter → email)
├── list_dogs.py          # Terminal listing + HTML output
├── ignore.py           # Ignored-dog tracking (IgnoreList)
├── serve.py              # Local HTML server with live ignore toggles
├── populate_caches.py    # Build baseline cache files for all sites
├── repair_cache.py       # Repair cached entries via profile scraping
├── distance_lookup.py    # Google Maps Distance Matrix API lookup + cache
├── too_far.py            # Track rescues excluded by distance
├── .env.example          # Example config (commit this)
├── .env                  # Your config (gitignored)
├── sites/
│   ├── base.py           # Dog dataclass + SiteChecker ABC + field names
│   ├── registry.py       # Shared checker registry (get_checkers())
│   ├── all_dogs_matter.py
│   ├── cotswolds.py
│   ├── dogs_trust.py
│   ├── jerry_green.py
│   ├── many_tears.py
│   ├── paws2rescue.py
│   ├── pro_dogs_direct.py
│   ├── raystede.py
│   ├── rspca_brighton.py
│   ├── rspca_leeds.py
│   ├── scsr.py           # Second Chance Spaniel Rescue
│   ├── south_east_dog_rescue.py
│   └── spaniel_aid.py
├── tests/
│   ├── test_*.py         # Per-site tests + script tests
│   └── ...
└── data/
    ├── *.txt             # Per-site cache files (gitignored)
    ├── distances.json    # Center distance cache (gitignored)
    ├── too-far.txt       # Excluded rescues (gitignored)
    └── ignored.txt    # Ignored dog URLs (gitignored)
```
