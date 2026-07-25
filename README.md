# Dog Rescue

Checks 13 dog adoption websites for new dogs matching criteria
(female, under 1 year old), filters by driving distance from Worcester,
and sends email notifications via msmtp.

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
pip install -r requirements.txt
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

### Daily check + email

```bash
python3 dog_rescue.py
```

Fetches all sites live, filters by distance, caches results in `data/`,
and emails new dogs. Dogs from centers beyond `MAX_DISTANCE_MILES` are excluded.

### Terminal listing

```bash
python3 list_dogs.py             # live-fetch all sites
python3 list_dogs.py --cached    # read from cache files
```

Prints a pipe-delimited table of all available dogs.

### HTML web page

```bash
python3 list_dogs.py --html             # live-fetch → dogs.html
python3 list_dogs.py --html --cached    # cache → dogs.html
```

Writes a self-contained `dogs.html` with styled cards, grouped by rescue,
with photo thumbnails and profile links. No external CSS/JS/fonts needed.

### Cache management

```bash
python3 populate_caches.py           # build baseline caches for all 13 sites
python3 repair_cache.py              # repair entries by scraping profile pages
python3 repair_cache.py --dry-run    # preview repairs without fetching
```

### Cron (daily at 8am)

```
0 8 * * * cd /Users/alpagan/Documents/dog-rescue && python3 dog_rescue.py
```

## Structure

```
.
├── dog_rescue.py         # Main orchestrator (fetch → filter → email)
├── list_dogs.py          # Terminal listing + HTML output
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
    └── too-far.txt       # Excluded rescues (gitignored)
```
