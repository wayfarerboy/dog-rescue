"""Shared registry of site checkers.

Import this module to get the canonical list of configured checker instances.
Both the cron script and future scripts use get_checkers() instead of
hardcoding the list in each entrypoint.
"""

from __future__ import annotations

from sites.base import SiteChecker
from sites.cotswolds import CotswoldsChecker
from sites.dogs_trust import DogsTrustChecker
from sites.jerry_green import JerryGreenChecker
from sites.many_tears import ManyTearsChecker
from sites.rspca_brighton import RSPCABrightonChecker
from sites.scsr import SCSRChecker
from sites.south_east_dog_rescue import SouthEastDogRescueChecker


def get_checkers(data_dir: str) -> list[SiteChecker]:
    """Return the canonical list of configured checker instances.

    Args:
        data_dir: Path to the data directory for cache files.
    """
    return [
        ManyTearsChecker(data_dir),
        SCSRChecker(data_dir),
        DogsTrustChecker(data_dir),
        JerryGreenChecker(data_dir),
        SouthEastDogRescueChecker(data_dir),
        CotswoldsChecker(data_dir),
        RSPCABrightonChecker(data_dir),
    ]
