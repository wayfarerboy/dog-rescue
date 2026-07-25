"""Tests for All Dogs Matter scraper."""

from unittest.mock import patch

from sites.all_dogs_matter import AllDogsMatterChecker
from sites.base import Dog


class TestAgeMonths:
    def test_year_old(self):
        assert AllDogsMatterChecker._age_months("1 year old") == 12

    def test_years(self):
        assert AllDogsMatterChecker._age_months("5 year old") == 60

    def test_months(self):
        assert AllDogsMatterChecker._age_months("9 Months") == 9

    def test_single_month(self):
        assert AllDogsMatterChecker._age_months("1 Month") == 1

    def test_years_approx(self):
        assert AllDogsMatterChecker._age_months("2 years approx") == 24

    def test_range_years(self):
        # "4-5 years" — first number is parsed
        assert AllDogsMatterChecker._age_months("4-5 years") == 48

    def test_unknown_returns_999(self):
        assert AllDogsMatterChecker._age_months("Unknown age") == 999

    def test_empty_returns_999(self):
        assert AllDogsMatterChecker._age_months("") == 999


class TestExtractField:
    def test_extract_breed(self):
        text = "Breed: Mastiff X Age: 5 year old Gender: Female Location: Waltham Abbey Can ..."
        assert AllDogsMatterChecker._extract_field(text, "Breed") == "Mastiff X"

    def test_extract_age(self):
        text = "Breed: Mastiff X Age: 5 year old Gender: Female Location: Waltham Abbey Can ..."
        assert AllDogsMatterChecker._extract_field(text, "Age") == "5 year old"

    def test_extract_gender(self):
        text = "Breed: Mastiff X Age: 5 year old Gender: Female Location: Waltham Abbey Can ..."
        assert AllDogsMatterChecker._extract_field(text, "Gender") == "Female"

    def test_extract_location(self):
        text = "Breed: Mastiff X Age: 5 year old Gender: Female Location: Waltham Abbey Can ..."
        assert AllDogsMatterChecker._extract_field(text, "Location") == "Waltham Abbey"

    def test_extract_location_with_more_about(self):
        text = (
            "Breed: Chihuahua Age: 1 year old Gender: Female "
            "Location: North London Can Fluffy live with cats? "
            "More about Fluffy: Please Read Profile Carefully..."
        )
        assert AllDogsMatterChecker._extract_field(text, "Location") == "North London"

    def test_extract_missing_field_returns_empty(self):
        text = "Breed: Lab Age: 2 years Gender: Male Location: London"
        assert AllDogsMatterChecker._extract_field(text, "Nope") == ""


class TestParse:
    def test_no_cards(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_single_dog_card(self, tmp_path):
        html = """<div class="grid multiple-cards no-title">
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/fluffy/">
              <div class="block-image">
                <div class="bg lazyload" data-back="https://alldogsmatter.co.uk/wp-content/uploads/fluffy.jpg"></div>
              </div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/fluffy/">Fluffy</a></h3>
              <p>Breed: Chihuahua Age: 1 year old Gender: Female Location: North London
              Can Fluffy live?</p>
            </div>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Fluffy"
        assert d.breed == "Chihuahua"
        assert d.age == "1 year old"
        assert d.gender == "Female"
        assert d.location == "North London"
        assert d.url == "https://alldogsmatter.co.uk/dogs/fluffy/"
        assert d.photo_url == "https://alldogsmatter.co.uk/wp-content/uploads/fluffy.jpg"

    def test_skips_adopted_dog(self, tmp_path):
        html = """<div class="grid multiple-cards no-title">
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/bear/">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/bear/">Bear</a></h3>
              <p>I have been adopted!</p>
            </div>
          </div>
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/max/">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/max/">Max</a></h3>
              <p>Breed: Labrador Age: 2 years Gender: Male Location: London Can Max live?</p>
            </div>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Max"

    def test_skips_adopted_case_insensitive(self, tmp_path):
        html = """<div class="grid multiple-cards no-title">
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/daisy/">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/daisy/">Daisy</a></h3>
              <p>I Have Been Adopted!</p>
            </div>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs == []

    def test_multiple_cards(self, tmp_path):
        html = """<div class="grid multiple-cards no-title">
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/a/">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/a/">A</a></h3>
              <p>Breed: X Age: 1 year Gender: Female Location: London Can A live?</p>
            </div>
          </div>
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/b/">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/b/">B</a></h3>
              <p>Breed: Y Age: 2 years Gender: Male Location: Essex Can B live?</p>
            </div>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        assert len(c.parse(html)) == 2

    def test_missing_href_skipped(self, tmp_path):
        html = """<div class="grid multiple-cards no-title">
          <div class="grid-block card three-col">
            <a class="card-image-link" href="">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a>Ghost</a></h3>
              <p>Breed: X Age: 1 year Gender: Female Location: London</p>
            </div>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_card_with_no_content_skipped(self, tmp_path):
        html = '<div class="grid-block card three-col"></div>'
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_card_with_no_paragraph_skipped(self, tmp_path):
        html = """<div class="grid-block card three-col">
          <div class="block-content">
            <h3><a href="https://alldogsmatter.co.uk/dogs/test/">Test</a></h3>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_missing_optional_fields(self, tmp_path):
        html = """<div class="grid multiple-cards no-title">
          <div class="grid-block card three-col">
            <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/min/">
              <div class="block-image"><div class="bg"></div></div>
            </a>
            <div class="block-content">
              <h3><a href="https://alldogsmatter.co.uk/dogs/min/">Min</a></h3>
              <p>Breed: X</p>
            </div>
          </div>
        </div>"""
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs[0].breed == "X"
        assert dogs[0].age == ""
        assert dogs[0].gender == ""
        assert dogs[0].location == ""


class TestGetMaxPages:
    def test_no_pagination_returns_1(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._get_max_pages("<html></html>") == 1

    def test_finds_max_page(self, tmp_path):
        html = """<a class="page-numbers" href="/dogs/page/2/">2</a>
        <a class="page-numbers" href="/dogs/page/3/">3</a>
        <a class="page-numbers" href="/dogs/page/17/">17</a>"""
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._get_max_pages(html) == 17

    def test_current_page_span_ignored(self, tmp_path):
        html = """<span class="page-numbers current">1</span>
        <a class="page-numbers" href="/dogs/page/2/">2</a>"""
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._get_max_pages(html) == 2


class TestCheckFiltering:
    def test_filters_by_gender_and_age(self, tmp_path):
        """check() should only return Female dogs <= 12 months."""
        c = AllDogsMatterChecker(str(tmp_path))
        # Simulate fetch returning page 1, max_pages=1
        with (
            patch.object(c, "_fetch_page", return_value=""),
            patch.object(c, "_get_max_pages", return_value=1),
            patch.object(c, "parse", return_value=[
                Dog(name="YoungF", age="6 Months", gender="Female",
                    breed="X", url="https://x.com/yf", location="L"),
                Dog(name="OldF", age="3 years", gender="Female",
                    breed="X", url="https://x.com/of", location="L"),
                Dog(name="YoungM", age="6 Months", gender="Male",
                    breed="X", url="https://x.com/ym", location="L"),
            ]),
        ):
            new = c.check()
        assert len(new) == 1
        assert new[0].name == "YoungF"

    def test_empty_when_no_matches(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        with (
            patch.object(c, "_fetch_page", return_value=""),
            patch.object(c, "_get_max_pages", return_value=1),
            patch.object(c, "parse", return_value=[
                Dog(name="OldM", age="3 years", gender="Male",
                    breed="X", url="https://x.com/om", location="L"),
            ]),
        ):
            new = c.check()
        assert new == []

    def test_saves_filtered_dogs_and_diffs_on_second_run(self, tmp_path):
        """Verify check() saves filtered dogs and detects no new on rerun."""
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = [
            Dog(name="Bella", age="6 Months", gender="Female",
                breed="Spaniel", url="https://x.com/bella", location="L"),
        ]
        with (
            patch.object(c, "_fetch_page", return_value=""),
            patch.object(c, "_get_max_pages", return_value=1),
            patch.object(c, "parse", return_value=dogs),
        ):
            new1 = c.check()
        assert len(new1) == 1
        # Second run: should see no new dogs
        with (
            patch.object(c, "_fetch_page", return_value=""),
            patch.object(c, "_get_max_pages", return_value=1),
            patch.object(c, "parse", return_value=dogs),
        ):
            new2 = c.check()
        assert new2 == []
