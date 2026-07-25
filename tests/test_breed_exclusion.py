from __future__ import annotations

from pathlib import Path

from breed_exclusion import BreedExclusionList, filter_dogs_by_breed
from sites.base import Dog


def make_dog(breed: str = "Spaniel", **kwargs: object) -> Dog:
    defaults: dict[str, str] = {
        "name": "Test",
        "age": "1 Year",
        "gender": "Female",
        "breed": breed,
        "url": "https://example.org",
        "status": "Available",
        "location": "Cardiff",
        "photo_url": "",
    }
    defaults.update({k: str(v) for k, v in kwargs.items() if k in defaults})  # type: ignore[arg-type]
    return Dog(**defaults)  # type: ignore[arg-type]


class TestBreedExclusionList:
    def test_empty_when_no_file(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        assert bel.breeds() == []
        assert "Pug" not in bel

    def test_add_persists_breed(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        assert "Pug" in bel
        assert bel.breeds() == ["Pug"]

    def test_add_idempotent(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.add("Pug")
        assert bel.breeds() == ["Pug"]

    def test_case_insensitive_contains(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        assert "pug" in bel
        assert "PUG" in bel
        assert " Pug " in bel

    def test_case_insensitive_add_idempotent(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.add("pug")
        assert bel.breeds() == ["Pug"]

    def test_loads_existing_file(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "excluded-breeds.txt").write_text("Pug\nLurcher\n")

        bel = BreedExclusionList(str(tmp_path))
        assert bel.breeds() == ["Pug", "Lurcher"]
        assert "Pug" in bel
        assert "Lurcher" in bel
        assert "Spaniel" not in bel

    def test_add_appends_to_existing(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "excluded-breeds.txt").write_text("Pug\n")

        bel = BreedExclusionList(str(tmp_path))
        bel.add("Lurcher")
        assert bel.breeds() == ["Pug", "Lurcher"]

    def test_ignores_blank_lines_on_load(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "excluded-breeds.txt").write_text("Pug\n\nLurcher\n  \n")

        bel = BreedExclusionList(str(tmp_path))
        assert bel.breeds() == ["Pug", "Lurcher"]

    def test_file_created_on_demand(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        assert not bel._data_path.exists()
        bel.add("Pug")
        assert bel._data_path.exists()

    def test_remove_existing_breed(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.add("Lurcher")
        bel.remove("Pug")
        assert bel.breeds() == ["Lurcher"]
        assert "Pug" not in bel
        assert "Lurcher" in bel

    def test_remove_case_insensitive(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.remove("pug")
        assert bel.breeds() == []
        assert "Pug" not in bel

    def test_remove_nonexistent_is_noop(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.remove("Spaniel")
        assert bel.breeds() == ["Pug"]

    def test_remove_last_breed_clears_file(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.remove("Pug")
        assert bel.breeds() == []
        assert bel._data_path.exists()  # file still exists, just empty

    def test_reload_after_remove(self, tmp_path: Path):
        data_dir = Path(tmp_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "excluded-breeds.txt").write_text("Pug\nLurcher\n")

        bel = BreedExclusionList(str(tmp_path))
        bel.remove("Pug")

        # Reload from disk
        bel2 = BreedExclusionList(str(tmp_path))
        assert bel2.breeds() == ["Lurcher"]


class TestFilterDogsByBreed:
    def test_filters_out_excluded_breeds(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        bel.add("Lurcher")

        dogs = [
            make_dog(breed="Pug"),
            make_dog(breed="Spaniel"),
            make_dog(breed="Lurcher"),
            make_dog(breed="Collie"),
        ]
        result = filter_dogs_by_breed(dogs, bel)
        assert len(result) == 2
        assert {d.breed for d in result} == {"Spaniel", "Collie"}

    def test_case_insensitive_matching(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")

        dogs = [make_dog(breed="pug"), make_dog(breed="PUG"), make_dog(breed=" Pug ")]
        result = filter_dogs_by_breed(dogs, bel)
        assert len(result) == 0

    def test_keeps_dogs_with_empty_breed(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")

        dogs = [make_dog(breed=""), make_dog(breed="Pug")]
        result = filter_dogs_by_breed(dogs, bel)
        assert len(result) == 1
        assert result[0].breed == ""

    def test_empty_exclusion_list_keeps_all(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        dogs = [make_dog(breed="Pug"), make_dog(breed="Spaniel")]
        result = filter_dogs_by_breed(dogs, bel)
        assert result == dogs

    def test_all_excluded_returns_empty(self, tmp_path: Path):
        bel = BreedExclusionList(str(tmp_path))
        bel.add("Pug")
        dogs = [make_dog(breed="Pug"), make_dog(breed="Pug")]
        result = filter_dogs_by_breed(dogs, bel)
        assert result == []
