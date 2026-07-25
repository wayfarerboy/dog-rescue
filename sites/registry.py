"""Shared registry of site checkers.

Import this module to get the canonical list of configured checker instances.
Both the cron script and future scripts use get_checkers() instead of
hardcoding the list in each entrypoint.
"""

from __future__ import annotations

from sites.all_dogs_matter import AllDogsMatterChecker
from sites.base import SiteChecker
from sites.cotswolds import CotswoldsChecker
from sites.dogs_trust import DogsTrustChecker
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


def get_checkers(data_dir: str) -> list[SiteChecker]:
    """Return the canonical list of configured checker instances.

    Args:
        data_dir: Path to the data directory for cache files.
    """
    return [
        AllDogsMatterChecker(data_dir),
        CotswoldsChecker(data_dir),
        DogsTrustChecker(data_dir),
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
    ]
