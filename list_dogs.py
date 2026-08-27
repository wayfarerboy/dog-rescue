#!/usr/bin/env python3
"""List all available dogs across rescue sites.

Usage:
  python3 list_dogs.py              # Live fetch all sites
  python3 list_dogs.py --cached     # Read from data/*.txt cache files
  python3 list_dogs.py --html       # Live fetch -> dogs.html
  python3 list_dogs.py --ignore <url>    # Mark a dog as ignored
  python3 list_dogs.py --un-ignore <url> # Un-mark a dog
  python3 list_dogs.py --hide-ignored   # Only show unseen dogs
"""

from __future__ import annotations

import sys
from pathlib import Path

from breed_exclusion import BreedExclusionList, filter_dogs_by_breed
from filters import filter_dogs_by_age, filter_dogs_by_gender
from ignore import IgnoredList
from sites.base import Dog, _esc, _photo_tag
from sites.registry import get_active_checkers

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"

# Inline JS: when the HTML is served over HTTP (see serve.py) it fetches the
# live ignored set and wires up the per-card Ignore/Un-ignore buttons so
# a click persists to data/ignored.txt. Opened as a plain file (file://) it
# degrades to the static markers baked in at generation time.
_HTML_JS = """<script>
(function () {
  var KEY = 'dogRescue.hideIgnored';
  var cards = function () {
    return Array.prototype.slice.call(document.querySelectorAll('[data-dog-url]'));
  };
  function isIgnored(set, c) { return set.has(c.getAttribute('data-dog-url')); }
  function applyState(card, ignored) {
    card.style.opacity = ignored ? '0.45' : '1';
    var nameEl = card.querySelector('.dog-name');
    if (nameEl) nameEl.style.textDecoration = ignored ? 'line-through' : 'none';
    var badge = card.querySelector('.dog-badge');
    if (ignored && !badge) {
      badge = document.createElement('span');
      badge.className = 'dog-badge';
      badge.textContent = 'ignored';
      badge.style.cssText = 'font-size:11px;font-weight:700;color:#fff;' +
        'background:#9a9a9a;border-radius:4px;padding:2px 8px;margin-left:8px;' +
        'vertical-align:middle';
      var n = card.querySelector('.dog-name');
      if (n) n.appendChild(badge);
    } else if (!ignored && badge) {
      badge.parentNode.removeChild(badge);
    }
    var btn = card.querySelector('.disc-btn');
    if (btn) {
      btn.textContent = ignored ? 'Un-ignore' : 'Ignore';
      btn.style.background = ignored ? '#9a9a9a' : '#e8e8e8';
      btn.style.color = ignored ? '#fff' : '#555';
    }
  }
  function hideIgnored() {
    var cb = document.getElementById('hideIgnored');
    return !!cb && cb.checked;
  }
  function applyVisibility(set) {
    var hide = hideIgnored();
    cards().forEach(function (c) {
      c.style.display = (hide && isIgnored(set, c)) ? 'none' : 'flex';
    });
  }
  function renderCounts(set) {
    var vis = cards().filter(function (c) { return c.style.display !== 'none'; });
    var total = vis.length;
    var ignored = vis.filter(function (c) { return isIgnored(set, c); }).length;
    var p = document.getElementById('summary');
    if (!p) return;
    var base = p.getAttribute('data-base');
    if (hideIgnored()) {
      p.textContent = base + ' \u00b7 ' + total + ' available (ignored hidden)';
    } else {
      p.textContent = base + ' \u00b7 ' + (total - ignored) + ' new / ' + ignored + ' ignored';
    }
  }
  function refresh(set) {
    cards().forEach(function (c) { applyState(c, isIgnored(set, c)); });
    applyVisibility(set);
    renderCounts(set);
  }
  function loadSet() {
    return fetch('/api/ignored').then(function (r) { return r.json(); })
      .then(function (d) { return new Set((d.urls || [])); });
  }
  function toggle(url) {
    fetch('/api/ignored/toggle?url=' + encodeURIComponent(url), { method: 'POST' })
      .then(function () { return loadSet(); })
      .then(function (set) { refresh(set); });
  }
  loadSet().then(function (set) {
    // Restore the persisted choice BEFORE computing visibility, so first-load
    // refresh() sees the checkbox state and hides ignored cards immediately.
    var cb = document.getElementById('hideIgnored');
    if (cb) cb.checked = localStorage.getItem(KEY) === '1';
    refresh(set);
    cards().forEach(function (c) {
      var url = c.getAttribute('data-dog-url');
      var btn = c.querySelector('.disc-btn');
      if (btn) btn.onclick = function () { toggle(url); };
    });
    if (cb) {
      cb.onchange = function () {
        localStorage.setItem(KEY, cb.checked ? '1' : '0');
        refresh(set);
      };
    }
  }).catch(function () {
    // Not served over HTTP (opened as a file) — keep static markers, disable toggles.
    cards().forEach(function (c) {
      var btn = c.querySelector('.disc-btn');
      if (btn) { btn.disabled = true; btn.textContent = 'ignore (use ./dogs)'; }
    });
    var cb = document.getElementById('hideIgnored');
    if (cb) cb.disabled = true;
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


def _empty_page() -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>"
        "<meta charset=\"utf-8\">\n"
        "<title>Available Dogs</title>\n</head>\n"
        "<body style=\"margin:20px;font-family:-apple-system,"
        "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif\">\n"
        "<p>No dogs found.</p>\n</body>\n</html>"
    )


def _is_showable(d: Dog, ignored: IgnoredList | None) -> bool:
    """Whether a dog counts as "to show" (i.e. it isn't ignored)."""
    return not (ignored and d.url in ignored)


def format_html(
    results: list[tuple[str, list[Dog]]],
    ignored: IgnoredList | None = None,
) -> str:
    """Format dogs as a self-contained HTML document with card layout.

    Ignored dogs are dimmed, struck through, and labelled.
    Rescue centres with no dog to show are omitted entirely (an ignored dog
    does not count as "to show").
    """
    if not results:
        return _empty_page()

    # Drop rescue centres whose dogs are all ignored (nothing to show).
    results = [
        (site, dogs)
        for site, dogs in results
        if any(_is_showable(d, ignored) for d in dogs)
    ]
    if not results:
        return _empty_page()

    sections: list[str] = []
    for site_name, dogs in results:
        cards: list[str] = []
        for d in dogs:
            is_ignored = bool(ignored and d.url in ignored)
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
                if is_ignored
                else 'background:#fff;border:1px solid #e0e0e0;'
                'border-radius:10px;overflow:hidden;display:flex;'
                'margin-bottom:14px;transition:box-shadow .15s'
            )
            name_style = (
                'font-size:16px;font-weight:700;color:#222;'
                'margin-bottom:2px;text-decoration:line-through'
                if is_ignored
                else 'font-size:16px;font-weight:700;color:#222;margin-bottom:2px'
            )
            badge = (
                '<span class="dog-badge" style="font-size:11px;font-weight:700;'
                'color:#fff;background:#9a9a9a;border-radius:4px;padding:2px 8px;'
                'margin-left:8px;vertical-align:middle">ignored</span>'
                if is_ignored
                else ''
            )
            escaped_url = _esc(d.url)
            btn_label = "Un-ignore" if is_ignored else "Ignore"

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
    ignored_count = 0
    if ignored:
        ignored_count = sum(
            1 for _, dogs in results for d in dogs if d.url in ignored
        )
    new_count = total - ignored_count
    summary_base = (
        f"Female · under 1 year · breed-filtered · {len(results)} rescues"
    )
    summary = f"{summary_base} · {new_count} new / {ignored_count} ignored"

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
        f'style="font-size:13px;color:#888;margin:0 0 8px 0">'
        f'{_esc(summary)}</p>\n'
        f'<label style="font-size:12px;color:#666;display:block;'
        f'margin-bottom:24px">'
        f'<input type="checkbox" id="hideIgnored" '
        f'style="margin-right:6px"> Hide ignored</label>\n'
        + "\n".join(sections)
        + "\n</div>\n"
        + _HTML_JS
        + "\n</body>\n</html>"
    )


def format_table(
    results: list[tuple[str, list[Dog]]],
    ignored: IgnoredList | None = None,
) -> str:
    """Format dogs as a pipe-delimited table string.

    Ignored dogs are prefixed with "[I]". Rescue centres with no dog to
    show (all their dogs ignored) are omitted.
    """
    if not results:
        return "No dogs found."

    # Drop rescue centres whose dogs are all ignored (nothing to show).
    results = [
        (site, dogs)
        for site, dogs in results
        if any(_is_showable(d, ignored) for d in dogs)
    ]
    if not results:
        return "No dogs found."

    lines: list[str] = []
    header = "status | name | age | gender | breed | location | url"
    lines.append(header)
    lines.append("-" * len(header))

    for _site_name, dogs in results:
        for d in dogs:
            mark = "  [I]" if (ignored and d.url in ignored) else ""
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
    hide_ignored = "--hide-ignored" in args

    ignored = IgnoredList(str(DATA_DIR))

    # Fast path: just mark/unmark a dog without listing.
    if "--ignore" in args:
        idx = args.index("--ignore")
        if idx + 1 < len(args):
            ignored.add(args[idx + 1])
            print(f"Ignored: {args[idx + 1]}")
        return
    if "--un-ignore" in args:
        idx = args.index("--un-ignore")
        if idx + 1 < len(args):
            ignored.remove(args[idx + 1])
            print(f"Removed from ignored: {args[idx + 1]}")
        return

    results = list_cached(str(DATA_DIR)) if cached else list_live(str(DATA_DIR))

    if hide_ignored:
        results = [
            (site_name, [d for d in dogs if d.url not in ignored])
            for site_name, dogs in results
        ]
        results = [(s, ds) for s, ds in results if ds]

    if html:
        output = format_html(results, ignored=ignored)
        Path("dogs.html").write_text(output)
        total = sum(len(dogs) for _, dogs in results)
        print(f"Wrote {total} dogs to dogs.html")
    else:
        print(format_table(results, ignored=ignored))


if __name__ == "__main__":
    main()
