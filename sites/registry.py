"""Shared registry of site checkers.

Import this module to get the canonical list of configured checker instances.
Both the cron script and future scripts use get_checkers() instead of
hardcoding the list in each entrypoint.

Use get_active_checkers() to exclude rescues in the too-far list.
"""

from __future__ import annotations

from pathlib import Path

from sites.all_dogs_matter import AllDogsMatterChecker
from sites.base import SiteChecker
from sites.birch_hill import BirchHillChecker
from sites.blue_cross import BlueCrossChecker
from sites.brighter_days import BrighterDaysChecker
from sites.cheltenham import CheltenhamChecker
from sites.cotswolds import CotswoldsChecker
from sites.dogs_trust import DogsTrustChecker
from sites.forest_dog_rescue import ForestDogRescueChecker
from sites.gsdr import GsdrChecker
from sites.jerry_green import JerryGreenChecker
from sites.many_tears import ManyTearsChecker
from sites.paws2rescue import Paws2RescueChecker
from sites.pro_dogs_direct import ProDogsDirectChecker
from sites.raystede import RaystedeChecker
from sites.rspca_brighton import RSPCABrightonChecker
from sites.rspca_leeds import RSPCALeedsChecker
from sites.scsr import SCSRChecker
from sites.south_east_dog_rescue import SouthEastDogRescueChecker
from sites.spaniel_aid import SpanielAidChecker
from sites.starfish import StarfishChecker
from sites.teckels import TeckelsChecker
from sites.wythall import WythallChecker


def _load_max_distance(data_dir: str) -> float | None:
    """Read MAX_DISTANCE_MILES from .env in the project root."""
    env_path = Path(data_dir).parent / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("MAX_DISTANCE_MILES="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            try:
                return float(value)
            except ValueError:
                return None
    return None


def get_checkers(data_dir: str) -> list[SiteChecker]:
    """Return the canonical list of configured checker instances.

    Args:
        data_dir: Path to the data directory for cache files.
    """
    max_dist = _load_max_distance(data_dir)
    return [
        AllDogsMatterChecker(data_dir),
        # BirchHillChecker(data_dir),  # Cloudflare blocks automated access
        BrighterDaysChecker(data_dir),
        CheltenhamChecker(data_dir),
        CotswoldsChecker(data_dir),
        DogsTrustChecker(data_dir, max_distance_miles=max_dist),
        ForestDogRescueChecker(data_dir),
        JerryGreenChecker(data_dir),
        ManyTearsChecker(data_dir),
        Paws2RescueChecker(data_dir),
        ProDogsDirectChecker(data_dir),
        RaystedeChecker(data_dir),
        RSPCABrightonChecker(data_dir),
        RSPCALeedsChecker(data_dir),
        SCSRChecker(data_dir),
        SouthEastDogRescueChecker(data_dir),
        SpanielAidChecker(data_dir),
        BlueCrossChecker(data_dir, "bromsgrove"),
        BlueCrossChecker(data_dir, "burford"),
        StarfishChecker(data_dir),
        TeckelsChecker(data_dir),
        WythallChecker(data_dir),
        GsdrChecker(data_dir),
    ]


def get_active_checkers(data_dir: str) -> list[SiteChecker]:
    """Return checkers excluding those in the too-far list.

    Use this for all normal operations (daily check, listing, audit,
    cache populate/repair, tests).  The evaluate_rescue_centers function
    should use get_checkers() directly so it can evaluate all rescues.
    """
    from too_far import TooFarList

    too_far = TooFarList(data_dir)
    return [c for c in get_checkers(data_dir) if c.site_name not in too_far]
