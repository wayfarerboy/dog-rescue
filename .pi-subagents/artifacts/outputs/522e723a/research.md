# UK Dog Rescue Websites for Scraping

Research compiled 2026-07-24. Focus: female dogs, under 1 year (preferably under 6 months), small/medium size.

## Summary

6 strong candidates with server-rendered HTML and browsable listings, plus 1 with a REST API. 5 major sites (RSPCA, Blue Cross, Battersea, NAWT, Hope Rescue) are JS SPAs not easily scraped. Dogs Trust is already monitored.

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
Since no site offers age/gender/size filters server-side:
- Scrape all available dogs from each site
- Parse age text into months (e.g., "12 Week Old" → 3 months, "1 year 2 months" → 14 months)
- Filter: gender == Female AND age_months <= 12 AND size in (Small, Medium)
- Store in unified format for notification

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

## Gaps

- **Age/gender filtering:** None of the discovered sites offer server-side age or gender filtering. Post-scrape Python filtering is the only option.
- **RSPCA API:** The Liferay portlet response was "Undeployed" — the findapet API may have moved to a different endpoint. Worth investigating via browser DevTools on the live site.
- **Blue Cross:** May be scrape-able if the JS SPA uses a JSON API. The 403 from curl suggests Cloudflare Bot Management. Playwright with stealth plugins might work.
- **Woodgreen ACF fields:** The WP REST API returns ACF custom fields as empty arrays in listing view. Individual pet endpoints at `/wp-json/wp/v2/pets/{id}` may contain `acf` data with age/gender.
- **NAWT:** The homepage shows dog cards, suggesting the API is accessible. Network tab inspection in browser would reveal the endpoint.
