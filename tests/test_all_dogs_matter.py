"""Tests for All Dogs Matter site checker."""

from bs4 import BeautifulSoup

from sites.all_dogs_matter import AllDogsMatterChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestParseAgeMonths:
    def test_years_only(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("1 year old") == 12
        assert c._parse_age_months("5 year old") == 60
        assert c._parse_age_months("2 years") == 24
        assert c._parse_age_months("1 Year old") == 12

    def test_months_only(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("9 Months") == 9
        assert c._parse_age_months("7 months") == 7
        assert c._parse_age_months("3 month") == 3

    def test_years_and_months(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("4 years 3 months") == 51
        assert c._parse_age_months("3 years 10 months") == 46

    def test_decimal_years(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("1.5 years (approx)") == 18

    def test_with_approx_prefix(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("approx. 18 months") == 18

    def test_range_uses_first_number(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("1-2 years old") == 12
        assert c._parse_age_months("3-4 years approx") == 36

    def test_unparseable_returns_none(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c._parse_age_months("Just a puppy") is None
        assert c._parse_age_months("") is None


class TestParse:
    def _card(self, name="Bella", breed="Spaniel", age="8 Months",
               gender="Female", location="London", href="/dogs/bella/",
               extra=""):
        return f"""
        <div class="grid-block card three-col">
          <a class="card-image-link" href="https://alldogsmatter.co.uk{href}"></a>
          <div class="block-content">
            <h3><a href="https://alldogsmatter.co.uk{href}">{name}</a></h3>
            <p>Breed: {breed} Age: {age} Gender: {gender} Location: {location} {extra}</p>
          </div>
        </div>
        """

    def test_empty(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_no_cards(self, tmp_path):
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse("<html><div class='grid-block card'></div></html>") == []

    def test_single_dog(self, tmp_path):
        html = self._card(
            name="Bella", breed="Cocker Spaniel", age="8 Months",
            gender="Female", location="Waltham Abbey",
            href="/dogs/bella/"
        )
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Bella"
        assert d.breed == "Cocker Spaniel"
        assert d.age == "8 Months"
        assert d.gender == "Female"
        assert d.location == "Waltham Abbey"
        assert d.url == "https://alldogsmatter.co.uk/dogs/bella/"

    def test_skips_adopted(self, tmp_path):
        html = """
        <div class="grid-block card three-col">
          <div class="block-content">
            <h3><a href="https://alldogsmatter.co.uk/dogs/lucky/">Lucky</a></h3>
            <p>I have been adopted!</p>
          </div>
        </div>
        """
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_skips_male(self, tmp_path):
        html = self._card(name="Rex", gender="Male")
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_skips_old_age(self, tmp_path):
        html = self._card(name="Luna", age="3 years", gender="Female")
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_keeps_one_year_old(self, tmp_path):
        html = self._card(name="Daisy", age="1 year old", gender="Female")
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Daisy"

    def test_unparseable_age_skipped(self, tmp_path):
        html = self._card(name="Mystery", age="Just a baby", gender="Female")
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_multiple_mixed(self, tmp_path):
        """Only female dogs <= 12 months, non-adopted pass through."""
        html = (
            self._card(name="Bella", age="8 Months", gender="Female", href="/dogs/bella/")
            + self._card(name="Rex", age="6 Months", gender="Male", href="/dogs/rex/")
            + self._card(name="Luna", age="2 years", gender="Female", href="/dogs/luna/")
            + self._card(name="Daisy", age="11 Months", gender="Female", href="/dogs/daisy/")
        )
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 2
        names = {d.name for d in dogs}
        assert names == {"Bella", "Daisy"}

    def test_missing_card_link(self, tmp_path):
        html = """
        <div class="grid-block card three-col">
          <div class="block-content">
            <h3>No Link</h3>
            <p>Breed: X Age: 5 Months Gender: Female Location: London</p>
          </div>
        </div>
        """
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].url == ""

    def test_missing_paragraph(self, tmp_path):
        html = """
        <div class="grid-block card three-col">
          <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/ghost/"></a>
        </div>
        """
        c = AllDogsMatterChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_breed_with_x_suffix(self, tmp_path):
        html = self._card(name="Lacey", breed="Mastiff X", age="9 Months",
                          gender="Female", location="Waltham Abbey")
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs[0].breed == "Mastiff X"

    def test_age_with_nbsp(self, tmp_path):
        """Age field may contain non-breaking spaces; parsing should handle them."""
        html = """
        <div class="grid-block card three-col">
          <a class="card-image-link" href="https://alldogsmatter.co.uk/dogs/test/"></a>
          <div class="block-content">
            <h3><a href="https://alldogsmatter.co.uk/dogs/test/">Test</a></h3>
            <p>Breed: Lab Age: 11\u00a0Months Gender: Female Location: London</p>
          </div>
        </div>
        """
        c = AllDogsMatterChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].age == "11\u00a0Months"


class TestFetchPage:
    def test_fetch_returns_string(self, tmp_path):
        """fetch() is required by ABC but pagination goes through check()."""
        c = AllDogsMatterChecker(str(tmp_path))
        # fetch should return the first page
        result = c.fetch()
        assert isinstance(result, str)
        assert len(result) > 0
