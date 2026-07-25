"""Too-far list — tracking of rescue sites excluded because all their
centers are beyond the maximum driving distance.

Usage:
    from too_far import TooFarList

    tfl = TooFarList("data")
    if "Some Rescue" not in tfl:
        # evaluate the rescue...
        tfl.add("Some Rescue")
"""

from __future__ import annotations

from pathlib import Path


class TooFarList:
    """A set of rescue names excluded due to distance, persisted as a text file.

    File path: <data_dir>/too-far.txt — one rescue name per line.
    """

    _FILE_NAME = "too-far.txt"

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_path = self._data_dir / self._FILE_NAME
        self._names: list[str] = []
        if self._data_path.exists():
            self._names = [
                line.strip()
                for line in self._data_path.read_text().splitlines()
                if line.strip()
            ]

    def names(self) -> list[str]:
        """Return all excluded rescue names in insertion order."""
        return list(self._names)

    def add(self, name: str) -> None:
        """Add a rescue name to the too-far list. Idempotent."""
        if name not in self._names:
            self._names.append(name)
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._data_path.write_text("\n".join(self._names) + "\n")

    def __contains__(self, name: str) -> bool:
        return name in self._names
