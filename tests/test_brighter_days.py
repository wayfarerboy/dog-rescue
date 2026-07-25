"""Tests for the Brighter Days Rescue site checker."""

from unittest.mock import patch

from sites.brighter_days import BrighterDaysChecker


class TestParseListingCards:
    def test_extracts_available_card(self):
        """Extract name, gender, age, status, url, photo_url from an available card."""
        html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a style="display:block" href="/dogs/anza">
            <div class="css-eufbxh">
              <img src="/_next/image?url=photo.jpg" alt="Anza" />
              <p class="css-d41hrg">Find out more about Anza</p>
            </div>
            <div class="css-iutleh"><p class="css-1ny3018">Anza</p></div>
            <p class="css-1x3xbk5">Female, 6 years</p>
          </a>
        </div>
        """
        cards = BrighterDaysChecker._parse_listing_cards(html)
        assert len(cards) == 1
        c = cards[0]
        assert c["name"] == "Anza"
        assert c["gender"] == "Female"
        assert c["age"] == "6 years"
        assert c["status"] == "Available"
        assert c["url"] == "https://brighterdaysrescue.com/dogs/anza"
        assert c["photo_url"] == "https://brighterdaysrescue.com/_next/image?url=photo.jpg"

    def test_extracts_male_card(self):
        """Male dog should also be included (checker returns all non-reserved)."""
        html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a style="display:block" href="/dogs/jack-qass">
            <img src="/_next/image?url=jack.jpg" alt="Jack" />
            <div class="css-iutleh"><p class="css-1ny3018">Jack</p></div>
            <p class="css-1x3xbk5">Male, 4 months</p>
          </a>
        </div>
        """
        cards = BrighterDaysChecker._parse_listing_cards(html)
        assert len(cards) == 1
        assert cards[0]["name"] == "Jack"
        assert cards[0]["gender"] == "Male"
        assert cards[0]["age"] == "4 months"

    def test_filters_reserved_cards(self):
        """Cards with 'Reserved' badge are excluded from results."""
        html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/storm">
            <img alt="Storm" />
            <div class="css-mqy1sm">Reserved</div>
            <p class="css-mmocuf">Reserved</p>
            <div class="css-iutleh"><p class="css-1ny3018">Storm</p></div>
            <p class="css-1x3xbk5">Female, 5 months</p>
          </a>
        </div>
        """
        cards = BrighterDaysChecker._parse_listing_cards(html)
        assert len(cards) == 0

    def test_mixed_available_and_reserved(self):
        """Only Available cards are returned; Reserved cards are skipped."""
        html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/anza">
            <img alt="Anza" />
            <p class="css-1ny3018">Anza</p>
            <p class="css-1x3xbk5">Female, 6 years</p>
          </a>
        </div>
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/storm">
            <img alt="Storm" />
            <div class="css-mqy1sm">Reserved</div>
            <div class="css-iutleh"><p class="css-1ny3018">Storm</p></div>
            <p class="css-1x3xbk5">Female, 5 months</p>
          </a>
        </div>
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/jack-qass">
            <img alt="Jack" />
            <p class="css-1ny3018">Jack</p>
            <p class="css-1x3xbk5">Male, 4 months</p>
          </a>
        </div>
        """
        cards = BrighterDaysChecker._parse_listing_cards(html)
        assert len(cards) == 2
        assert cards[0]["name"] == "Anza"
        assert cards[1]["name"] == "Jack"

    def test_no_cards(self):
        """Empty listing page returns no cards."""
        assert BrighterDaysChecker._parse_listing_cards("<html></html>") == []

    def test_relative_url_prefixed(self):
        """Relative /dogs/* URLs are prefixed with BASE_URL."""
        html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/bella-gvow">
            <p class="css-1ny3018">Bella</p>
            <p class="css-1x3xbk5">Female, 7 months</p>
          </a>
        </div>
        """
        cards = BrighterDaysChecker._parse_listing_cards(html)
        assert cards[0]["url"] == "https://brighterdaysrescue.com/dogs/bella-gvow"


class TestParseDetailPage:
    def test_extracts_breed(self):
        """Breed is extracted from the first <p> after <h1>."""
        html = """
        <h1 class="chakra-heading css-11m8g5r">Anza</h1>
        <p class="css-5ub73f">German Shepherd</p>
        <div class="css-n8hj4z">
          <div>SexFemale</div>
        </div>
        <div class="css-wdemyf">Available at our kennels based in Penkridge.</div>
        """
        breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert breed == "German Shepherd"
        assert location == "Penkridge, Staffs"

    def test_breed_missing(self):
        """No <p> after <h1> means empty breed."""
        html = """
        <h1 class="chakra-heading">Ghost</h1>
        <div class="css-wdemyf">Some description.</div>
        """
        breed, _location = BrighterDaysChecker._parse_detail_page(html)
        assert breed == ""

    def test_breed_with_cross(self):
        """Breed containing 'Cross' is captured."""
        html = """
        <h1 class="chakra-heading">Albie</h1>
        <p class="css-5ub73u">German Shepherd Cross</p>
        <div class="css-wdemyf">Available at our rescue based in Penkridge.</div>
        """
        breed, _location = BrighterDaysChecker._parse_detail_page(html)
        assert breed == "German Shepherd Cross"

    def test_uk_location(self):
        """UK dog (no 'Rescued from' or UK origin) gets base location."""
        html = """
        <h1 class="chakra-heading">Rover</h1>
        <p>Labrador</p>
        <div class="css-wdemyf">Available at our kennels based in Penkridge.
        Meet Rover! Good boy.</div>
        """
        breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert breed == "Labrador"
        assert location == "Penkridge, Staffs"

    def test_international_origin(self):
        """Dog rescued from abroad has origin annotated in location."""
        html = """
        <h1 class="chakra-heading">Jack</h1>
        <p>Unknown</p>
        <div class="css-wdemyf">Available at our rescue based in Penkridge.

        Meet Jack!

        - Rescued from Bosnia
        - Fully vaccinated
        - Microchipped</div>
        """
        breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert breed == "Unknown"
        assert location == "Penkridge, Staffs (origin: Bosnia)"

    def test_romania_origin(self):
        """Dog from Romania."""
        html = """
        <h1 class="chakra-heading">Teddy</h1>
        <p>Unknown</p>
        <div class="css-wdemyf">Available at our rescue based in Penkridge.

        Meet Teddy!

        - Rescued from Romania
        - Fully vaccinated</div>
        """
        _breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert location == "Penkridge, Staffs (origin: Romania)"

    def test_bulgaria_origin(self):
        """Dog from Bulgaria."""
        html = """
        <h1 class="chakra-heading">Bella</h1>
        <p>Mix</p>
        <div class="css-wdemyf">Available at our rescue based in Penkridge.

        Meet Bella!

        - Rescued from Bulgaria
        - Microchipped</div>
        """
        _breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert location == "Penkridge, Staffs (origin: Bulgaria)"

    def test_spain_origin(self):
        """Dog from Spain."""
        html = """
        <h1 class="chakra-heading">Pablo</h1>
        <p>Podengo</p>
        <div class="css-wdemyf">Available at our rescue based in Penkridge.

        - Rescued from Spain
        - Vaccinated</div>
        """
        _breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert location == "Penkridge, Staffs (origin: Spain)"

    def test_missing_description(self):
        """No description div defaults to base location."""
        html = """
        <h1 class="chakra-heading">Mystery</h1>
        <p>Unknown</p>
        """
        breed, location = BrighterDaysChecker._parse_detail_page(html)
        assert breed == "Unknown"
        assert location == "Penkridge, Staffs"


class TestParse:
    def test_no_cards(self, tmp_path):
        c = BrighterDaysChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_available_dog_with_detail(self, tmp_path):
        """Available dog with detail fetch returns full Dog object."""
        listing_html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/anza">
            <img src="https://cdn.example.com/anza.jpg" alt="Anza" />
            <div class="css-iutleh"><p class="css-1ny3018">Anza</p></div>
            <p class="css-1x3xbk5">Female, 6 years</p>
          </a>
        </div>
        """
        detail_html = """
        <h1 class="chakra-heading">Anza</h1>
        <p>German Shepherd</p>
        <div class="css-wdemyf">Available at our kennels based in Penkridge.

        Meet Anza!

        - Rescued from Bosnia</div>
        """
        c = BrighterDaysChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Anza"
        assert d.gender == "Female"
        assert d.age == "6 years"
        assert d.breed == "German Shepherd"
        assert d.url == "https://brighterdaysrescue.com/dogs/anza"
        assert d.status == "Available"
        assert d.location == "Penkridge, Staffs (origin: Bosnia)"
        assert d.photo_url == "https://cdn.example.com/anza.jpg"

    def test_reserved_dog_skipped(self, tmp_path):
        """Reserved dogs should not be included in output."""
        listing_html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/storm">
            <img alt="Storm" />
            <div class="css-mqy1sm">Reserved</div>
            <div class="css-iutleh"><p class="css-1ny3018">Storm</p></div>
            <p class="css-1x3xbk5">Female, 5 months</p>
          </a>
        </div>
        """
        c = BrighterDaysChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail_page") as mock_fetch:
            dogs = c.parse(listing_html)
            mock_fetch.assert_not_called()
        assert dogs == []

    def test_multiple_mixed_status(self, tmp_path):
        """Only Available dogs returned; Reserved filtered out."""
        listing_html = """
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/anza">
            <p class="css-1ny3018">Anza</p>
            <p class="css-1x3xbk5">Female, 6 years</p>
          </a>
        </div>
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/storm">
            <div class="css-mqy1sm">Reserved</div>
            <p class="css-1ny3018">Storm</p>
            <p class="css-1x3xbk5">Female, 5 months</p>
          </a>
        </div>
        <div data-dog-card="true" class="css-4g0e4j">
          <a href="/dogs/jack-qass">
            <p class="css-1ny3018">Jack</p>
            <p class="css-1x3xbk5">Male, 4 months</p>
          </a>
        </div>
        """
        c = BrighterDaysChecker(str(tmp_path))

        def mock_fetch(url):
            if "anza" in url:
                return (
                    '<h1 class="chakra-heading">Anza</h1>'
                    '<p>German Shepherd</p>'
                    '<div class="css-wdemyf">Available at kennels'
                    ' based in Penkridge. - Rescued from Bosnia</div>'
                )
            if "jack" in url:
                return (
                    '<h1 class="chakra-heading">Jack</h1>'
                    '<p>Unknown</p>'
                    '<div class="css-wdemyf">Available at rescue'
                    ' based in Penkridge. - Rescued from Bosnia</div>'
                )
            return ""

        with patch.object(c, "_fetch_detail_page", side_effect=mock_fetch):
            dogs = c.parse(listing_html)
        assert len(dogs) == 2
        assert dogs[0].name == "Anza"
        assert dogs[1].name == "Jack"
