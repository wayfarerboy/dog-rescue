#!/usr/bin/env python3
"""List all available dogs across rescue sites.

Usage:
  python3 list_dogs.py              # Live fetch all sites
  python3 list_dogs.py --cached     # Read from data/*.txt cache files
  python3 list_dogs.py --html       # Live fetch -> dogs.html
  python3 list_dogs.py --discard <url>    # Mark a dog as discounted
  python3 list_dogs.py --un-discard <url> # Un-mark a dog
  python3 list_dogs.py --hide-discarded   # Only show unseen dogs
"""

from __future__ import annotations

import sys
from pathlib import Path

from breed_exclusion import BreedExclusionList, filter_dogs_by_breed
from discount import DiscountedList
from filters import filter_dogs_by_age, filter_dogs_by_gender
from sites.base import Dog, _esc, _photo_tag
from sites.registry import get_active_checkers

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"

# Inline JS: when the HTML is served over HTTP (see serve.py) it fetches the
# live discounted set and wires up the per-card Discount/Un-discount buttons so
# a click persists to data/discounted.txt. Opened as a plain file (file://) it
# degrades to the static markers baked in at generation time.
_HTML_JS = """<script>
(function () {
  var cards = function () {
    return Array.prototype.slice.call(document.querySelectorAll('[data-dog-url]'));
  };
  function applyState(card, discounted) {
    card.style.opacity = discounted ? '0.45' : '1';
    var nameEl = card.querySelector('.dog-name');
    if (nameEl) nameEl.style.textDecoration = discounted ? 'line-through' : 'none';
    var badge = card.querySelector('.dog-badge');
    if (discounted && !badge) {
      badge = document.createElement('span');
      badge.className = 'dog-badge';
      badge.textContent = 'discounted';
      badge.style.cssText = 'font-size:11px;font-weight:700;color:#fff;' +
        'background:#9a9a9a;border-radius:4px;padding:2px 8px;margin-left:8px;' +
        'vertical-align:middle';
      var n = card.querySelector('.dog-name');
      if (n) n.appendChild(badge);
    } else if (!discounted && badge) {
      badge.parentNode.removeChild(badge);
    }
    var btn = card.querySelector('.disc-btn');
    if (btn) {
      btn.textContent = discounted ? 'Un-discount' : 'Discount';
      btn.style.background = discounted ? '#9a9a9a' : '#e8e8e8';
      btn.style.color = discounted ? '#fff' : '#555';
    }
  }
  function renderCounts(set) {
    var total = cards().length;
    var discarded = cards().filter(function (c) {
      return set.has(c.getAttribute('data-dog-url'));
    }).length;
    var p = document.getElementById('summary');
    if (p) p.textContent = p.getAttribute('data-base') + ' \u00b7 ' +
      (total - discarded) + ' new / ' + discarded + ' discounted';
  }
  function loadSet() {
    return fetch('/api/discounted').then(function (r) { return r.json(); })
      .then(function (d) { return new Set((d.urls || [])); });
  }
  function toggle(url) {
    fetch('/api/discounted/toggle?url=' + encodeURIComponent(url), { method: 'POST' })
      .then(function () { return loadSet(); })
      .then(function (set) {
        cards().forEach(function (c) { applyState(c, set.has(c.getAttribute('data-dog-url'))); });
        renderCounts(set);
      });
  }
  loadSet().then(function (set) {
    cards().forEach(function (c) {
      var url = c.getAttribute('data-dog-url');
      applyState(c, set.has(url));
      var btn = c.querySelector('.disc-btn');
      if (btn) btn.onclick = function () { toggle(url); };
    });
    renderCounts(set);
  }).catch(function () {
    // Not served over HTTP (opened as a file) — keep static markers, disable toggles.
    cards().forEach(function (c) {
      var btn = c.querySelector('.disc-btn');
      if (btn) { btn.disabled = true; btn.textContent = 'discount (use ./dogs)'; }
    });
  });
})();
</script>"""


def dog_from_line(line: str) -> Dog:
    """Parse a pipe-delimited cache line into a Dog object."""
    parts = line.split(" | ")
    # Pad short lines so we always have at least 8 fields
    while len(parts) < 8:
        parts.append("")
    return Dog(
        status=parts[0],
        name=parts[1],
        age=parts[2],
        gender=parts[3],
        breed=parts[4],
        location=parts[5],
        photo_url=parts[6],
        url=parts[7],
    )


def format_html(
    results: list[tuple[str, list[Dog]]],
    discounted: DiscountedList | None = None,
) -> str:
    """Format dogs as a self-contained HTML document with card layout.

    Discounted dogs are dimmed, struck through, and labelled.
    """
    if not results:
        return (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>"
            "<meta charset=\"utf-8\">\n"
            "<title>Available Dogs</title>\n</head>\n"
            "<body style=\"margin:20px;font-family:-apple-system,"
            "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif\">\n"
            "<p>No dogs found.</p>\n</body>\n</html>"
        )

    sections: list[str] = []
    for site_name, dogs in results:
        cards: list[str] = []
        for d in dogs:
            is_discarded = bool(discounted and d.url in discounted)
            name = _esc(d.name)
            age = _esc(d.age)
            gender = _esc(d.gender)
            breed = _esc(d.breed)
            location = _esc(d.location)
            url = _esc(d.url)
            photo_html = _photo_tag(d.photo_url)

            card_style = (
                'background:#fff;border:1px solid #e0e0e0;border-radius:10px;'
                'overflow:hidden;display:flex;margin-bottom:14px;'
                'transition:box-shadow .15s;opacity:0.45'
                if is_discarded
                else 'background:#fff;border:1px solid #e0e0e0;'
                'border-radius:10px;overflow:hidden;display:flex;'
                'margin-bottom:14px;transition:box-shadow .15s'
            )
            name_style = (
                'font-size:16px;font-weight:700;color:#222;'
                'margin-bottom:2px;text-decoration:line-through'
                if is_discarded
                else 'font-size:16px;font-weight:700;color:#222;margin-bottom:2px'
            )
            badge = (
                '<span class="dog-badge" style="font-size:11px;font-weight:700;'
                'color:#fff;background:#9a9a9a;border-radius:4px;padding:2px 8px;'
                'margin-left:8px;vertical-align:middle">discounted</span>'
                if is_discarded
                else ''
            )
            escaped_url = _esc(d.url)
            btn_label = "Un-discount" if is_discarded else "Discount"

            cards.append(
                f'<div data-dog-url="{escaped_url}" style="{card_style}" '
                'onmouseover="this.style.boxShadow=\'0 2px 12px rgba(0,0,0,0.08)\'" '
                'onmouseout="this.style.boxShadow=\'none\'">'
                f'<div style="width:100px;min-height:100px;background:#f0ede8;'
                f'flex-shrink:0;display:flex;align-items:center;'
                f'justify-content:center;font-size:40px">{photo_html}</div>'
                '<div style="padding:14px 16px;flex:1;min-width:0">'
                f'<div class="dog-name" style="{name_style}">{name}{badge}</div>'
                f'<div style="font-size:13px;color:#555;margin-bottom:1px">'
                f'{breed or "&mdash;"}</div>'
                f'<div style="font-size:12px;color:#888;margin-bottom:6px">'
                f'{gender or "&mdash;"} &middot; {age or "&mdash;"}</div>'
                f'<div style="font-size:11px;color:#aaa;margin-bottom:10px;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" '
                f'title="{location}">📍 {location or "&mdash;"}</div>'
                f'<a href="{url}" style="font-size:12px;font-weight:600;'
                f'color:#1a73e8;text-decoration:none;'
                f'border:1px solid #1a73e8;border-radius:4px;'
                f'padding:5px 12px;display:inline-block" target="_blank">'
                f'View profile →</a>'
                f'<button type="button" class="disc-btn" style="font-size:12px;'
                f'font-weight:600;background:#e8e8e8;color:#555;border:none;'
                f'border-radius:4px;padding:5px 12px;margin-left:8px;'
                f'cursor:pointer">{btn_label}</button>'
                '</div></div>'
            )

        count = len(dogs)
        label = "1 dog" if count == 1 else f"{count} dogs"

        sections.append(
            '<div style="margin-bottom:24px">'
            f'<h2 style="font-size:17px;font-weight:700;color:#222;'
            f'margin:0 0 2px 0">{_esc(site_name)}</h2>'
            f'<p style="font-size:12px;color:#aaa;margin:0 0 12px 0">'
            f'{label}</p>'
            + "".join(cards)
            + "</div>"
        )

    total = sum(len(dogs) for _, dogs in results)
    total_label = "1 dog" if total == 1 else f"{total} dogs"
    discarded_count = 0
    if discounted:
        discarded_count = sum(
            1 for _, dogs in results for d in dogs if d.url in discounted
        )
    new_count = total - discarded_count
    summary_base = (
        f"Female · under 1 year · breed-filtered · {len(results)} rescues"
    )
    summary = f"{summary_base} · {new_count} new / {discarded_count} discounted"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>Available Dogs</title>\n"
        "</head>\n"
        '<body style="margin:0;padding:24px;font-family:-apple-system,'
        "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
        'background:#f5f5f5">\n'
        '<div style="max-width:520px;margin:0 auto">\n'
        f'<h1 style="font-size:24px;font-weight:700;color:#222;'
        f'margin:0 0 4px 0">🐾 {total_label} available</h1>\n'
        f'<p id="summary" data-base="{_esc(summary_base)}" '
        f'style="font-size:13px;color:#888;margin:0 0 24px 0">'
        f'{_esc(summary)}</p>\n'
        + "\n".join(sections)
        + "\n</div>\n"
        + _HTML_JS
        + "\n</body>\n</html>"
    )


def format_table(
    results: list[tuple[str, list[Dog]]],
    discounted: DiscountedList | None = None,
) -> str:
    """Format dogs as a pipe-delimited table string.

    Discounted dogs are prefixed with "[D]".
    """
    if not results:
        return "No dogs found."

    lines: list[str] = []
    header = "status | name | age | gender | breed | location | url"
    lines.append(header)
    lines.append("-" * len(header))

    for _site_name, dogs in results:
        for d in dogs:
            mark = "  [D]" if (discounted and d.url in discounted) else ""
            lines.append(
                f"{d.status} | {d.name} | {d.age} | {d.gender} | "
                f"{d.breed} | {d.location} | {d.url}{mark}"
            )

    return "\n".join(lines)


def _join_broken_lines(lines: list[str]) -> list[str]:
    """Rejoin cache lines that were split by embedded newlines in fields.

    A valid cache line has 8 pipe-separated fields. If a line has fewer,
    it's a continuation of the previous line's last field. Merge them.
    """
    result: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if result and line.count("|") < 3:
            # Likely a continuation — append to previous line
            result[-1] = result[-1] + " " + line
        else:
            result.append(line)
    return result


def list_cached(data_dir: str) -> list[tuple[str, list[Dog]]]:
    """Read dogs from cache files. Does not modify any files."""
    breed_exclusion = BreedExclusionList(data_dir)
    results: list[tuple[str, list[Dog]]] = []
    for checker in get_active_checkers(data_dir):
        data_path = Path(data_dir) / checker.data_file
        if not data_path.exists():
            continue
        raw_lines = data_path.read_text().strip().splitlines()
        lines = _join_broken_lines(raw_lines)
        dogs = [
            dog_from_line(line)
            for line in lines
            if line.strip()
        ]
        if dogs:
            dogs = filter_dogs_by_breed(dogs, breed_exclusion)
            dogs = filter_dogs_by_gender(dogs, keep="Female")
            dogs = filter_dogs_by_age(dogs, max_months=11)
        if dogs:
            results.append((checker.site_name, dogs))
    return results


def list_live(data_dir: str) -> list[tuple[str, list[Dog]]]:
    """Fetch and parse all sites live. Does not modify cache files."""
    breed_exclusion = BreedExclusionList(data_dir)
    results: list[tuple[str, list[Dog]]] = []
    for checker in get_active_checkers(data_dir):
        try:
            raw = checker.fetch()
            dogs = checker.parse(raw)
            if dogs:
                dogs = filter_dogs_by_breed(dogs, breed_exclusion)
                dogs = filter_dogs_by_gender(dogs, keep="Female")
                dogs = filter_dogs_by_age(dogs, max_months=11)
            if dogs:
                results.append((checker.site_name, dogs))
        except Exception as exc:
            print(f"Error checking {checker.site_name}: {exc}", file=sys.stderr)
    return results


def main() -> None:
    args = sys.argv[1:]
    cached = "--cached" in args
    html = "--html" in args
    hide_discarded = "--hide-discarded" in args

    discounted = DiscountedList(str(DATA_DIR))

    # Fast path: just mark/unmark a dog without listing.
    if "--discard" in args:
        idx = args.index("--discard")
        if idx + 1 < len(args):
            discounted.add(args[idx + 1])
            print(f"Discounted: {args[idx + 1]}")
        return
    if "--un-discard" in args:
        idx = args.index("--un-discard")
        if idx + 1 < len(args):
            discounted.remove(args[idx + 1])
            print(f"Removed from discounted: {args[idx + 1]}")
        return

    results = list_cached(str(DATA_DIR)) if cached else list_live(str(DATA_DIR))

    if hide_discarded:
        results = [
            (site_name, [d for d in dogs if d.url not in discounted])
            for site_name, dogs in results
        ]
        results = [(s, ds) for s, ds in results if ds]

    if html:
        output = format_html(results, discounted=discounted)
        Path("dogs.html").write_text(output)
        total = sum(len(dogs) for _, dogs in results)
        print(f"Wrote {total} dogs to dogs.html")
    else:
        print(format_table(results, discounted=discounted))


if __name__ == "__main__":
    main()
