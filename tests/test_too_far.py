from __future__ import annotations

from pathlib import Path

from too_far import TooFarList


class TestTooFarList:
    def test_empty_when_no_file(self, tmp_path: Path):
        tfl = TooFarList(str(tmp_path))
        assert tfl.names() == []
        assert "Anything" not in tfl

    def test_add_persists_name(self, tmp_path: Path):
        tfl = TooFarList(str(tmp_path))
        tfl.add("Pro Dogs Direct")
        assert "Pro Dogs Direct" in tfl
        assert tfl.names() == ["Pro Dogs Direct"]

    def test_add_idempotent(self, tmp_path: Path):
        tfl = TooFarList(str(tmp_path))
        tfl.add("Spaniel Aid")
        tfl.add("Spaniel Aid")
        assert tfl.names() == ["Spaniel Aid"]

    def test_loads_existing_file(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "too-far.txt").write_text("Rescue A\nRescue B\n")

        tfl = TooFarList(str(tmp_path))
        assert tfl.names() == ["Rescue A", "Rescue B"]
        assert "Rescue A" in tfl
        assert "Rescue B" in tfl
        assert "Rescue C" not in tfl

    def test_add_appends_to_existing(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "too-far.txt").write_text("Rescue A\n")

        tfl = TooFarList(str(tmp_path))
        tfl.add("Rescue B")
        assert tfl.names() == ["Rescue A", "Rescue B"]

    def test_ignores_blank_lines_on_load(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "too-far.txt").write_text("Rescue A\n\nRescue B\n  \n")

        tfl = TooFarList(str(tmp_path))
        assert tfl.names() == ["Rescue A", "Rescue B"]

    def test_file_created_on_demand(self, tmp_path: Path):
        tfl = TooFarList(str(tmp_path))
        assert not tfl._data_path.exists()
        tfl.add("Test Rescue")
        assert tfl._data_path.exists()
        assert "Test Rescue\n" in tfl._data_path.read_text()
