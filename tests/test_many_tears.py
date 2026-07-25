from unittest.mock import patch

from sites.many_tears import ManyTearsChecker

# Reusable detail page HTML for tests that just need a valid status
_DETAIL_AVAILABLE = (
    "<html><li class='status'>Available for Adoption</li></html>"
)
_DETAIL_RESERVED = "<html><li class='status'>Reserved</li></html>"
_DETAIL_HOME_FOUND = "<html><li class='status'>Home Found</li></html>"


class TestTextHelper:
    def test_extracts_text(self):
        html = "<div><span class='icon breed'>Cocker Spaniel</span></div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        assert ManyTearsChecker._text(soup, ".icon.breed") == "Cocker Spaniel"

    def test_missing_selector_returns_empty(self):
        html = "<div></div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        assert ManyTearsChecker._text(soup, ".nope") == ""


class TestParse:
    def test_no_cards(self, tmp_path):
        c = ManyTearsChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_single_card(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/bella">
          <h3>Bella</h3>
          <div class="icon breed">Cocker Spaniel</div>
          <div class="icon age">6 Months</div>
          <div class="icon sex">Female</div>
          <div class="icon location">Carmarthen</div>
        </a>
        """
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=_DETAIL_AVAILABLE):
            dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Bella"
        assert d.breed == "Cocker Spaniel"
        assert d.age == "6 Months"
        assert d.gender == "Female"
        assert d.location == "Carmarthen"
        assert d.url == "https://www.manytearsrescue.org/dogs/bella"
        assert d.status == "Available for Adoption"

    def test_card_missing_href_skipped(self, tmp_path):
        html = '<a class="animal-card"><h3>Ghost</h3></a>'
        c = ManyTearsChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_multiple_cards(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/a"><h3>A</h3></a>
        <a class="animal-card" href="/dogs/b"><h3>B</h3></a>
        """
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(
            c, "_fetch_detail_page", return_value=_DETAIL_AVAILABLE
        ):
            dogs = c.parse(html)
        assert len(dogs) == 2

    def test_missing_optional_fields(self, tmp_path):
        html = '<a class="animal-card" href="/dogs/min"><h3>Min</h3></a>'
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=_DETAIL_AVAILABLE):
            dogs = c.parse(html)
        assert dogs[0].breed == ""
        assert dogs[0].age == ""


class TestExtractFromProfile:
    def test_extracts_status_available(self):
        html = "<html><li class='status'>Available for Adoption</li></html>"
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result["status"] == "Available for Adoption"

    def test_extracts_status_reserved(self):
        html = "<html><div>Reserved</div></html>"
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result["status"] == "Reserved"

    def test_extracts_status_home_found(self):
        html = "<html><span>Home Found</span></html>"
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result["status"] == "Home Found"

    def test_extracts_status_foster(self):
        html = "<html><p>Foster</p></html>"
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result["status"] == "Foster"

    def test_extracts_photo_url(self):
        html = (
            '<html><meta property="og:image" '
            'content="/media/dog.jpg.1500x1000_q80.jpg" />'
            "</html>"
        )
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result["photo_url"] == (
            "https://www.manytearsrescue.org"
            "/media/dog.jpg.1500x1000_q80.jpg"
        )

    def test_no_status_returns_empty(self):
        html = "<html><body>Just a dog page</body></html>"
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result == {}

    def test_no_photo_returns_status_only(self):
        html = "<html>Available for Adoption</html>"
        c = ManyTearsChecker("/tmp")
        result = c.extract_from_profile(html)
        assert result == {"status": "Available for Adoption"}


class TestStatusFiltering:
    """Test that reserved and home-found dogs are filtered out of parse()."""

    def test_reserved_dog_filtered_out(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/reserved-dog">
          <h3>Rover</h3>
        </a>
        """
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=_DETAIL_RESERVED):
            dogs = c.parse(html)
        assert dogs == []

    def test_home_found_dog_filtered_out(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/home-dog">
          <h3>Lucky</h3>
        </a>
        """
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=_DETAIL_HOME_FOUND):
            dogs = c.parse(html)
        assert dogs == []

    def test_available_dog_kept(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/good-dog">
          <h3>Bella</h3>
        </a>
        """
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=_DETAIL_AVAILABLE):
            dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Bella"
        assert dogs[0].status == "Available for Adoption"

    def test_mixed_available_and_reserved(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/available1">
          <h3>Available Dog</h3>
        </a>
        <a class="animal-card" href="/dogs/reserved1">
          <h3>Reserved Dog</h3>
        </a>
        <a class="animal-card" href="/dogs/available2">
          <h3>Another Available</h3>
        </a>
        """
        c = ManyTearsChecker(str(tmp_path))

        def mock_fetch(url):
            if "reserved" in url:
                return _DETAIL_RESERVED
            return _DETAIL_AVAILABLE

        with patch.object(c, "_fetch_detail_page", side_effect=mock_fetch):
            dogs = c.parse(html)
        assert len(dogs) == 2
        assert dogs[0].name == "Available Dog"
        assert dogs[1].name == "Another Available"


class TestAllFieldsFilled:
    """Test that all 8 Dog fields are populated from listing + detail page."""

    def test_all_eight_fields_filled(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/complete">
          <div class="animal-card__image"
            style="background-image: url('/media/dog.jpg.450x450.jpg')">
          </div>
          <h3>Lady</h3>
          <div class="icon breed">Cocker Spaniel</div>
          <div class="icon age">5 Months</div>
          <div class="icon sex">Female</div>
          <div class="icon location">Carmarthen</div>
        </a>
        """
        detail_html = "<html><li class='status'>Available for Adoption</li></html>"
        c = ManyTearsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=detail_html):
            dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.status == "Available for Adoption"
        assert d.name == "Lady"
        assert d.age == "5 Months"
        assert d.gender == "Female"
        assert d.breed == "Cocker Spaniel"
        assert d.location == "Carmarthen"
        assert d.photo_url == (
            "https://www.manytearsrescue.org"
            "/media/dog.jpg.450x450.jpg"
        )
        assert d.url == "https://www.manytearsrescue.org/dogs/complete"
