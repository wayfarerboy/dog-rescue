from __future__ import annotations

from pathlib import Path

from sites.base import Dog, SiteChecker


class FakeChecker(SiteChecker):
    """Concrete checker for testing the base class."""

    site_name = "Fake Site"
    data_file = "fake.txt"

    def __init__(self, data_dir: str, raw: str = "", dogs: list[Dog] | None = None):
        super().__init__(data_dir)
        self._raw = raw
        self._dogs = dogs or []

    def fetch(self) -> str:
        return self._raw

    def parse(self, raw: str) -> list[Dog]:
        return self._dogs


def make_dog(name: str, url: str) -> Dog:
    return Dog(name=name, age="1", gender="F", breed="X", url=url)


class TestSiteChecker:
    def test_load_previous_empty(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        assert c._load_previous() == set()

    def test_load_previous_has_urls(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        c._data_path.write_text(
            " | A | 1 | F | X |  | https://a\n"
            " | B | 2 | M | Y |  | https://b\n"
        )
        urls = c._load_previous()
        assert urls == {"https://a", "https://b"}

    def test_load_previous_fallback_for_bare_urls(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        c._data_path.write_text("https://a\nhttps://b\n")
        assert c._load_previous() == {"https://a", "https://b"}

    def test_save_current_writes_lines(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        dogs = [make_dog("A", "https://a"), make_dog("B", "https://b")]
        c._save_current(dogs)
        lines = c._data_path.read_text().strip().splitlines()
        assert len(lines) == 2
        assert lines[0].endswith("https://a")
        assert lines[1].endswith("https://b")

    def test_diff_all_new_when_no_previous(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        dogs = [make_dog("A", "https://a")]
        new = c.diff(dogs)
        assert new == dogs

    def test_diff_filters_seen_urls(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        c._data_path.write_text(" | Old | 1 | F | X |  | https://old\n")
        dogs = [make_dog("Old", "https://old"), make_dog("New", "https://new")]
        new = c.diff(dogs)
        assert new == [make_dog("New", "https://new")]

    def test_diff_all_seen_returns_empty(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        c._data_path.write_text(" | A | 1 | F | X |  | https://a\n")
        new = c.diff([make_dog("A", "https://a")])
        assert new == []

    def test_check_returns_new_and_saves(self, tmp_path: Path):
        c = FakeChecker(
            str(tmp_path),
            dogs=[make_dog("A", "https://a"), make_dog("B", "https://b")],
        )
        # First run: both are new
        new = c.check()
        assert len(new) == 2
        saved = c._data_path.read_text().strip().splitlines()
        assert len(saved) == 2

        # Second run: no new dogs
        new2 = c.check()
        assert new2 == []

    def test_format_section(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        dogs = [make_dog("Bella", "https://bella")]
        section = c.format_section(dogs, "Test Site", "Col1 | Col2")
        assert "=== Test Site ===" in section
        assert "https://bella" in section
        assert "Bella" in section

    def test_format_section_empty(self, tmp_path: Path):
        c = FakeChecker(str(tmp_path))
        assert c.format_section([], "X", "C") == ""
