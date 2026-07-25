# Dog Rescue — Domain Glossary

## Core concepts

- **Checker** — A Python class that scrapes one rescue website. Fetches listing page(s), optionally visits detail pages, produces `Dog` objects.
- **Listing page** — A rescue site's main dog listing. May span multiple pages. Shows cards with partial dog data.
- **Detail page** — An individual dog's profile page. Contains full data (breed, age, gender, location, photo).
- **Dog** — One adoptable dog entry. Eight fields: `status`, `name`, `age`, `gender`, `breed`, `location`, `photo_url`, `url`.
- **Cache** — A pipe-separated text file (`data/<checker>.txt`) storing every dog the checker has seen. One line per dog, 8 pipe-separated fields. Overwritten each run with current results.
- **Diff** — Comparing the current scrape against the cache. URLs in current but not in cache → new dogs → email notification.
- **Status flip** — When a dog goes available→reserved→available. Because the cache is overwritten each run and reserved dogs are filtered out of `parse()`, a flipped dog reappears in `parse()` as "new" and triggers notification.
- **Reserved filter** — A checker must exclude dogs that are reserved / home-found / applications-closed from its `parse()` output. This ensures they drop from cache so a status flip is detected.
- **Center distance** — Google Maps driving distance from home (224 Bath Road, Worcester WR5 3ER) to a rescue center. Cached in a lookup table so the API is only called once per center.
- **Too-far list** — Centers beyond the maximum acceptable driving distance. Kept so future rescue research doesn't re-evaluate them.

## Decisions

See `docs/adr/` for architectural decisions.
