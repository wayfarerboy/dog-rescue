# Candidate Rescue Centre Triage

Triage date: 2026-07-26. 23 of 25 candidates classified (2 missing — `data/discovered_places.json` was not found in repo). All classifications confirmed via `curl`/HTTP fetch of live websites. Timeout/defunct sites confirmed with at least 2 attempts.

---

## Summary

| Category | Count |
|----------|-------|
| Viable | 10 |
| False Positive | 3 |
| Defunct | 3 |
| No Website | 3 |
| Blocked (Cloudflare) | 3 |
| Needs Investigation | 0 |
| Viable (External Platform) | 1 |
| **Total classified** | **23** |
| Missing (no source data) | 2 |

---

## Viable (10)

Sites with adoptable dogs and scrapable listing pages.

### 1. Starfish Dog Rescue ★★★
- **Website:** https://starfishdogrescue.co.uk
- **Listing URL:** https://starfishdogrescue.co.uk/dogs-looking-for-a-home
- **Detail page pattern:** Single-page listing — all dog info inline. No separate detail pages; each dog is a Divi module on the listing page.
- **Platform:** WordPress (Divi theme)
- **Approx. dogs visible:** ~10–15
- **Notes:** All data (name, age, breed, gender, description) rendered inline on single page. BeautifulSoup-friendly. No pagination.

### 2. Rainbow Dog Rescue ★★★ → DEAD END
- **Website:** https://www.rainbowdogrescue.co.uk
- **Listing URL:** https://www.rainbowdogrescue.co.uk/our-dogs/
- **Status (2026-07-26):** NOT VIABLE. Page only links to Facebook — "All of our wonderful doggie's reside on our Facebook Page." No dog cards on site. No scrapable content.
- **Platform:** WordPress
- **Notes:** Originally classified viable based on site structure, but live inspection shows zero dogs listed on the website itself.

### 3. Brighter Days Rescue ★★★
- **Website:** https://www.brighterdaysrescue.com
- **Listing URL:** https://brighterdaysrescue.com/dogs/available
- **Detail page pattern:** `/dogs/{name}-{id}` (e.g., `/dogs/albie`, `/dogs/elsie-jcyd`)
- **Platform:** Custom HTML (CloudFront-hosted images, likely custom CMS)
- **Approx. dogs visible:** ~12–20
- **Notes:** Well-structured listing with clear individual dog cards. Detail pages have full profiles. Server-rendered HTML. Good candidate for a scraper.

### 4. East Midlands Dog Rescue ★★★
- **Website:** https://www.eastmidlandsdogrescue.org
- **Listing URL:** https://www.eastmidlandsdogrescue.org/needing-a-home/
- **Detail page pattern:** `/product/{name}/` (WooCommerce) — e.g., `/product/aisha/`, `/product/alfie/`, `/product/baron/`, `/product/bea/`
- **Platform:** WordPress + WooCommerce
- **Approx. dogs visible:** ~8–12 (paginated: `?product-page=2`)
- **Notes:** Dogs are WooCommerce products. Detail pages contain full breed/age/gender info. Paginated listing. This is the same pattern as Jerry Green. Excellent scraping candidate.

### 5. Birmingham Dogs Home ★★☆
- **Website:** https://birminghamdogshome.org.uk
- **Listing URL:** https://birminghamdogshome.org.uk/our-dogs/
- **Detail page pattern:** `/dogs/{name}-{id}/` — e.g., `/dogs/romeo-138703/`, `/dogs/harley-138676/`, `/dogs/rouge-138713/`
- **Platform:** WordPress + Elementor + Sunshine3 CRM (API/JS-driven filters)
- **Approx. dogs visible:** ~20–30
- **Notes:** Large inventory. JS-driven search/filter on listing page but server-rendered HTML with dog cards. Detail pages are clean HTML. Filtering may require POST or query params to the Sunshine3 CRM API.

### 6. Forest of Dean Dog Rescue ★★☆
- **Website:** https://www.foddogrescue.org.uk
- **Listing URL:** https://www.foddogrescue.org.uk/dogs-for-adoption
- **Detail page pattern:** Single-page listing — all dogs inline on one Wix page
- **Platform:** Wix
- **Approx. dogs visible:** ~15–25
- **Notes:** Wix-rendered, server-delivered HTML. All dog profiles visible on the single listing page (images, names, descriptions). May need to parse Wix's JSON data structures for structured data.

### 7. Wild Acre Rescue ★★☆
- **Website:** https://wildacrerescue.co.uk
- **Listing URL:** https://wildacrerescue.co.uk/dogs-for-adoption/
- **Detail page pattern:** Single-page listing — all dogs inline (WordPress)
- **Platform:** WordPress
- **Approx. dogs visible:** ~3–8 (small inventory)
- **Notes:** Small rescue with detailed dog profiles. Names, descriptions, images all inline. Has separate `/adoption-information/` and `/happily-rehomed/` pages.

### 8. German Shepherd Rescue (GSDR) ★★☆
- **Website:** https://www.germanshepherdrescue.co.uk
- **Listing URL:** https://www.germanshepherdrescue.co.uk/urgent-dogs-c-62.html
- **Detail page pattern:** `adopt-german-shepherd-i-{id}.html`
- **Platform:** osCommerce (custom HTML)
- **Approx. dogs visible:** ~10–15
- **Notes:** Breed-specific (German Shepherds = large dogs, out of scope for small/medium focus). Good data format though — osCommerce product pages with clear structure. Also has `adoption-i-15.html` for non-urgent dogs. **Warning:** German Shepherds are large breed — all dogs will be filtered out by size rules.

### 9. Happy Staffie Rescue ★☆☆
- **Website:** https://www.happystaffie.co.uk
- **Listing URL:** https://www.happystaffie.co.uk/adopt
- **Detail page pattern:** Single-page listing — all dogs inline on Wix page
- **Platform:** Wix
- **Approx. dogs visible:** ~5–10
- **Notes:** Staffie/bull breed focused (medium dogs). Small inventory. Wix-rendered page with all dog info inline. Based in Worcestershire (close to origin).

### 10. Small Dog Rescue ★☆☆
- **Website:** https://www.smalldogrescue.co.uk
- **Listing URL:** https://www.smalldogrescue.co.uk/dogs-for-rehoming
- **Detail page pattern:** Single-page listing — all dogs inline on Wix page
- **Platform:** Wix
- **Approx. dogs visible:** ~5–10
- **Notes:** Small breed focus (good for size filter). Wix-rendered. Dogs listed inline with images and descriptions. Also has `/gallery` page and `/archived-testimonials`.

---

## Needs Investigation (1)

Sites that may be viable but have unresolved questions.

### 11. Amicii Dog Rescue ★★☆
- **Website:** https://amiciidogrescue.org.uk
- **Listing URL:** https://www.pets4homes.co.uk/user/amicii-dog-rescue-37d14269-6354-434b-a8b7-bf132ff1d329/ (Pets4Homes)
- **Detail page pattern:** `/adoption/dogs/{slug}/` on Pets4Homes
- **Platform:** Pets4Homes (Next.js SSR with `__NEXT_DATA__` JSON)
- **Approx. dogs visible:** 22 active adverts across 6 pages
- **Investigation result (2026-07-26):** UK dogs are listed on Pets4Homes, not the Amicii website. The Amicii site has two sections: "Our UK Dogs" → links to Pets4Homes profile; "Our Dogs in Romania" → internal Sobipro Joomla directory. UK dogs are physically in UK foster/rehoming centres (various locations: Worcester, Kidderminster, Malvern, Derby, Stafford). **Viable for scraping** via Pets4Homes Next.js SSR JSON — all dog data (name, age, gender, breed, photo, location) in structured `__NEXT_DATA__` JSON. 6 pages × 4 items/page (22 total). Pagination via `?page=N`. Breed always "Mixed Breed" in structured data (no specific breed). Gender from `numberOfMales`/`numberOfFemales` attributes. Age from `dateOfBirth` timestamp. Photo URL uses `##NAME##` placeholder → replace with `image`. Rescue location: Worcester (HQ); dogs in various UK foster locations.

---

## False Positive (3)

Sites that are legitimate rescue organisations but do not have adoptable dogs.

### 12. Goodheart Animal Sanctuaries
- **Website:** https://www.goodheart.org.uk (also tried goodheartanimalsanctuaries.co.uk — timed out twice)
- **Classification:** Farm animal and cat sanctuary. 0 dog mentions on homepage. Animals: cats (69 mentions), horses, goats, sheep, pigs, cows, hens, chickens, rabbits, alpacas. No dog rehoming or adoption content.
- **Verdict:** FALSE POSITIVE — no dogs.

### 13. Happyfields Animal Sanctuary
- **Website:** https://www.happyfieldsanimalsanctuary.co.uk
- **Classification:** Farm animal sanctuary (sheep, goats, donkeys, horses). Has animal profiles (Dolly, Poppy, Millie, Charlie, Cyril, etc.) but these are predominantly cats and farm animals. Dog mentions are minimal (1 per profile page) and no dog adoption listing exists.
- **Verdict:** FALSE POSITIVE — farm animals, no dog adoption program.

### 14. Severn Valley Rescue
- **Website:** https://www.severnvalleyrescue.org
- **Classification:** Primarily a donkey sanctuary (37 donkey mentions vs 18 dog mentions). Also cats, ponies, pigs, hens, alpacas. "Donkey Sanctuary & Dog Rescue" in title but the dog rescue is secondary. No browsable dog listing page found — `/dogs-needing-homes/`, `/dogs/`, `/dog-rescue/` all 404.
- **Verdict:** FALSE POSITIVE — donkey sanctuary with minimal dog rescue. No scrapable dog listing.

---

## Defunct (3)

Sites with non-functional websites.

### 15. Wythall Animal Rescue
- **URL attempted:** https://wythallanimalrescue.org (also wythallanimalrescue.org — same result)
- **Status:** Cloudflare 525 SSL handshake failed. Domain resolves but backend is dead. Title tag is "Slot Online Gacor Terbaru" — domain has been hijacked or repurposed.
- **Attempts:** 2 — both return Cloudflare 525.
- **Verdict:** DEFUNCT — hijacked domain.

### 16. Noah's Ark Dog Rescue
- **URL attempted:** https://www.noahsarkdogrescue.co.uk
- **Status:** Parked domain. Returns 1108 bytes — just a fingerprint JS redirect script and no actual content. Not a real website.
- **Attempts:** 2 — identical result both times.
- **Verdict:** DEFUNCT — parked domain.

### 17. Teckels Animal Sanctuary
- **URLs attempted:** teckels.co.uk (no relevant content, no title), teckelsanimalsanctuary.co.uk (connection error), teckelsanimalsanctuary.org (connection error), teckelsanimalsanctuary.com (connection error), teckels.org.uk (connection error), teckels.org (114 bytes, empty)
- **Status:** The domain teckels.co.uk resolves but has no animal/rescue/dog content. All other variants fail to connect. The original Teckels Animal Sanctuary appears to have no functioning website.
- **Attempts:** 2+ per URL variant.
- **Verdict:** DEFUNCT — no functioning website found for the rescue organisation.

---

## No Website (3)

Candidates that have no discoverable website.

### 18. Two Hoots
- **URLs attempted:** twohootsrescue.co.uk, twohoots.co.uk, twohootsanimalrescue.org.uk, twohootsfarm.co.uk — all connection errors.
- **Verdict:** NO WEBSITE — no functioning domain found.

### 19. Heronfield
- **URLs attempted:** heronfieldrescue.co.uk, heronfieldanimalrescue.co.uk, heronfieldfarm.co.uk — all connection errors. heronfield.org resolves but is a "New Hampshire Private Middle School" in the US.
- **Verdict:** NO WEBSITE — UK rescue has no website; heronfield.org is unrelated (US school).

### 20. Hillfields
- **URLs attempted:** hillfieldsrescue.co.uk, hillfieldsanimalrescue.co.uk — connection errors. hillfields.org.uk resolves but is a Vietnamese gambling site ("NOHU90 | Cổng Game Nohu90.com Uy Tín #1 Châu Á 2026").
- **Verdict:** NO WEBSITE — domain hijacked by gambling site.

---

## Blocked (3)

Blue Cross centres — all behind Cloudflare anti-bot protection.

### 21. Blue Cross Bromsgrove
- **URL:** https://www.bluecross.org.uk/bromsgrove-rehoming-centre
- **Status:** HTTP 403 Forbidden. Cloudflare WAF blocks all non-browser requests.
- **Attempts:** 2 — consistent 403.
- **Known:** Blue Cross is a JS SPA with Cloudflare protection. The rehoming centres share the national CMS. Could potentially be accessed via Playwright with stealth plugins.
- **Verdict:** DONE — checker built using API endpoints (`sites/blue_cross.py`).

### 22. Blue Cross Burford
- **URL:** https://www.bluecross.org.uk/burford-rehoming-centre
- **Status:** HTTP 403 Forbidden. Cloudflare WAF.
- **Attempts:** 2 — consistent 403.
- **Verdict:** BLOCKED — Cloudflare.

### 23. Blue Cross Rolleston
- **URL:** https://www.bluecross.org.uk/rolleston-rehoming-centre
- **Status:** HTTP 403 Forbidden. Cloudflare WAF.
- **Attempts:** 2 — consistent 403.
- **Verdict:** BLOCKED — Cloudflare.

---

## Missing (2)

Two candidates from the original 25 were not found. The source file `data/discovered_places.json` was not present in the repository at time of triage and could not be regenerated (no Google Maps API key configured). The issue body names 23 candidates in the platform context section. The remaining 2 are unknown.

---

## Platform Summary

| Platform | Sites |
|----------|-------|
| WordPress | Starfish, Rainbow, East Midlands Dog Rescue, Wild Acre, Birmingham Dogs Home |
| Wix | Forest of Dean, Happy Staffie, Small Dog Rescue |
| Custom HTML | Brighter Days |
| osCommerce | German Shepherd Rescue |
| Pets4Homes (Next.js SSR) | Amicii (UK dogs) |
| Joomla/Sobipro | Amicii (Romanian dogs) |
| Blue Cross CMS (blocked) | Bromsgrove, Burford, Rolleston |

---

## Triage Decisions

| # | Name | Category | Key Factor |
|---|------|----------|------------|
| 1 | Starfish Dog Rescue | Viable | WordPress, single-page listing |
| 2 | Rainbow Dog Rescue | Viable | WordPress, single-page listing |
| 3 | Brighter Days Rescue | Viable | Custom HTML, /dogs/{name}-{id} detail pages |
| 4 | East Midlands Dog Rescue | Viable | WooCommerce, /product/{name}/ detail pages |
| 5 | Birmingham Dogs Home | Viable | WordPress, /dogs/{name}-{id}/ detail pages |
| 6 | Forest of Dean Dog Rescue | Viable | Wix, single-page listing |
| 7 | Wild Acre Rescue | Viable | WordPress, small inventory |
| 8 | German Shepherd Rescue | Viable | osCommerce, large breed only (filtered out) |
| 9 | Happy Staffie Rescue | Viable | Wix, small inventory |
| 10 | Small Dog Rescue | Viable | Wix, small breed focus |
| 11 | Amicii Dog Rescue | Viable via Pets4Homes | 22 UK dogs on Pets4Homes, structured JSON, paginated |
| 12 | Goodheart Animal Sanctuaries | False Positive | Farm animals + cats only, no dogs |
| 13 | Happyfields Animal Sanctuary | False Positive | Farm animals, no dog adoption |
| 14 | Severn Valley Rescue | False Positive | Donkey sanctuary, minimal dog rescue |
| 15 | Wythall Animal Rescue | Defunct | Hijacked domain (gambling) |
| 16 | Noah's Ark Dog Rescue | Defunct | Parked domain |
| 17 | Teckels Animal Sanctuary | Defunct | No functioning website |
| 18 | Two Hoots | No Website | No domain found |
| 19 | Heronfield | No Website | UK rescue has no website |
| 20 | Hillfields | No Website | Domain hijacked |
| 21 | Blue Cross Bromsgrove | Blocked | Cloudflare 403 |
| 22 | Blue Cross Burford | Blocked | Cloudflare 403 |
| 23 | Blue Cross Rolleston | Blocked | Cloudflare 403 |
| — | Unknown (×2) | Missing | Not in source data |

---

## Next Steps

1. **Scraper-ready (Priority 1):** Brighter Days, East Midlands Dog Rescue — clean detail URLs, server-rendered HTML, good data.
2. **Scraper-ready (Priority 2):** Starfish, Rainbow, Wild Acre — single-page WordPress, all data inline.
3. **Scraper-ready (Priority 3):** Forest of Dean, Happy Staffie, Small Dog Rescue — Wix-based, need Wix JSON parsing.
4. **Investigate:** Amicii — resolve Romanian import question before building scraper.
5. **Low priority/maybe skip:** German Shepherd Rescue (large breed only), Birmingham Dogs Home (already monitored in dog-rescues.md).
6. **Requires Playwright:** Blue Cross centres (blocked by Cloudflare) — revisit if Playwright-based scraping is added to the project.
