#!/usr/bin/env python3
"""Dog Rescue — interactive CLI menu.

Makes all repo tools accessible from one command-line interface.
Run with:  python3 cli.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import termios
import threading
import time
import tty
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python3"
CACHE_SUFFIX = ".txt"
TOO_FAR_PATH = DATA_DIR / "too-far.txt"
DISTANCES_PATH = DATA_DIR / "distances.json"
EXCLUDED_BREEDS_PATH = DATA_DIR / "excluded-breeds.txt"

# ── helpers ────────────────────────────────────────────────────────────

def _getch() -> str:
    """Read a single character from stdin without requiring Enter."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x03":  # Ctrl-C
            raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _run(script: str, *args: str) -> None:
    """Run a Python script with optional args, showing a spinner while it runs."""
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [python, str(SCRIPT_DIR / script), *args]

    done = threading.Event()

    def _spin():
        i = 0
        while not done.is_set():
            print(f"\r  {_SPINNER[i % len(_SPINNER)]} Running...", end="", flush=True)
            i += 1
            time.sleep(0.08)
        print("\r" + " " * 30 + "\r", end="", flush=True)  # clear spinner line

    spinner = threading.Thread(target=_spin, daemon=True)
    spinner.start()
    try:
        subprocess.run(cmd, check=False)
    finally:
        done.set()
        spinner.join(timeout=0.5)


def _press_any_key() -> None:
    print("\nPress any key to return to menu...", end="", flush=True)
    _getch()
    print()


def _header(title: str) -> None:
    _clear()
    print(f"\n  {title}")
    print(f"  {'=' * len(title)}\n")


def _menu(title: str, options: list[tuple[str, str]], prompt: str = "Choose") -> str | None:
    """Display a menu, return the key of the chosen option (or None to quit).

    Reads a single keypress — no Enter required.
    """
    _header(title)
    for key, desc in options:
        print(f"  [{key}]  {desc}")
    print()
    print(f"  {prompt} (q=quit): ", end="", flush=True)
    choice = _getch()
    print(choice)  # echo the key
    if choice.lower() == "q":
        return None
    return choice.lower()


# ── main menu actions ──────────────────────────────────────────────────

def _daily_check():
    """Fetch all sites, filter by distance, email new dogs."""
    _header("Daily Check + Email")
    print("  Fetching all 13 sites, filtering by distance, and emailing...\n")
    _run("dog_rescue.py")
    _press_any_key()


# ── list dogs ──────────────────────────────────────────────────────────

def _list_dogs_menu():
    while True:
        choice = _menu("List Dogs", [
            ("1", "Live fetch → terminal table"),
            ("2", "Cached data → terminal table"),
            ("3", "Live fetch → HTML file (dogs.html)"),
            ("4", "Cached data → HTML file (dogs.html)"),
            ("5", "Open dogs.html in browser"),
            ("0", "Back to main menu"),
        ])
        if choice is None or choice == "0":
            return
        if choice == "1":
            _header("Live Fetch → Terminal")
            _run("list_dogs.py")
            _press_any_key()
        elif choice == "2":
            _header("Cached → Terminal")
            _run("list_dogs.py", "--cached")
            _press_any_key()
        elif choice == "3":
            _header("Live Fetch → HTML")
            _run("list_dogs.py", "--html")
            _press_any_key()
        elif choice == "4":
            _header("Cached → HTML")
            _run("list_dogs.py", "--html", "--cached")
            _press_any_key()
        elif choice == "5":
            html = SCRIPT_DIR / "dogs.html"
            if html.exists():
                subprocess.run(["open", str(html)], check=False)
            else:
                print("  dogs.html not found. Generate it first (options 3 or 4).")
                _press_any_key()


# ── cache management ───────────────────────────────────────────────────

def _cache_file_menu():
    """Browse individual cache files."""
    while True:
        files = sorted(
            [f for f in DATA_DIR.glob(f"*{CACHE_SUFFIX}")],
            key=lambda p: p.name,
        )
        options = []
        for i, fp in enumerate(files, 1):
            lines = [l for l in fp.read_text().splitlines() if l.strip()]
            options.append((str(i), f"{fp.stem}  ({len(lines)} entries)"))
        options.append(("0", "Back"))

        choice = _menu("View Cache Files", options, prompt="Choose file")
        if choice is None or choice == "0":
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                _header(f"Cache: {files[idx].stem}")
                content = files[idx].read_text()
                if len(content) > 5000:
                    # Truncated view
                    print(content[:5000])
                    print("\n  ... (truncated — file has more entries)")
                else:
                    print(content)
                _press_any_key()
        except (ValueError, IndexError):
            pass


def _cache_menu():
    while True:
        choice = _menu("Cache Management", [
            ("1", "Populate all caches (fresh baseline)"),
            ("2", "Repair cache — all sites"),
            ("3", "Repair cache — specific site"),
            ("4", "Repair cache — dry run (preview only)"),
            ("5", "View cache files"),
            ("0", "Back to main menu"),
        ])
        if choice is None or choice == "0":
            return
        if choice == "1":
            _header("Populate Caches")
            _run("populate_caches.py")
            _press_any_key()
        elif choice == "2":
            _header("Repair Cache — All Sites")
            _run("repair_cache.py")
            _press_any_key()
        elif choice == "3":
            _header("Repair Cache — Specific Site")
            # Show known sites
            _register = {}
            from sites.registry import get_active_checkers
            for checker in get_active_checkers(str(DATA_DIR)):
                _register[checker.data_file] = checker.site_name
            for i, (fname, sname) in enumerate(sorted(_register.items()), 1):
                print(f"  {i:>2}. {sname}  ({fname})")
            print()
            site = input("  Site name (e.g. dogs-trust): ").strip()
            if site:
                _run("repair_cache.py", "--site", site)
            _press_any_key()
        elif choice == "4":
            _header("Repair Cache — Dry Run")
            _run("repair_cache.py", "--dry-run")
            _press_any_key()
        elif choice == "5":
            _cache_file_menu()


# ── distance & location ────────────────────────────────────────────────

def _view_distances():
    _header("Cached Distances")
    if not DISTANCES_PATH.exists():
        print("  No distance data yet. Run a daily check or list_dogs first.\n")
    else:
        data = json.loads(DISTANCES_PATH.read_text())
        if not data:
            print("  No entries.\n")
        else:
            print(f"  {'Centre':<30} {'Miles':>8}")
            print(f"  {'-' * 30} {'-' * 8}")
            for centre, miles in sorted(data.items()):
                m_str = f"{miles:.1f}" if miles is not None else "unknown"
                print(f"  {centre:<30} {m_str:>8}")
            print(f"\n  {len(data)} centre(s) total")
    _press_any_key()


def _view_too_far():
    _header("Too-Far List (excluded rescues)")
    if not TOO_FAR_PATH.exists():
        print("  No entries yet.\n")
    else:
        names = [
            l.strip() for l in TOO_FAR_PATH.read_text().splitlines() if l.strip()
        ]
        if not names:
            print("  No entries.\n")
        else:
            for i, name in enumerate(names, 1):
                print(f"  {i:>2}. {name}")
            print(f"\n  {len(names)} rescue(s) excluded")

    # Option to add/remove
    print()
    action = input("  [a]dd, [r]emove, or [Enter] back: ").strip().lower()
    if action == "a":
        name = input("  Rescue name to add: ").strip()
        if name:
            from too_far import TooFarList
            tfl = TooFarList(str(DATA_DIR))
            tfl.add(name)
            print(f"  Added '{name}' to too-far list.")
            _press_any_key()
    elif action == "r":
        name = input("  Rescue name to remove: ").strip()
        if name and TOO_FAR_PATH.exists():
            lines = [
                l for l in TOO_FAR_PATH.read_text().splitlines() if l.strip()
            ]
            if name in lines:
                lines.remove(name)
                TOO_FAR_PATH.write_text("\n".join(lines) + "\n")
                print(f"  Removed '{name}' from too-far list.")
            else:
                print(f"  '{name}' not found.")
            _press_any_key()
    # else just go back


def _lookup_location():
    _header("Look Up Location Distance")
    print("  Enter a rescue centre name to check its cached distance from Worcester.\n")
    centre = input("  Centre name: ").strip()
    if not centre:
        return

    from distance_lookup import DistanceLookup
    env = _load_env()
    api_key = env.get("GOOGLE_MAPS_API_KEY", "")
    dl = DistanceLookup(str(DATA_DIR), api_key=api_key)
    distance = dl.get_distance(centre)
    if distance is None:
        print(f"\n  No distance found for '{centre}'. (May need a live lookup with API key.)")
    else:
        print(f"\n  '{centre}' → {distance:.1f} miles from Worcester")
    _press_any_key()


def _evaluate_rescue_distances():
    """Evaluate all rescues: single-location centres beyond max distance → too-far."""
    _header("Evaluate Rescue Centre Distances")

    from distance_lookup import DistanceLookup, evaluate_rescue_centers
    from too_far import TooFarList

    env = _load_env()
    api_key = env.get("GOOGLE_MAPS_API_KEY", "")
    max_distance_str = env.get("MAX_DISTANCE_MILES", "")
    max_distance = float(max_distance_str) if max_distance_str else 120.0

    dl = DistanceLookup(str(DATA_DIR), api_key=api_key)
    too_far = TooFarList(str(DATA_DIR))

    print(f"  Max distance: {max_distance:.0f} miles")
    print(f"  Currently excluded: {len(too_far.names())} rescue(s)")
    print()

    excluded = evaluate_rescue_centers(str(DATA_DIR), dl, max_distance, too_far)

    if not excluded:
        print("  No new rescues to exclude.")
    else:
        print(f"  Added {len(excluded)} rescue(s) to too-far list:\n")
        for site_name, location, distance in excluded:
            print(f"    • {site_name}")
            print(f"      Location: {location} ({distance:.1f} mi > {max_distance:.0f} mi)")

    _press_any_key()


def _view_breed_exclusion():
    _header("Breed Exclusion List")
    if not EXCLUDED_BREEDS_PATH.exists():
        print("  No entries yet.\n")
    else:
        breeds = [
            l.strip() for l in EXCLUDED_BREEDS_PATH.read_text().splitlines() if l.strip()
        ]
        if not breeds:
            print("  No entries.\n")
        else:
            for i, breed in enumerate(breeds, 1):
                print(f"  {i:>2}. {breed}")
            print(f"\n  {len(breeds)} breed(s) excluded")

    print()
    action = input("  [a]dd, [r]emove, or [Enter] back: ").strip().lower()
    if action == "a":
        breed = input("  Breed to exclude: ").strip()
        if breed:
            from breed_exclusion import BreedExclusionList
            bel = BreedExclusionList(str(DATA_DIR))
            bel.add(breed)
            print(f"  Added '{breed}' to breed exclusion list.")
            _press_any_key()
    elif action == "r":
        breed = input("  Breed to remove: ").strip()
        if breed and EXCLUDED_BREEDS_PATH.exists():
            from breed_exclusion import BreedExclusionList
            bel = BreedExclusionList(str(DATA_DIR))
            bel.remove(breed)
            print(f"  Removed '{breed}' from breed exclusion list.")
            _press_any_key()


def _distance_menu():
    while True:
        choice = _menu("Distance & Location", [
            ("1", "View cached distances"),
            ("2", "View / manage too-far list"),
            ("3", "Look up a location"),
            ("4", "Evaluate rescue centres (auto-detect too-far)"),
            ("5", "View / manage breed exclusion list"),
            ("6", "Discover new rescues (Places API search)"),
            ("0", "Back to main menu"),
        ])
        if choice is None or choice == "0":
            return
        if choice == "1":
            _view_distances()
        elif choice == "2":
            _view_too_far()
        elif choice == "3":
            _lookup_location()
        elif choice == "4":
            _evaluate_rescue_distances()
        elif choice == "5":
            _view_breed_exclusion()
        elif choice == "6":
            _header("Discover New Rescues")
            _run("discover_rescues.py")
            _press_any_key()


# ── tests & diagnostics ────────────────────────────────────────────────

def _run_tests(site: str = "") -> None:
    """Run pytest, optionally filtered to a specific site."""
    _header("Run Tests" if not site else f"Tests: {site}")
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [python, "-m", "pytest", "-v"]
    if site:
        cmd.extend(["-k", site])
    subprocess.run(cmd, check=False)
    _press_any_key()


def _run_lint() -> None:
    _header("Ruff Lint + Format Check")
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    subprocess.run([python, "-m", "ruff", "check", "."], check=False)
    print()
    subprocess.run([sys.executable, "-m", "ruff", "format", "--check", "."], check=False)
    _press_any_key()



def _run_audit() -> None:
    _header("Audit Cache — Missing Fields")
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    subprocess.run([python, str(SCRIPT_DIR / "audit.py")], check=False)
    _press_any_key()
def _env_info() -> None:
    _header("Environment Info")
    env = _load_env()
    print(f"  Python:      {sys.version}")
    print(f"  Working dir: {SCRIPT_DIR}")
    print(f"  Data dir:    {DATA_DIR}")
    print(f"  Email:       {env.get('EMAIL', '(not set)')}")
    print(f"  API key:     {'✓ set' if env.get('GOOGLE_MAPS_API_KEY') else '✗ not set'}")
    print(f"  Max dist:    {env.get('MAX_DISTANCE_MILES', 'default 120')} mi")
    print()

    # Data file stats
    cache_files = list(DATA_DIR.glob(f"*{CACHE_SUFFIX}"))
    print(f"  Cache files: {len(cache_files)}")
    total_entries = 0
    for fp in cache_files:
        entries = [l for l in fp.read_text().splitlines() if l.strip()]
        total_entries += len(entries)
    print(f"  Total dogs in cache: {total_entries}")

    if DISTANCES_PATH.exists():
        dist = json.loads(DISTANCES_PATH.read_text())
        print(f"  Cached distances: {len(dist)}")
    if TOO_FAR_PATH.exists():
        tf = [l for l in TOO_FAR_PATH.read_text().splitlines() if l.strip()]
        print(f"  Too-far rescues: {len(tf)}")
    _press_any_key()


def _tests_menu():
    while True:
        # Build list of known sites from registry
        from sites.registry import get_active_checkers
        sites = [(c.data_file.replace(".txt", ""), c.site_name) for c in get_active_checkers(str(DATA_DIR))]

        options = [
            ("1", "Run all tests"),
            ("2", "Run linting (ruff check + format)"),
            ("3", "Audit cache (missing fields per site)"),
            ("4", "Environment info"),
        ]
        # Add per-site test options
        for i, (slug, name) in enumerate(sorted(sites), 5):
            options.append((str(i), f"Test: {name}"))

        options.append(("0", "Back to main menu"))

        choice = _menu("Tests & Diagnostics", options)
        if choice is None or choice == "0":
            return
        if choice == "1":
            _run_tests()
        elif choice == "2":
            _run_lint()
        elif choice == "3":
            _run_audit()
        elif choice == "4":
            _env_info()
        else:
            try:
                idx = int(choice) - 5
                if 0 <= idx < len(sites):
                    slug = sorted(sites)[idx][0]
                    _run_tests(slug)
            except (ValueError, IndexError):
                pass


# ── env ────────────────────────────────────────────────────────────────

def _load_env() -> dict[str, str]:
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


# ── main ───────────────────────────────────────────────────────────────

def main() -> None:
    # Make sure we're running from the right directory so relative paths work
    os.chdir(SCRIPT_DIR)

    while True:
        choice = _menu("Dog Rescue CLI", [
            ("1", "Daily Check + Email  (fetch all → filter → email)"),
            ("2", "List Dogs  (terminal table / HTML output)"),
            ("3", "Cache Management  (populate / repair / browse)"),
            ("4", "Distance & Location  (distances, too-far list)"),
            ("5", "Tests & Diagnostics  (pytest, ruff, env)"),
            ("0", "Exit"),
        ])
        if choice is None or choice == "0":
            print("\n  Bye!\n")
            break
        if choice == "1":
            _daily_check()
        elif choice == "2":
            _list_dogs_menu()
        elif choice == "3":
            _cache_menu()
        elif choice == "4":
            _distance_menu()
        elif choice == "5":
            _tests_menu()


if __name__ == "__main__":
    main()
