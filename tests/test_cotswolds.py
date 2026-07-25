"""Tests for the Cotswolds Dogs & Cats Home site checker."""

from unittest.mock import patch

from bs4 import BeautifulSoup

from sites.cotswolds import CotswoldsChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestParseAgeMonths:
    def test_years_old(self):
        assert CotswoldsChecker._parse_age_months("1.5 years old") == 18

    def test_single_year(self):
        assert CotswoldsChecker._parse_age_months("1 year old") == 12

    def test_multiple_years(self):
        assert CotswoldsChecker._parse_age_months("2 years old") == 24

    def test_months_old(self):
        assert CotswoldsChecker._parse_age_months("6 months old") == 6

    def test_single_month(self):
        assert CotswoldsChecker._parse_age_months("1 month old") == 1

    def test_empty_returns_0(self):
        assert CotswoldsChecker._parse_age_months("") == 0

    def test_unparseable_returns_0(self):
        assert CotswoldsChecker._parse_age_months("Unknown") == 0

    def test_approx_age(self):
        assert CotswoldsChecker._parse_age_months("1 year old approx") == 12


class TestParseDetailPage:
    def test_extracts_age_and_breed(self):
        """Detail page with 'Age:: X years old' and 'Breed:: Y' format."""
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes-grid vehica-grid">
            <div class="vehica-grid__element vehica-grid__element--1of1">
              <div class="vehica-car-attributes__name">Age:: 1.5 years old</div>
            </div>
            <div class="vehica-grid__element vehica-grid__element--1of1">
              <div class="vehica-car-attributes__name">Breed:: Patterdale Terrier X</div>
            </div>
          </div>
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == "1.5 years old"
        assert breed == "Patterdale Terrier X"
        assert location == ""
        assert photo_url == ""

    def test_extracts_age_months(self):
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes-grid vehica-grid">
            <div class="vehica-grid__element">
              <div class="vehica-car-attributes__name">Age:: 6 months old</div>
            </div>
            <div class="vehica-grid__element">
              <div class="vehica-car-attributes__name">Breed:: Labrador</div>
            </div>
          </div>
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == "6 months old"
        assert breed == "Labrador"
        assert location == ""
        assert photo_url == ""

    def test_missing_age_returns_empty(self):
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Breed:: Spaniel</div>
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == ""
        assert breed == "Spaniel"
        assert location == ""
        assert photo_url == ""

    def test_missing_breed_returns_empty(self):
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 2 years old</div>
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == "2 years old"
        assert breed == ""
        assert location == ""
        assert photo_url == ""

    def test_extracts_location(self):
        """Location is extracted from .vehica-address span."""
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 6 months old</div>
          <div class="vehica-car-attributes__name">Breed:: Terrier</div>
        </div>
        <div class="vehica-address">
          <a href="https://maps.google.com/?q=Test+Location">
            <span>Cambridge, Gloucestershire, GL2 7AS</span>
          </a>
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == "6 months old"
        assert breed == "Terrier"
        assert location == "Cambridge, Gloucestershire, GL2 7AS"
        assert photo_url == ""

    def test_extracts_photo_url(self):
        """Photo URL is extracted from first .vehica-car-gallery img."""
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 1 year old</div>
          <div class="vehica-car-attributes__name">Breed:: Lab</div>
        </div>
        <div class="vehica-car-gallery">
          <img src="https://example.org/dog1.jpg" />
          <img src="https://example.org/dog2.jpg" />
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == "1 year old"
        assert breed == "Lab"
        assert location == ""
        assert photo_url == "https://example.org/dog1.jpg"

    def test_extracts_all_fields(self):
        """All four fields populated from a full detail page."""
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 3 months old</div>
          <div class="vehica-car-attributes__name">Breed:: Cocker Spaniel</div>
        </div>
        <div class="vehica-address">
          <a href="https://maps.google.com/?q=Test">
            <span>Gloucester</span>
          </a>
        </div>
        <div class="vehica-car-gallery">
          <img src="https://example.org/puppy.jpg" />
        </div>
        """
        age, breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert age == "3 months old"
        assert breed == "Cocker Spaniel"
        assert location == "Gloucester"
        assert photo_url == "https://example.org/puppy.jpg"

    def test_missing_location_returns_empty(self):
        """No .vehica-address means empty location."""
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 2 years old</div>
        </div>
        <div class="vehica-car-gallery">
          <img src="https://example.org/dog.jpg" />
        </div>
        """
        _age, _breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert location == ""
        assert photo_url == "https://example.org/dog.jpg"

    def test_missing_photo_returns_empty(self):
        """No .vehica-car-gallery img means empty photo_url."""
        html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 1 year old</div>
        </div>
        <div class="vehica-address">
          <span>Somewhere</span>
        </div>
        """
        _age, _breed, location, photo_url = CotswoldsChecker._parse_detail_page(html)
        assert location == "Somewhere"
        assert photo_url == ""


class TestParseListingCards:
    def test_extracts_name_gender_status_url(self):
        html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <a class="vehica-car-card-link" href="https://cotswoldsdogsandcatshome.org.uk/animals/bella-2/">
              <div class="vehica-car-card__content">
                <a class="vehica-car-card__name"
                  href="https://cotswoldsdogsandcatshome.org.uk/animals/bella-2/"
                  title="Bella">Bella</a>
                <div class="vehica-car-card__separator"></div>
                <div class="vehica-car-card__info">
                  <div class="vehica-car-card__info__single">Available</div>
                  <div class="vehica-car-card__info__single">Female</div>
                  <div class="vehica-car-card__info__single">Dog</div>
                </div>
              </div>
            </a>
          </div>
        </div>
        """
        cards = CotswoldsChecker._parse_listing_cards(html)
        assert len(cards) == 1
        assert cards[0]["name"] == "Bella"
        assert cards[0]["gender"] == "Female"
        assert cards[0]["status"] == "Available"
        assert cards[0]["url"] == "https://cotswoldsdogsandcatshome.org.uk/animals/bella-2/"

    def test_multiple_cards(self):
        html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/luna/" title="Luna">Luna</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/rex/" title="Rex">Rex</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Male</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        cards = CotswoldsChecker._parse_listing_cards(html)
        assert len(cards) == 2
        assert cards[0]["name"] == "Luna"
        assert cards[1]["name"] == "Rex"

    def test_skips_cards_after_reserved_heading(self):
        """Cards after the 'Dogs that are Reserved' heading should be skipped."""
        html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/luna/" title="Luna">Luna</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        <h2 class="elementor-heading-title">Dogs that are Reserved, awaiting adoption!</h2>
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/mac/" title="Mac">Mac</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Reserved</div>
                <div class="vehica-car-card__info__single">Male</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        cards = CotswoldsChecker._parse_listing_cards(html)
        assert len(cards) == 1
        assert cards[0]["name"] == "Luna"

    def test_no_reserved_heading_keeps_all(self):
        """If there's no Reserved heading, all cards are kept."""
        html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/luna/" title="Luna">Luna</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/rex/" title="Rex">Rex</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Male</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        cards = CotswoldsChecker._parse_listing_cards(html)
        assert len(cards) == 2

    def test_card_missing_info_uses_empty(self):
        """Card with fewer info divs than expected gets empty strings for missing fields."""
        html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/ghost/" title="Ghost">Ghost</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
              </div>
            </div>
          </div>
        </div>
        """
        cards = CotswoldsChecker._parse_listing_cards(html)
        assert len(cards) == 1
        assert cards[0]["name"] == "Ghost"
        assert cards[0]["status"] == "Available"
        assert cards[0]["gender"] == ""

    def test_no_cards(self):
        assert CotswoldsChecker._parse_listing_cards("<html></html>") == []


class TestParse:
    def test_no_cards(self, tmp_path):
        c = CotswoldsChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_male_filtered_out(self, tmp_path):
        """Male dog should be filtered out before detail page fetch."""
        html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/rex/" title="Rex">Rex</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Male</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        c = CotswoldsChecker(str(tmp_path))
        # Male is filtered before detail fetch, so _fetch_detail_page should not be called
        with patch.object(c, "_fetch_detail_page") as mock_fetch:
            dogs = c.parse(html)
            mock_fetch.assert_not_called()
        assert dogs == []

    def test_female_under_12_months_included(self, tmp_path):
        """Female dog aged 6 months should be included."""
        listing_html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name"
                href="https://cotswoldsdogsandcatshome.org.uk/animals/luna/"
                title="Luna">Luna</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        detail_html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 6 months old</div>
          <div class="vehica-car-attributes__name">Breed:: Spaniel</div>
        </div>
        <div class="vehica-address">
          <span>Cambridge</span>
        </div>
        <div class="vehica-car-gallery">
          <img src="https://example.org/luna.jpg" />
        </div>
        """
        c = CotswoldsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.gender == "Female"
        assert d.status == "Available"
        assert d.age == "6 months old"
        assert d.breed == "Spaniel"
        assert d.location == "Cambridge"
        assert d.photo_url == "https://example.org/luna.jpg"
        assert d.url == "https://cotswoldsdogsandcatshome.org.uk/animals/luna/"

    def test_female_over_12_months_filtered_out(self, tmp_path):
        """Female dog over 12 months should be filtered out."""
        listing_html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/bella/" title="Bella">Bella</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        detail_html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 1.5 years old</div>
          <div class="vehica-car-attributes__name">Breed:: Terrier</div>
        </div>
        """
        c = CotswoldsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert dogs == []

    def test_12_months_exactly_included(self, tmp_path):
        """Female dog at exactly 12 months (1 year) should be included."""
        listing_html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/pup/" title="Pup">Pup</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        detail_html = """
        <div class="vehica-car-attributes">
          <div class="vehica-car-attributes__name">Age:: 12 months old</div>
          <div class="vehica-car-attributes__name">Breed:: Pug</div>
        </div>
        <div class="vehica-address">
          <span>Gloucester</span>
        </div>
        <div class="vehica-car-gallery">
          <img src="https://example.org/pup.jpg" />
        </div>
        """
        c = CotswoldsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        assert dogs[0].name == "Pup"
        assert dogs[0].location == "Gloucester"
        assert dogs[0].photo_url == "https://example.org/pup.jpg"

    def test_multiple_cards_mixed(self, tmp_path):
        """Only female under 12 months should pass."""
        listing_html = """
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/rex/" title="Rex">Rex</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Male</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/luna/" title="Luna">Luna</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        <div class="vehica-car-card vehica-car vehica-car-card-v2">
          <div class="vehica-car-card__inner">
            <div class="vehica-car-card__content">
              <a class="vehica-car-card__name" href="/animals/daisy/" title="Daisy">Daisy</a>
              <div class="vehica-car-card__info">
                <div class="vehica-car-card__info__single">Available</div>
                <div class="vehica-car-card__info__single">Female</div>
                <div class="vehica-car-card__info__single">Dog</div>
              </div>
            </div>
          </div>
        </div>
        """
        c = CotswoldsChecker(str(tmp_path))

        def mock_fetch(url):
            if "luna" in url:
                return """<div class="vehica-car-attributes">
                  <div class="vehica-car-attributes__name">Age:: 6 months old</div>
                  <div class="vehica-car-attributes__name">Breed:: Spaniel</div>
                </div>
                <div class="vehica-address">
                  <span>Cambridge</span>
                </div>
                <div class="vehica-car-gallery">
                  <img src="https://example.org/luna.jpg" />
                </div>"""
            if "daisy" in url:
                return """<div class="vehica-car-attributes">
                  <div class="vehica-car-attributes__name">Age:: 3 years old</div>
                  <div class="vehica-car-attributes__name">Breed:: Terrier</div>
                </div>
                <div class="vehica-address">
                  <span>Gloucester</span>
                </div>
                <div class="vehica-car-gallery">
                  <img src="https://example.org/daisy.jpg" />
                </div>"""
            return ""

        with patch.object(c, "_fetch_detail_page", side_effect=mock_fetch):
            dogs = c.parse(listing_html)
        # Rex: male -> filtered. Daisy: female but 3y -> filtered.
        # Luna: female, 6 months -> included.
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"
        assert dogs[0].location == "Cambridge"
        assert dogs[0].photo_url == "https://example.org/luna.jpg"
