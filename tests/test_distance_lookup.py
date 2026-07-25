"""Tests for distance_lookup.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from distance_lookup import MAX_DISTANCE_MILES_DEFAULT, DistanceLookup, filter_dogs_by_distance


class TestDistanceLookup:
    def test_empty_when_no_file(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path))
        assert dl.get_distance("Cardiff") is None
        assert dl.centers() == []

    def test_loads_existing_file(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "distances.json").write_text(
            json.dumps({"Cardiff": 87.5, "Leeds": 150.2})
        )

        dl = DistanceLookup(str(tmp_path))
        assert dl.get_distance("Cardiff") == 87.5
        assert dl.get_distance("Leeds") == 150.2
        assert dl.get_distance("Unknown") is None

    def test_get_distance_returns_none_for_empty_string(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path))
        assert dl.get_distance("") is None

    def test_save_persists_cache(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path))
        dl._cache["Cardiff"] = 87.5
        dl.save()

        # Verify file was created
        assert (tmp_path / "distances.json").exists()
        content = json.loads((tmp_path / "distances.json").read_text())
        assert content["Cardiff"] == 87.5

    def test_save_writes_human_readable_json(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path))
        dl._cache["Cardiff"] = 87.5
        dl.save()

        raw = (tmp_path / "distances.json").read_text()
        assert "87.5" in raw
        assert "\n" in raw  # indented output

    def test_centers_returns_all_cached_centers(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path))
        dl._cache["Cardiff"] = 87.5
        dl._cache["Leeds"] = 150.2
        dl._cache["London"] = None  # failed lookup

        assert sorted(dl.centers()) == ["Cardiff", "Leeds", "London"]

    def test_handles_corrupt_json_file(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "distances.json").write_text("not json")

        dl = DistanceLookup(str(tmp_path))
        assert dl._cache == {}
        assert dl.get_distance("Anything") is None

    def test_lookup_calls_api_and_caches(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="test-key")
        mock_response = {
            "rows": [
                {
                    "elements": [
                        {
                            "status": "OK",
                            "distance": {"text": "140 km", "value": 140000},
                            "duration": {"text": "1 hour 30 mins", "value": 5400},
                        }
                    ]
                }
            ],
            "status": "OK",
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            result = dl._lookup("Cardiff")

            # 140000 meters ≈ 86.99 miles
            assert result is not None
            assert abs(result - 86.99) < 0.1
            mock_get.assert_called_once()

            # Cache persisted to file
            assert (tmp_path / "distances.json").exists()
            cached = json.loads((tmp_path / "distances.json").read_text())
            assert "Cardiff" in cached
            assert abs(cached["Cardiff"] - 86.99) < 0.1

    def test_lookup_caches_none_when_center_not_found(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="test-key")
        mock_response = {
            "rows": [
                {
                    "elements": [
                        {"status": "NOT_FOUND"}
                    ]
                }
            ],
            "status": "OK",
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            result = dl._lookup("Nowhere")
            assert result is None
            assert dl._cache["Nowhere"] is None
            # File written with None value
            cached = json.loads((tmp_path / "distances.json").read_text())
            assert cached["Nowhere"] is None

    def test_lookup_returns_none_without_api_key(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="")
        result = dl._lookup("Cardiff")
        assert result is None

    def test_lookup_returns_none_on_api_error(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="test-key")

        with patch("requests.get", side_effect=Exception("boom")):
            result = dl._lookup("Cardiff")
            assert result is None

    def test_get_distance_uses_cache_not_api(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="test-key")
        dl._cache["Cardiff"] = 50.0

        with patch.object(dl, "_lookup") as mock_lookup:
            result = dl.get_distance("Cardiff")
            assert result == 50.0
            mock_lookup.assert_not_called()

    def test_get_distance_calls_lookup_on_cache_miss(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="test-key")

        with patch.object(dl, "_lookup", return_value=42.0) as mock_lookup:
            result = dl.get_distance("Cardiff")
            assert result == 42.0
            mock_lookup.assert_called_once_with("Cardiff")


class TestFilterDogsByDistance:
    @staticmethod
    def _make_dl(cache: dict[str, float | None]) -> DistanceLookup:
        """Create a DistanceLookup with a pre-populated cache, no API key."""
        dl = DistanceLookup.__new__(DistanceLookup)
        dl._cache = cache
        dl._api_key = ""
        dl._data_dir = None  # not used by filter_dogs_by_distance
        return dl

    def _make_dog(self, location: str):
        from sites.base import Dog

        return Dog(
            name="Test",
            age="6 Months",
            gender="Female",
            breed="Spaniel",
            url="https://example.org",
            location=location,
        )

    def test_includes_dog_within_max_distance(self):
        dl = self._make_dl({"Cardiff": 80.0})

        dogs = [self._make_dog("Cardiff")]
        result = filter_dogs_by_distance(dogs, dl, max_distance=100.0)
        assert len(result) == 1

    def test_excludes_dog_beyond_max_distance(self):
        dl = self._make_dl({"Edinburgh": 320.0})

        dogs = [self._make_dog("Edinburgh")]
        result = filter_dogs_by_distance(dogs, dl, max_distance=200.0)
        assert len(result) == 0

    def test_includes_dog_at_exact_max_distance(self):
        dl = self._make_dl({"Cardiff": 100.0})

        dogs = [self._make_dog("Cardiff")]
        result = filter_dogs_by_distance(dogs, dl, max_distance=100.0)
        assert len(result) == 1

    def test_includes_dog_with_unknown_center(self):
        dl = self._make_dl({})

        dogs = [self._make_dog("Mystery Location")]
        result = filter_dogs_by_distance(dogs, dl, max_distance=100.0)
        assert len(result) == 1

    def test_includes_dog_with_none_cached_distance(self):
        dl = self._make_dl({"Nowhere": None})

        dogs = [self._make_dog("Nowhere")]
        result = filter_dogs_by_distance(dogs, dl, max_distance=100.0)
        assert len(result) == 1

    def test_skips_filtering_when_max_distance_is_none(self):
        dl = self._make_dl({})

        dogs = [self._make_dog("Anywhere")]
        result = filter_dogs_by_distance(dogs, dl, max_distance=None)
        assert len(result) == 1
        assert result == dogs

    def test_mixed_centers_filtered_correctly(self):
        dl = self._make_dl({
            "Cardiff": 80.0,
            "Edinburgh": 320.0,
            "Unknown": None,
        })

        dogs = [
            self._make_dog("Cardiff"),
            self._make_dog("Edinburgh"),
            self._make_dog("Unknown"),
            self._make_dog("Secret Base"),
        ]
        result = filter_dogs_by_distance(dogs, dl, max_distance=100.0)
        # Only Edinburgh should be excluded — beyond max distance
        assert len(result) == 3
        locations = {d.location for d in result}
        assert locations == {"Cardiff", "Unknown", "Secret Base"}

    def test_filtering_preserves_dog_object_integrity(self):
        dl = self._make_dl({"Cardiff": 80.0})

        dog = self._make_dog("Cardiff")
        result = filter_dogs_by_distance([dog], dl, max_distance=100.0)
        assert result[0] is dog  # same object, not a copy

    def test_default_max_distance(self):
        assert MAX_DISTANCE_MILES_DEFAULT > 0


class TestDistanceLookupLive:
    """Smoke test that the API key env var is loaded correctly.

    These tests do NOT call the live API — they only validate that
    constructing with an API key passes it through correctly.
    """

    def test_api_key_passed_to_lookup(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="sk-abc123")
        assert dl._api_key == "sk-abc123"

    def test_api_key_stored_and_used(self, tmp_path: Path):
        dl = DistanceLookup(str(tmp_path), api_key="real-key")
        mock_response = {
            "rows": [{"elements": [{"status": "OK", "distance": {"value": 50000}}]}],
            "status": "OK",
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None
            dl._lookup("Cardiff")
            # Verify the API key was passed
            call_args = mock_get.call_args
            assert call_args[1]["params"]["key"] == "real-key"
