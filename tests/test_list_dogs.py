"""Tests for list_dogs.py — terminal listing of available dogs."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import list_dogs
from sites.base import Dog


def make_dog(
    name: str = "Bella",
    age: str = "6 Months",
    gender: str = "Female",
    breed: str = "Spaniel",
    url: str = "https://example.org/bella",
    status: str = "Available",
    location: str = "Cardiff",
    photo_url: str = "",
) -> Dog:
    return Dog(
        name=name,
        age=age,
        gender=gender,
        breed=breed,
        url=url,
        status=status,
        location=location,
        photo_url=photo_url,
    )


class TestDogFromLine:
    def test_parses_full_line(self):
        line = "Available | Bella | 6 Months | Female | Spaniel | Cardiff | https://img | https://ex.org/b"
        dog = list_dogs.dog_from_line(line)
        assert dog.status == "Available"
        assert dog.name == "Bella"
        assert dog.age == "6 Months"
        assert dog.gender == "Female"
        assert dog.breed == "Spaniel"
        assert dog.location == "Cardiff"
        assert dog.photo_url == "https://img"
        assert dog.url == "https://ex.org/b"

    def test_parses_minimal_line(self):
        line = " |  |  |  |  |  |  | https://ex.org/b"
        dog = list_dogs.dog_from_line(line)
        assert dog.url == "https://ex.org/b"
        assert dog.name == ""

    def test_handles_pipes_in_fields(self):
        line = "Available | Fido | 2 Years | Male | Lab | London |  | https://ex.org/fido"
        dog = list_dogs.dog_from_line(line)
        assert dog.breed == "Lab"
        assert dog.url == "https://ex.org/fido"


class TestFormatTable:
    def test_single_dog(self):
        dogs = [make_dog()]
        table = list_dogs.format_table([("Test Site", dogs)])
        lines = table.strip().splitlines()
        assert len(lines) >= 2  # header + at least 1 data row
        assert "status" in lines[0].lower()
        assert "Bella" in table
        assert "https://example.org/bella" in table

    def test_multiple_dogs_and_sites(self):
        dogs1 = [make_dog(name="Bella"), make_dog(name="Luna", url="https://ex.org/luna")]
        dogs2 = [make_dog(name="Max", gender="Male", url="https://ex.org/max")]
        table = list_dogs.format_table([("Site A", dogs1), ("Site B", dogs2)])
        assert "Bella" in table
        assert "Luna" in table
        assert "Max" in table

    def test_empty_list(self):
        table = list_dogs.format_table([])
        assert table == "No dogs found."

    def test_pipe_delimited(self):
        dogs = [make_dog()]
        table = list_dogs.format_table([("Test", dogs)])
        data_lines = [
            line
            for line in table.strip().splitlines()
            if line.startswith("Available")
        ]
        assert len(data_lines) == 1
        assert " | " in data_lines[0]


class TestListCached:
    def test_reads_cache_files(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "cotswolds.txt").write_text(
            "Available | Bella | 6 Months | Female | Spaniel | Cardiff |  | https://ex.org/b\n"
        )

        with patch("list_dogs.get_checkers") as mock_registry:
            mock_checker = type(
                "Fake", (), {"data_file": "cotswolds.txt", "site_name": "Cotswolds"}
            )()
            mock_registry.return_value = [mock_checker]

            results = list_dogs.list_cached(str(data_dir))
            assert len(results) == 1
            site_name, dogs = results[0]
            assert site_name == "Cotswolds"
            assert len(dogs) == 1
            assert dogs[0].name == "Bella"

    def test_missing_cache_file_is_skipped(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        with patch("list_dogs.get_checkers") as mock_registry:
            mock_checker = type(
                "Fake", (), {"data_file": "nonexistent.txt", "site_name": "Ghost"}
            )()
            mock_registry.return_value = [mock_checker]

            results = list_dogs.list_cached(str(data_dir))
            assert results == []

    def test_does_not_modify_cache(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        cache_file = data_dir / "test.txt"
        original = "Available | Bella | 6 Months | Female | Spaniel | Cardiff |  | https://ex.org/b\n"
        cache_file.write_text(original)
        mtime_before = cache_file.stat().st_mtime

        with patch("list_dogs.get_checkers") as mock_registry:
            mock_checker = type("Fake", (), {"data_file": "test.txt", "site_name": "Test"})()
            mock_registry.return_value = [mock_checker]

            list_dogs.list_cached(str(data_dir))

        assert cache_file.read_text() == original
        assert cache_file.stat().st_mtime == mtime_before


class TestListLive:
    def test_fetches_and_parses_all_checkers(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        fake_dog = make_dog()

        mock_checker = type("Fake", (), {
            "site_name": "Test Site",
            "data_file": "test.txt",
            "fetch": lambda self: "<html></html>",
            "parse": lambda self, raw: [fake_dog],
        })()

        with patch("list_dogs.get_checkers", return_value=[mock_checker]):
            results = list_dogs.list_live(str(data_dir))
            assert len(results) == 1
            site_name, dogs = results[0]
            assert site_name == "Test Site"
            assert dogs == [fake_dog]

    def test_checker_error_is_handled(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        bad_checker = type("Fake", (), {
            "site_name": "Broken",
            "data_file": "broken.txt",
            "fetch": lambda self: (_ for _ in ()).throw(RuntimeError("boom")),
        })()

        with patch("list_dogs.get_checkers", return_value=[bad_checker]):
            results = list_dogs.list_live(str(data_dir))
            assert results == []

    def test_does_not_mutate_cache(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        cache_file = data_dir / "test.txt"
        cache_file.write_text("old data\n")

        fake_dog = make_dog()

        mock_checker = type("Fake", (), {
            "site_name": "Test",
            "data_file": "test.txt",
            "fetch": lambda self: "<html>",
            "parse": lambda self, raw: [fake_dog],
        })()

        with patch("list_dogs.get_checkers", return_value=[mock_checker]):
            list_dogs.list_live(str(data_dir))

        # Cache file should not be touched (no _save_current, no overwrite)
        assert cache_file.read_text() == "old data\n"
