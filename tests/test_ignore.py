from __future__ import annotations

from pathlib import Path

from ignore import IgnoredList

URL = "https://brighterdaysrescue.com/dogs/dolly-hius"


class TestIgnoredList:
    def test_empty_when_no_file(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        assert dl.urls() == []
        assert URL not in dl

    def test_add_persists_url(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        dl.add(URL)
        assert URL in dl
        assert dl.urls() == [URL]

    def test_add_idempotent(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        dl.add(URL)
        dl.add(URL)
        assert dl.urls() == [URL]

    def test_add_ignores_blank(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        dl.add("   ")
        dl.add("")
        assert dl.urls() == []

    def test_remove(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        dl.add(URL)
        dl.remove(URL)
        assert URL not in dl
        assert dl.urls() == []

    def test_remove_noop_when_absent(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        dl.remove(URL)
        assert dl.urls() == []

    def test_toggle(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        assert dl.toggle(URL) is True
        assert URL in dl
        assert dl.toggle(URL) is False
        assert URL not in dl

    def test_loads_existing_file(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "ignored.txt").write_text("https://a/\nhttps://b/\n")

        dl = IgnoredList(str(tmp_path))
        assert dl.urls() == ["https://a/", "https://b/"]
        assert "https://a/" in dl
        assert "https://c/" not in dl

    def test_ignores_blank_lines_on_load(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "ignored.txt").write_text("https://a/\n\nhttps://b/\n  \n")

        dl = IgnoredList(str(tmp_path))
        assert dl.urls() == ["https://a/", "https://b/"]

    def test_file_created_on_demand(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        assert not dl._data_path.exists()
        dl.add(URL)
        assert dl._data_path.exists()
        assert URL + "\n" in dl._data_path.read_text()

    def test_remove_empty_file(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        dl.add(URL)
        dl.remove(URL)
        assert dl._data_path.exists()
        assert dl._data_path.read_text() == ""

    def test_migrates_legacy_discounted_file(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "discounted.txt").write_text("https://a/\n")

        il = IgnoredList(str(tmp_path))
        assert il.urls() == ["https://a/"]
        assert "https://a/" in il
        # legacy file moved out of the way, new file used from now on
        assert not (data_dir / "discounted.txt").exists()
        il.add("https://b/")
        assert (data_dir / "ignored.txt").read_text().split() == ["https://a/", "https://b/"]

    def test_len(self, tmp_path: Path):
        dl = IgnoredList(str(tmp_path))
        assert len(dl) == 0
        dl.add("https://a/")
        dl.add("https://b/")
        assert len(dl) == 2
