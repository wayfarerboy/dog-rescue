#!/usr/bin/env python3.14
"""Dog Rescue — check multiple adoption sites for new dogs matching criteria
(female, under 1 year old) and email notifications.

Usage:  python3 dog_rescue.py
Cron:   0 8 * * * cd /path/to/dog-rescue && python3 dog_rescue.py
"""

from __future__ import annotations

import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from breed_exclusion import BreedExclusionList, filter_dogs_by_breed
from filters import filter_dogs_by_age, filter_dogs_by_gender
from distance_lookup import (
    MAX_DISTANCE_MILES_DEFAULT,
    DistanceLookup,
    evaluate_rescue_centers,
    filter_dogs_by_distance,
)
from too_far import TooFarList

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"

_HTML_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:24px;background:#f5f5f5;
      font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<div style="max-width:520px;margin:0 auto">
<h1 style="font-size:22px;font-weight:700;color:#222;margin:0 0 4px 0">{subject}</h1>
<p style="font-size:13px;color:#888;margin:0 0 24px 0">
Female &middot; under 1 year &middot; breed-filtered</p>
{content}
<div style="padding:16px 0 0 0;border-top:1px solid #e0e0e0;font-size:11px;color:#aaa;margin-top:8px">
Dog Rescue &mdash; automated notification
</div>
</div>
</body>
</html>"""


def load_env() -> dict[str, str]:
    """Load .env file into a dict. Simple parser, no dependencies."""
    env: dict[str, str] = {}
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def main(dry_run: bool = False) -> None:
    env = load_env()
    email = env.get("EMAIL", "")
    subject = env.get("SUBJECT", "New dogs available for adoption")

    if not email:
        print("Error: EMAIL not set in .env", file=sys.stderr)
        sys.exit(1)

    # Distance filtering setup
    api_key = env.get("GOOGLE_MAPS_API_KEY", "")
    max_distance_str = env.get("MAX_DISTANCE_MILES", "")
    max_distance: float | None = None
    if max_distance_str:
        try:
            max_distance = float(max_distance_str)
        except ValueError:
            max_distance = MAX_DISTANCE_MILES_DEFAULT
    distance_lookup = DistanceLookup(str(DATA_DIR), api_key=api_key)
    breed_exclusion = BreedExclusionList(str(DATA_DIR))

    # Import site checkers from shared registry
    from sites.base import Dog
    from sites.registry import get_active_checkers

    too_far = TooFarList(str(DATA_DIR))

    # Evaluate single-location rescues that are too far
    if max_distance is not None:
        newly_excluded = evaluate_rescue_centers(
            str(DATA_DIR), distance_lookup, max_distance, too_far
        )
        for site_name, location, distance in newly_excluded:
            print(
                f"Added '{site_name}' to too-far list "
                f"(single location '{location}' at {distance:.1f} mi > {max_distance} mi)",
                file=sys.stderr,
            )

    # Only check active (non-too-far) rescues
    checkers = get_active_checkers(str(DATA_DIR))

    text_sections: list[str] = []
    html_sites: list[tuple[str, list[Dog]]] = []

    total_listed = 0
    total_matched = 0

    for checker in checkers:
        try:
            previous_urls = checker._load_previous()
            cached_before = checker.cached_count
            new_dogs = checker.check()
            listed = checker.cached_count

            total_listed += listed

            # Build the status line piece by piece
            parts: list[str] = []
            unfiltered_new = len(new_dogs)

            if new_dogs and max_distance is not None:
                if not getattr(checker, "bypass_distance_filter", False):
                    before = len(new_dogs)
                    new_dogs = filter_dogs_by_distance(new_dogs, distance_lookup, max_distance)
                    removed = before - len(new_dogs)
                    if removed:
                        parts.append(f"—{removed} far")

            if new_dogs:
                before = len(new_dogs)
                new_dogs = filter_dogs_by_gender(new_dogs, keep="Female")
                removed = before - len(new_dogs)
                if removed:
                    parts.append(f"—{removed} gender")

            if new_dogs:
                before = len(new_dogs)
                new_dogs = filter_dogs_by_age(new_dogs, max_months=12)
                removed = before - len(new_dogs)
                if removed:
                    parts.append(f"—{removed} age")

            if new_dogs:
                before = len(new_dogs)
                new_dogs = filter_dogs_by_breed(new_dogs, breed_exclusion)
                removed = before - len(new_dogs)
                if removed:
                    parts.append(f"—{removed} breed")

            matched = len(new_dogs)
            matched_cached = sum(1 for d in new_dogs if d.url in previous_urls)
            matched_new = matched - matched_cached

            total_matched += matched

            filters = " ".join(parts)
            if filters:
                filters = " " + filters

            if matched:
                print(f"{checker.site_name}: {listed} listed{filters} → {matched} matched "
                      f"({matched_cached} cached, {matched_new} new)", file=sys.stderr)
                section = checker.format_section(
                    new_dogs,
                    checker.site_name,
                    "Status | Name | Age | Gender | Breed | Location | Link",
                )
                if section:
                    text_sections.append(section)
                html_sites.append((checker.site_name, new_dogs))
            elif unfiltered_new:
                print(f"{checker.site_name}: {listed} listed{filters} → 0 matched",
                      file=sys.stderr)
            else:
                print(f"{checker.site_name}: {listed} listed → 0 new", file=sys.stderr)

        except Exception as exc:
            print(f"{checker.site_name}: ✗ Error: {exc}", file=sys.stderr)

    if not text_sections:
        print(f"\n{total_listed} listed across {len(checkers)} rescues, "
              f"{total_matched} matched criteria — none new.",
              file=sys.stderr)
        return

    print(f"\n{total_matched} dog(s) matched — sending email to {email}...")

    # Plain-text body
    text_body = (
        "New dogs available for adoption:\n"
        "------------------------------------------------------\n\n"
        + "\n".join(text_sections)
    )

    # HTML body (format_section_html is on the base class; any checker
    # instance works since it only uses site_name + Dog data)
    html_parts: list[str] = []
    for site_name, dogs in html_sites:
        html_parts.append(checkers[0].format_section_html(dogs, site_name))
    html_body = _HTML_WRAPPER.format(
        subject=subject,
        content="\n".join(html_parts),
    )

    # Multipart message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["To"] = email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    if dry_run:
        print("\n── DRY RUN ──")
        print(f"To: {email}")
        print(f"Subject: {subject}")
        print(f"\n{msg.as_string()}")
        print(f"\nTotal dogs: {sum(len(dogs) for _, dogs in html_sites)}")
        return

    try:
        subprocess.run(
            ["msmtp", "-t"],
            input=msg.as_string(),
            text=True,
            check=True,
            timeout=30,
        )
        print("Email sent.")
    except FileNotFoundError:
        print("Error: msmtp not found. Install with: brew install msmtp", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Error sending email: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
