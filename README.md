# Dog Rescue

Checks multiple dog adoption websites for new dogs matching criteria
(female, under 1 year old) and sends email notifications via msmtp.

## Sites monitored

| Site | Method |
|------|--------|
| **Many Tears Rescue** | URL query params → HTML scrape (BeautifulSoup) |
| **Second Chance Spaniel Rescue** | HTML scrape → content filter |
| **Dogs Trust** | GraphQL API |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # edit with your email
brew install msmtp      # for sending email
```

## Usage

```bash
python3.14 dog_rescue.py
```

### Cron (daily at 8am)

```
0 8 * * * cd /Users/alpagan/Documents/dog-rescue && python3.14 dog_rescue.py
```

## Structure

```
.
├── dog_rescue.py         # Main orchestrator
├── .env.example          # Example config (commit this)
├── .env                  # Your config (gitignored)
├── sites/
│   ├── base.py           # Dog dataclass + SiteChecker ABC
│   ├── many_tears.py     # Many Tears Rescue
│   ├── scsr.py           # Second Chance Spaniel Rescue
│   └── dogs_trust.py     # Dogs Trust
└── data/                 # Previous run data (gitignored)
```
