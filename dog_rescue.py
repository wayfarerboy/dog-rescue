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

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"

_HTML_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:16px;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden">
<div style="padding:16px">
<h1 style="font-size:18px;font-weight:700;color:#222;margin:0 0 16px 0">{subject}</h1>
{content}
</div>
<div style="padding:12px 16px;border-top:1px solid #f0f0f0;font-size:11px;color:#aaa">
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


def main() -> None:
    env = load_env()
    email = env.get("EMAIL", "")
    subject = env.get("SUBJECT", "New dogs available for adoption")

    if not email:
        print("Error: EMAIL not set in .env", file=sys.stderr)
        sys.exit(1)

    # Import site checkers
    from sites.base import Dog
    from sites.dogs_trust import DogsTrustChecker
    from sites.jerry_green import JerryGreenChecker
    from sites.many_tears import ManyTearsChecker
    from sites.scsr import SCSRChecker
    from sites.south_east_dog_rescue import SouthEastDogRescueChecker

    checkers = [
        ManyTearsChecker(str(DATA_DIR)),
        SCSRChecker(str(DATA_DIR)),
        DogsTrustChecker(str(DATA_DIR)),
        JerryGreenChecker(str(DATA_DIR)),
        SouthEastDogRescueChecker(str(DATA_DIR)),
    ]

    text_sections: list[str] = []
    html_sites: list[tuple[str, list[Dog]]] = []

    for checker in checkers:
        try:
            print(f"Checking {checker.site_name}...", file=sys.stderr)
            new_dogs = checker.check()
            print(f"  Found {len(new_dogs)} new dog(s)", file=sys.stderr)

            if new_dogs:
                section = checker.format_section(
                    new_dogs,
                    checker.site_name,
                    "Status | Name | Age | Gender | Breed | Location | Link",
                )
                if section:
                    text_sections.append(section)
                html_sites.append((checker.site_name, new_dogs))
        except Exception as exc:
            print(f"  Error checking {checker.site_name}: {exc}", file=sys.stderr)

    if not text_sections:
        print("No new dogs since last check.")
        return

    print(f"New entries detected! Sending email to {email}...")

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
    main()
