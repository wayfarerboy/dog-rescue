# UK Dog Rescue Websites for Scraping

Research compiled 2026-07-24. Focus: female dogs, under 1 year (preferably under 6 months), small/medium size.

## Summary

6 strong candidates with server-rendered HTML and browsable listings, plus 1 with a REST API. 5 major sites (RSPCA, Blue Cross, Battersea, NAWT, Hope Rescue) are JS SPAs. Dogs Trust is already monitored.

**Update 2026-07-25:** 6 additional sites evaluated. RSPCA branch sites (Leeds, Brighton, Cotswolds) are independently scrapable unlike the national JS SPA.

---

## Candidate Sites (ranked by scraping suitability)

### 1. Pro Dogs Direct ★★★
- **URL:** https://prodogsdirect.org.uk/dogs-for-adoption/
- **Filters:** Category dropdown (Available dogs, Reserved, Applications Closed, Rehomed, etc.) — no age/gender/size filter
- **Rendering:** Server-rendered HTML (WordPress). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Age text, Gender, Breed, Foster location
- **Data shown:** Breed ✓, Age ✓ (text: "12 Week Old Male", "6 Year Old Female"), Gender ✓, Location ✓ (foster town), Status ✓ (available/reserved)
- **Notes:** Very high density of small dogs (Pomeranians, Dachshunds, Spaniels, Poodles, Chihuahuas). ~50 dogs listed. Single-page flat list. No pagination.

### 2. Jerry Green Dog Rescue ★★★
- **URL:** https://www.jerrygreendogs.org.uk/dogs/
- **Filters:** Location dropdown (4 centres), Availability (Available/Reserved). Age/gender/size not filterable but SIZE IS TAGGED on cards.
- **Rendering:** Server-rendered HTML (WordPress/WooCommerce). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Breed, Age (years + months), Gender, Size tag (Small/Medium/Large), children compatibility, housetrained, garden needs.
- **Data shown:** Breed ✓, Age ✓ (precise: "0 years 1 months"), Gender ✓, Size ✓ (Small/Medium/Large tag), Location ✓ (centre), Status ✓
- **Notes:** Size tags make this excellent for size-based filtering. 12 dogs currently visible. The "Meet&Match" process means not all dogs visible without registration, but the public listing is good.

### 3. Spaniel Aid ★★★
- **URL:** https://spanielaid.co.uk/available-dogs/
- **Filters:** None. Flat list. Paginated.
- **Rendering:** Server-rendered HTML. BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Breed, Age (months/years), Location (town), Gender, Child compatibility, Cat compatibility.
- **Data shown:** Breed ✓, Age ✓ ("15 months", "4 years 6 months"), Gender ✓, Location ✓ (town + county), Status ✓ (includes "Reserved while we review")
- **Notes:** Excellent for small/medium spaniels and crosses (Springer, Cocker, Sprocker, Cockapoo). ~14 dogs currently. Breed-specific but spaniel crosses can be any size.

### 4. All Dogs Matter ★★☆
- **URL:** https://alldogsmatter.co.uk/dogs/
- **Filters:** None. Paginated (17 pages).
- **Rendering:** Server-rendered HTML (WordPress). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Breed, Age, Gender, Location (centre/area).
- **Data shown:** Breed ✓, Age ✓ ("1 year old", "9 Months"), Gender ✓, Location ✓ (Waltham Abbey, North London, etc.), Status ✗ (adopted dogs remain on page marked "I have been adopted!")
- **Notes:** Large inventory (hundreds of dogs across 17 pages). Need to filter out adopted dogs (marked with "I have been adopted!"). Mix of sizes from Chihuahua to Mastiff.

### 5. The Mayhew ★★☆
- **URL:** https://themayhew.org/dogs/
- **Filters:** Can live with cats (Any/Yes/No/Possibly), Can live with other dogs, Can live with children, Can be left alone, Can live in a flat. Form-based filtering (likely query params).
- **Rendering:** Server-rendered HTML (WordPress). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Age, Breed.
- **Data shown:** Breed ✓, Age ✓ ("2 years 3 months old", "10 months old"), Gender ✗ (not shown on cards — need to visit detail page), Location ✗ (not on cards)
- **Notes:** ~20 dogs across 10 pages. Gender is missing from listing cards — would require detail page scraping. Good for small dogs (Pugs, Dachshunds, small terriers). Filter system is form-based POST.

### 6. Woodgreen Pets Charity ★★☆
- **URL:** https://woodgreen.org.uk/pets/ (dogs at /pets/dogs/ redirects to /pets/ with species filter applied)
- **Filters:** Species, Breed, "Can I live with..." compatibility filters, "Other filters". Rich filter system with breed dropdown.
- **Rendering:** Server-rendered HTML (WordPress). **Also has REST API at `/wp-json/wp/v2/pets`**.
- **Listing format:** Individual cards. Each shows: Name, Breed, compatibility tags, status (Available/Reserved/Needs support).
- **Data shown:** Breed ✓, Age ✗ (not on cards), Gender ✗ (not on cards), Location ✗, Status ✓
- **Notes:** ~75 pets total (mixed species). Dogs are identifiable by breed. Age and gender NOT shown on listing cards — requires detail page or API ACF fields. The WP REST API is promising for programmatic access. "The Dog House" TV show charity.

### 7. Birmingham Dogs Home ★☆☆ (limited inventory)
- **URL:** https://birminghamdogshome.org.uk/our-dogs/
- **Filters:** "Search for a dog" feature exists (JS-driven). Only 6 "Featured Available Dogs" shown.
- **Rendering:** Server-rendered HTML (WordPress/Elementor). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Breed, Age (years + months), Gender, Neutered status.
- **Data shown:** Breed ✓, Age ✓ (precise: "10 years 2 months"), Gender ✓ ("Male (N)" for neutered), Location ✓ (2 centres: Birmingham & Wolverhampton implied)
- **Notes:** Very limited public inventory (6 dogs). Good data format. Would need to investigate if there are more dogs accessible via search.

---

## Excluded Sites

| Site | Reason |
|------|--------|
| **RSPCA** (rspca.org.uk/findapet) | JS SPA on Liferay. API endpoint returns "Undeployed". Search is JavaScript-only. No accessible REST endpoint found. |
| **Blue Cross** (bluecross.org.uk) | JS SPA with Cloudflare WAF. All direct URL attempts return 403 or 404. Listing page at /rehome-pet only shows species selector. |
| **Battersea** (battersea.org.uk) | Matchmaking model — no browsable dog listings. Register first, they match you. |
| **NAWT** (nawt.org.uk) | JS SPA — all direct URLs 404. Homepage navigation uses JavaScript routing. Dog cards shown on homepage but no dedicated listing page accessible via URL. |
| **Hope Rescue** (hoperescue.org.uk) | JS SPA — category-based navigation. No direct URL for dog listings found. |
| **Rescue Remedies** (rescueremedies.co.uk) | All URLs tested returned 404. Site may be defunct or restructured. |
| **Stokenchurch Dog Rescue** | /dogs/ page only shows already-rehomed dogs, not available ones. |
| **Underdog International** | Timed out. Likely JS SPA. |
| **Labrador Retriever Rescue SE** (labrador-rescue.org.uk) | Static HTML with 5 dogs. Requires application form for full inventory. Not scrape-able for full listing. |

---

## Technical Notes

### Scraping approach per site

**BeautifulSoup-friendly (server-rendered HTML):**
- Pro Dogs Direct: Simple flat page, all dogs on one page
- Jerry Green: Flat page, all dogs on one page, filter via `<select>` form
- Spaniel Aid: Flat page, ~14 dogs
- All Dogs Matter: Paginated (`/dogs/page/2/`), need to skip adopted dogs
- The Mayhew: Form POST for filters, paginated
- Birmingham Dogs Home: Simple cards, very limited

**API-accessible:**
- Woodgreen: WordPress REST API at `/wp-json/wp/v2/pets`. ACF custom fields may contain age/gender/status. Needs investigation.

### Filter mechanisms

| Site | Age filter | Gender filter | Size filter | Breed filter | Mechanism |
|------|-----------|---------------|-------------|--------------|-----------|
| Pro Dogs Direct | ✗ | ✗ | ✗ | ✗ | Category dropdown only |
| Jerry Green | ✗ | ✗ | ✗ (but tagged) | ✗ | Form select (location, availability) |
| Spaniel Aid | ✗ | ✗ | ✗ | ✗ | None |
| All Dogs Matter | ✗ | ✗ | ✗ | ✗ | Pagination only |
| The Mayhew | ✗ | ✗ | ✗ | ✗ | Form POST (compatibility filters) |
| Woodgreen | ✗ | ✗ | ✗ | ✓ dropdown | Form POST + WP REST API |

**Conclusion:** None of the sites offer age or gender filtering. All filtering must be done post-scrape. This is consistent with the currently monitored sites.

### JavaScript SPAs (requires Playwright/Selenium, not BeautifulSoup)
- RSPCA, Blue Cross, NAWT, Hope Rescue, Dogs Trust (already monitored), Battersea

---

## Recommendations

### Priority for integration (by ease + data quality):
1. **Pro Dogs Direct** — easiest (flat page, all data, lots of small/young dogs)
2. **Spaniel Aid** — easy (flat page, clear data, spaniels are small/medium)
3. **Jerry Green** — easy (size tags are unique, good location filter)
4. **All Dogs Matter** — medium (paginated, need to filter adopted dogs)
5. **Woodgreen** — medium (REST API promising but age/gender not visible)
6. **The Mayhew** — harder (gender missing from cards)

### Post-scrape filtering strategy
- Scrape all available dogs from each site
- Parse age text into months (e.g., "12 Week Old" → 3 months, "1 year 2 months" → 14 months)
- Filter: gender == Female AND age_months <= 12 AND size in (Small, Medium)
- Store in unified format for notification

---

---

## Additional Sites (researched 2026-07-25)

### South East Dog Rescue ★★★
- **URL:** https://www.sedogrescue.co.uk/adopt-a-dog/
- **Filters:** None on listing page. All dogs on one page.
- **Rendering:** Server-rendered HTML. BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Age, Gender, Breed.
- **Data shown:** Breed ✓, Age ✓, Gender ✓, Location ✗ (Kent-based, some foster UK-wide per site text), Status ✓ (all dogs on this page are available)
- **Notes:** Small inventory (6 dogs currently). Data quality is excellent — every card has breed, precise age, and gender. Includes small breeds (Terrier, Pomeranian x Husky, Cavachon, Shih Tzu). Adoption donation £400.

### Raystede ★★☆
- **URL:** https://www.raystede.org/adopt/dogs/
- **Filters:** None visible. All dogs on one page.
- **Rendering:** Server-rendered HTML (WordPress). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Age, Status ("Home Found", "Video" tag, etc.)
- **Data shown:** Breed ✗ (not on cards), Age ✓ ("1 year 1 month", "11 months"), Gender ✗ (not on cards), Location ✗, Status ✓
- **Notes:** ~14 dogs. Includes young dogs (Dolly, 11 months; Stanley, 1 year 1 month). Breed and gender require detail page scraping. Some dogs already marked "Home Found" — filter those out.

### Cotswolds Dogs & Cats Home (CDCH) ★★☆
- **URL:** https://cotswoldsdogsandcatshome.org.uk/adopt-a-dog/
- **Filters:** None. Paginated sections (Available / Reserved).
- **Rendering:** Server-rendered HTML. BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Gender, Status (Available/Reserved), "Dog" label (species). Numbered cards.
- **Data shown:** Breed ✗ (not on cards), Age ✗ (not on cards), Gender ✓, Location ✗, Status ✓
- **Notes:** ~12 dogs available + reserved section. RSPCA Cotswolds branch. Breed and age require detail page scraping. High proportion of females in current inventory.

### Paws2Rescue ★★☆
- **URL:** https://paws2rescue.com/dogs/
- **Filters:** Sex (Good Boy/Good Girl/All), Size (Small/Small-Medium/Medium/Medium-Large/Large), Location (Romania/England/Scotland/Wales)
- **Rendering:** Server-rendered HTML (WordPress). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Sex icon + Size tag + Location tag. No name, no breed, no age visible on cards.
- **Data shown:** Breed ✗, Age ✗, Gender ✓ (via Good Boy/Good Girl), Location ✓ (country-level), Status ✗
- **Notes:** Large inventory (~35 dogs). **Most dogs are in Romania** — imported rescue. Sex + size filters are useful but lack of age and breed on cards means detail page scraping is essential. Good for finding small/medium females if you're willing to scrape detail pages.

### RSPCA Leeds & Wakefield ★★☆
- **URL:** https://www.rspcaleedsandwakefield.org.uk/dogs/
- **Filters:** None.
- **Rendering:** Server-rendered HTML. BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Age, Gender.
- **Data shown:** Breed ✗ (not on cards), Age ✓, Gender ✓, Location ✗, Status ✓
- **Notes:** Very small inventory (5 dogs currently). Good data format. RSPCA branch — independent from the national JS SPA. Breed missing from cards.

### RSPCA Brighton & Heart of Sussex ★★☆
- **URL:** https://rspca-brighton.org.uk/animals/dogs/
- **Filters:** None.
- **Rendering:** Server-rendered HTML (WordPress). BeautifulSoup-compatible.
- **Listing format:** Individual cards. Each shows: Name, Status ("New arrival", "Reserved", "No more applications being taken").
- **Data shown:** Breed ✗ (not on cards), Age ✗ (not on cards), Gender ✗ (not on cards), Location ✗, Status ✓
- **Notes:** ~20 dogs — best inventory of the RSPCA branches checked. But cards show ONLY name and status. All breed/age/gender data requires detail page scraping. Adoption fee £300 (£350 for puppies).

---

### Newly Evaluated & Excluded

| Site | Reason |
|------|--------|
| **Blue Cross** (bluecross.org.uk) | Reconfirmed JS SPA. All direct dog-listing URLs return 404. Species selector at /rehome-pet works but dog listings require client-side JS navigation. **Playwright-able** if worth the effort. |
| **Hope Rescue** (hoperescue.org.uk) | JS category selector at /dogs-for-adoption. All /dogs/, /adopt/, /rehome/ etc. 301-redirect back to /dogs-for-adoption. No server-rendered dog listing pages found. **Playwright needed** to click through categories. |
| **RSPCA national** (rspca.org.uk/findapet) | Reconfirmed JS SPA. Search form renders but results are JS-driven. **Playwright needed.** RSPCA branch sites (Leeds, Brighton, Cotswolds) are independent WordPress sites and ARE scrapable. |
| **Border Collie Trust GB** (bordercollietrustgb.org.uk) | /dogs.html and all listing URLs return 404. Site appears to have no public dog listings — just info pages and a photo gallery of kennels. |
| **CAESSR** (caessr.org.uk) | Spaniel rescue. All listing URLs return 404. Homepage shows one "Featured Dog" but no browsable listings found. |
| **Greyhound Trust** | Excluded — greyhounds are large dogs (outside small/medium focus). |
| **Irish Retriever Rescue** | Excluded — retrievers are medium/large. |
| **Pawz For Thought** | /dogs/ returns page with no dog cards — just contact info and a "Find the Perfect Pooch" blurb. No public listings. |
| **Finding Furever Homes** | /dogs/ page says "Sorry, no listings were found." Empty inventory. |
| **Ruff Start Rescue** | /dogs/ is a blog post, not a listing page. |
| **Animal Rescue and Care** | /dogs/ is a contact/adoption form, not a listing page. |
| **Pawprints Dog Rescue** | All listing URLs 404. |
| **Starlight Trust** | /dogs/ 404. |
| **Oakwood Dog Rescue** | 301 redirect but destination also 404. |
| **DogsBlog.com** | Timed out (20s). Likely defunct or JS-heavy. |
| **Pug Rescue UK** | Domain not resolving (DNS error). |
| **French Bulldog Saviours** | Domain not resolving (DNS error). |

---

## RSPCA Branch Strategy

RSPCA branches run independent WordPress sites that are often server-rendered and scrapable, unlike the national JS SPA. Confirmed scrapable:
- RSPCA Leeds & Wakefield (rspcaleedsandwakefield.org.uk/dogs/)
- RSPCA Brighton (rspca-brighton.org.uk/animals/dogs/)
- CDCH / RSPCA Cotswolds (cotswoldsdogsandcatshome.org.uk/adopt-a-dog/)

Other branches may be discoverable via RSPCA's branch finder at rspca.org.uk.

---

## Sources

- Kept: Pro Dogs Direct (prodogsdirect.org.uk/dogs-for-adoption) — high density of small dogs, server-rendered
- Kept: Jerry Green Dog Rescue (jerrygreendogs.org.uk/dogs) — size tags + age data, server-rendered
- Kept: Spaniel Aid (spanielaid.co.uk/available-dogs) — spaniel focus, server-rendered HTML
- Kept: All Dogs Matter (alldogsmatter.co.uk/dogs) — large inventory, WordPress
- Kept: The Mayhew (themayhew.org/dogs) — good filters, small-breed dogs
- Kept: Woodgreen Pets Charity (woodgreen.org.uk/pets) — WP REST API, large charity
- Kept: Birmingham Dogs Home (birminghamdogshome.org.uk/our-dogs) — good data format but tiny inventory
- Dropped: RSPCA — JS SPA, API inaccessible
- Dropped: Blue Cross — WAF-protected JS SPA, all URLs 404/403
- Dropped: Battersea — no browsable listings
- Dropped: NAWT — JS SPA navigation, no accessible listing URLs
- Dropped: Hope Rescue — JS SPA
- Dropped: Rescue Remedies — all URLs 404
- Dropped: Stokenchurch Dog Rescue — only rehomed dogs shown
- Dropped: Underdog International — timed out, likely SPA
- Dropped: Labrador Retriever Rescue SE — requires application form, only 5 public dogs
- Kept: South East Dog Rescue (sedogrescue.co.uk/adopt-a-dog/) — ★★★ all data on cards, small inventory
- Kept: Raystede (raystede.org/adopt/dogs/) — ★★☆ age on cards, breed/gender on detail pages
- Kept: Cotswolds Dogs & Cats Home (cotswoldsdogsandcatshome.org.uk/adopt-a-dog/) — ★★☆ gender on cards, age/breed on detail pages
- Kept: Paws2Rescue (paws2rescue.com/dogs/) — ★★☆ sex/size/location filters, mostly Romanian imports, no age/breed on cards
- Kept: RSPCA Leeds & Wakefield (rspcaleedsandwakefield.org.uk/dogs/) — ★★☆ independent RSPCA branch, small inventory
- Kept: RSPCA Brighton (rspca-brighton.org.uk/animals/dogs/) — ★★☆ independent RSPCA branch, best branch inventory (~20 dogs)
- Dropped: Blue Cross — JS SPA (Playwright-able but adds complexity)
- Dropped: Hope Rescue — JS category selector, no server-rendered listings
- Dropped: Border Collie Trust GB — no public dog listings
- Dropped: CAESSR — no browsable listings
- Dropped: Greyhound Trust — large breed only
- Dropped: Irish Retriever Rescue — medium/large breed
- Dropped: Pawz For Thought — no public listings
- Dropped: Finding Furever Homes — empty inventory
- Dropped: DogsBlog.com — timed out, likely defunct
- Dropped: Pug Rescue UK, French Bulldog Saviours — domains not resolving
- Dropped: Multiple other rescues — dead domains or no dog listings

## Gaps

- **Age/gender filtering:** No newly discovered site offers server-side age or gender filtering beyond those already documented.
- **RSPCA API:** The Liferay portlet response was "Undeployed" — the findapet API may have moved to a different endpoint. Worth investigating via browser DevTools on the live site.
- **Blue Cross:** May be scrape-able if the JS SPA uses a JSON API. The 403 from curl suggests Cloudflare Bot Management. Playwright with stealth plugins might work.
- **Woodgreen ACF fields:** The WP REST API returns ACF custom fields as empty arrays in listing view. Individual pet endpoints at `/wp-json/wp/v2/pets/{id}` may contain `acf` data with age/gender.
- **NAWT:** The homepage shows dog cards, suggesting the API is accessible. Network tab inspection in browser would reveal the endpoint.