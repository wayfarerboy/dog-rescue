"""Tests for the shared checker registry."""

from __future__ import annotations

from sites.registry import get_checkers


def test_all_checkers_present() -> None:
    """All site checkers should be in the registry."""
    checkers = get_checkers("/tmp/test_data")

    site_names = sorted(c.site_name for c in checkers)

    expected = sorted([
        "All Dogs Matter",
        "Birmingham Dogs Home",
        "Blue Cross Bromsgrove",
        "Blue Cross Burford",
        "Brighter Days Rescue",
        "Cheltenham Animal Shelter",
        "Cotswolds Dogs & Cats Home",
        "Dogs Trust",
        "Forest Dog Rescue",
        "German Shepherd Rescue",
        "Jerry Green Dog Rescue",
        "Many Tears Rescue",
        "Paws2Rescue",
        "Pro Dogs Direct",
        "Raystede",
        "RSPCA Brighton",
        "RSPCA Leeds & Wakefield",
        "Second Chance Spaniel Rescue",
        "South East Dog Rescue",
        "Spaniel Aid",
        "Starfish Dog Rescue",
        "Teckels Animal Sanctuaries",
        "Wythall Animal Sanctuary",
    ])

    assert len(checkers) >= 22, f"Expected at least 23 checkers, got {len(checkers)}"
    missing = set(expected) ^ set(site_names)
    assert site_names == expected, f"Missing or unexpected checkers: {missing}"
