"""Tests for Blue Cross site checker."""

from __future__ import annotations

from sites.blue_cross import BlueCrossChecker

# Sample listing HTML with two pet cards (one dog, one cat)
LISTING_HTML = """\
<div class="rehoming-centre-pets">
  <div class="splide__list">
    <li class="splide__slide m-slide m-slide--content">
      <div class="m-slide__content">
        <a class="m-pet-listing-item" href="/pet/buddy-123">
          <div class="m-pet-listing-item__image">
            <img data-srcset="https://example.com/photo.jpg 542w"/>
          </div>
          <div class="m-pet-listing-item__content">
            <h4 class="m-pet-listing-item__content--title"><span>Buddy</span></h4>
            <dl><dt class="sr-only">Breed</dt><dd>Labrador</dd></dl>
            <dl><dt class="sr-only">Sex</dt><dd>Male</dd></dl>
            <dl><dt class="sr-only">Age</dt><dd>2 years</dd></dl>
          </div>
        </a>
      </div>
    </li>
    <li class="splide__slide m-slide m-slide--content">
      <div class="m-slide__content">
        <a class="m-pet-listing-item" href="/pet/whiskers-456">
          <div class="m-pet-listing-item__image"></div>
          <div class="m-pet-listing-item__content">
            <h4 class="m-pet-listing-item__content--title"><span>Whiskers</span></h4>
            <dl><dt class="sr-only">Breed</dt><dd>Domestic Short Hair</dd></dl>
            <dl><dt class="sr-only">Sex</dt><dd>Female</dd></dl>
            <dl><dt class="sr-only">Age</dt><dd>1 year</dd></dl>
          </div>
        </a>
      </div>
    </li>
  </div>
</div>"""

# Profile HTML for a single dog
DOG_PROFILE_HTML = """\
<html><body>
<div class="t-pet-profile">
  <dl>
    <dt class="mr-3" title="Species - dog        Labrador,  Yellow
      ">Breed</dt>
    <dd>Labrador,  Yellow</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="Male">Sex</dt>
    <dd>Male</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="2 years 4 months">Age</dt>
    <dd>2 years 4 months</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="West Midlands: Bromsgrove rehoming centre">Location</dt>
    <dd>West Midlands: Bromsgrove rehoming centre</dd>
  </dl>
  <img src="/sites/default/files/d8/styles/pet_profile/public/123.jpg.webp?itok=abc"/>
</div>
</body></html>"""

# Profile HTML for a cat
CAT_PROFILE_HTML = """\
<html><body>
<div class="t-pet-profile">
  <dl>
    <dt class="mr-3" title="Species - cat        Domestic Short Hair,  White
      ">Breed</dt>
    <dd>Domestic Short Hair,  White</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="Female">Sex</dt>
    <dd>Female</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="1 year 2 months">Age</dt>
    <dd>1 year 2 months</dd>
  </dl>
</div>
</body></html>"""

# Profile HTML for a horse
HORSE_PROFILE_HTML = """\
<html><body>
<div class="t-pet-profile">
  <dl>
    <dt class="mr-3" title="Species - horse        Cob,  Piebald
      ">Breed</dt>
    <dd>Cob,  Piebald</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="Male">Sex</dt>
    <dd>Male</dd>
  </dl>
  <dl>
    <dt class="mr-3" title="16 years 2 months">Age</dt>
    <dd>16 years 2 months</dd>
  </dl>
</div>
</body></html>"""


class TestParseProfile:
    """Tests for _parse_profile static method."""

    def test_parses_dog_profile(self) -> None:
        dog = BlueCrossChecker._parse_profile(
            DOG_PROFILE_HTML, name="Buddy", url="https://www.bluecross.org.uk/pet/buddy-123"
        )
        assert dog is not None
        assert dog.name == "Buddy"
        assert dog.breed == "Labrador, Yellow"
        assert dog.gender == "Male"
        assert dog.age == "2 years 4 months"
        assert dog.location == "West Midlands: Bromsgrove rehoming centre"
        assert dog.url == "https://www.bluecross.org.uk/pet/buddy-123"
        assert "/pet_profile/" in dog.photo_url

    def test_filters_cat(self) -> None:
        result = BlueCrossChecker._parse_profile(
            CAT_PROFILE_HTML, name="Whiskers", url="https://www.bluecross.org.uk/pet/whiskers-456"
        )
        assert result is None

    def test_filters_horse(self) -> None:
        result = BlueCrossChecker._parse_profile(
            HORSE_PROFILE_HTML, name="Rose", url="https://www.bluecross.org.uk/pet/rose-123"
        )
        assert result is None

    def test_parses_female_dog(self) -> None:
        html = DOG_PROFILE_HTML.replace("Male", "Female").replace('title="Male"', 'title="Female"')
        dog = BlueCrossChecker._parse_profile(
            html, name="Bella", url="https://www.bluecross.org.uk/pet/bella-123"
        )
        assert dog is not None
        assert dog.gender == "Female"


class TestParse:
    """Integration tests for parse() with mocked profile fetching."""

    def test_parse_filters_non_dogs(self, tmp_path, monkeypatch) -> None:
        """parse() should only return dogs, filtering out cats and horses."""
        checker = BlueCrossChecker(str(tmp_path), "bromsgrove")

        profile_map = {
            "https://www.bluecross.org.uk/pet/buddy-123": DOG_PROFILE_HTML,
            "https://www.bluecross.org.uk/pet/whiskers-456": CAT_PROFILE_HTML,
        }

        def mock_fetch_profile(url: str) -> str:
            return profile_map[url]

        monkeypatch.setattr(checker, "_fetch_profile", mock_fetch_profile)

        dogs = checker.parse(LISTING_HTML)
        assert len(dogs) == 1
        assert dogs[0].name == "Buddy"

    def test_parse_empty_listing(self, tmp_path) -> None:
        checker = BlueCrossChecker(str(tmp_path), "bromsgrove")
        dogs = checker.parse("<html></html>")
        assert dogs == []


class TestConstructor:
    """Tests for checker construction."""

    def test_valid_centre_keys(self, tmp_path) -> None:
        for key in ("bromsgrove", "burford"):
            checker = BlueCrossChecker(str(tmp_path), key)
            assert "Blue Cross" in checker.site_name

    def test_invalid_centre_key(self, tmp_path) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown Blue Cross centre"):
            BlueCrossChecker(str(tmp_path), "rolleston")

    def test_data_file_per_centre(self, tmp_path) -> None:
        b = BlueCrossChecker(str(tmp_path), "bromsgrove")
        u = BlueCrossChecker(str(tmp_path), "burford")
        assert b.data_file == "blue-cross-bromsgrove.txt"
        assert u.data_file == "blue-cross-burford.txt"
        assert b.data_file != u.data_file


class TestExtractPhoto:
    """Tests for photo extraction from profile pages."""

    def test_extracts_from_og_image(self) -> None:
        html = (
            '<meta property="og:image" content="https://example.com/dog.jpg"/>'
            + DOG_PROFILE_HTML
        )
        dog = BlueCrossChecker._parse_profile(
            html, name="Buddy", url="https://www.bluecross.org.uk/pet/buddy-123"
        )
        assert dog is not None
        assert dog.photo_url == "https://example.com/dog.jpg"

    def test_extracts_from_profile_img(self) -> None:
        dog = BlueCrossChecker._parse_profile(
            DOG_PROFILE_HTML, name="Buddy", url="https://www.bluecross.org.uk/pet/buddy-123"
        )
        assert dog is not None
        assert dog.photo_url.startswith("https://www.bluecross.org.uk/sites/default")

    def test_no_photo(self) -> None:
        html = DOG_PROFILE_HTML.replace('<img src="', '<img data-src="')
        dog = BlueCrossChecker._parse_profile(
            html, name="Buddy", url="https://www.bluecross.org.uk/pet/buddy-123"
        )
        assert dog is not None
        assert dog.photo_url == ""
