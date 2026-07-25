"""Tests for Paws2Rescue site checker."""

from bs4 import BeautifulSoup

from sites.paws2rescue import Paws2RescueChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestHelpers:
    def test_text(self):
        assert Paws2RescueChecker._text(soup("<div><h3>Rover</h3></div>"), "h3") == "Rover"

    def test_text_missing(self):
        assert Paws2RescueChecker._text(soup("<div></div>"), "h3") == ""

    def test_parse_age_months(self):
        assert Paws2RescueChecker._age_months("7 Months") == 7
        assert Paws2RescueChecker._age_months("1 Month") == 1
        assert Paws2RescueChecker._age_months("12 Months") == 12

    def test_parse_age_years_to_months(self):
        assert Paws2RescueChecker._age_months("1 Year") == 12
        assert Paws2RescueChecker._age_months("2 Years") == 24

    def test_parse_age_with_approx(self):
        assert Paws2RescueChecker._age_months("approx. 7 Months old") == 7
        assert Paws2RescueChecker._age_months("approx. 2 Years old") == 24

    def test_parse_age_unparseable(self):
        assert Paws2RescueChecker._age_months("") == 999
        assert Paws2RescueChecker._age_months("Senior") == 999

    def test_extract_detail_field(self):
        html = "<p>Name: Bella</p>"
        assert Paws2RescueChecker._extract_detail_field(soup(html), "Name") == "Bella"

    def test_extract_detail_field_missing(self):
        html = "<p>Gender: Female</p>"
        assert Paws2RescueChecker._extract_detail_field(soup(html), "Name") == ""

    def test_extract_age_from_detail(self):
        html = "<p>Age: approx. 7 Months old</p>"
        assert Paws2RescueChecker._extract_detail_field(soup(html), "Age") == "approx. 7 Months old"

    def test_extract_breed_from_detail(self):
        # Most dogs don't have a breed field; scraper returns empty string
        html = "<p>Name: Olive</p><p>Age: 7 Months</p>"
        assert Paws2RescueChecker._extract_detail_field(soup(html), "Breed") == ""

    def test_extract_detail_field_with_unicode_bold(self):
        """Detail pages use mathematical bold Unicode characters."""
        # 𝗡𝗮𝗺𝗲: Bella (mathematical bold)
        bold_name = "\U0001d5e1\U0001d5ee\U0001d5fa\U0001d5f2"
        html = f"<p>{bold_name}: Bella</p>"
        result = Paws2RescueChecker._extract_detail_field(soup(html), "Name")
        assert result == "Bella"

    def test_location_fallback(self):
        """When API _embed is unavailable, _parse_location_names should handle
        raw term ID lists gracefully (returns empty string)."""
        names = Paws2RescueChecker._parse_location_names({}, [15])
        assert names == ""

    def test_parse_sex_name(self):
        names = Paws2RescueChecker._parse_term_names({}, "sex", [17])
        # Without _embed, returns empty string
        assert names == ""


class TestParse:
    def test_empty(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        assert c.parse("[]") == []

    def test_parses_api_dog(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        # Simulate an API response item with _embed
        dog_data = {
            "title": {"rendered": "Bella (Cat Friendly)"},
            "link": "https://paws2rescue.com/dog/bella/",
            "_embedded": {
                "wp:term": [
                    [{"taxonomy": "sex", "name": "Good Girl", "id": 17, "slug": "female"}],
                    [{"taxonomy": "size", "name": "Small", "id": 18, "slug": "small"}],
                    [{"taxonomy": "location", "name": "Romania", "id": 15, "slug": "romania"}],
                ]
            },
        }
        result = c._parse_single(dog_data)
        assert result is not None
        assert result.name == "Bella (Cat Friendly)"
        assert result.gender == "Female"
        assert result.location == "Romania"
        assert result.url == "https://paws2rescue.com/dog/bella/"

    def test_filters_male_dogs(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Rex"},
            "link": "https://paws2rescue.com/dog/rex/",
            "_embedded": {
                "wp:term": [
                    [{"taxonomy": "sex", "name": "Good Boy", "id": 16, "slug": "male"}],
                    [{"taxonomy": "size", "name": "Small", "id": 18, "slug": "small"}],
                    [{"taxonomy": "location", "name": "Romania", "id": 15, "slug": "romania"}],
                ]
            },
        }
        # _parse_single returns male dogs (filtering happens in check())
        result = c._parse_single(dog_data)
        assert result is not None
        assert result.gender == "Male"

    def test_filters_to_age_12_months_or_under(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        # Age filtering happens in check() via _age_months
        assert c._age_months("7 Months") <= 12
        assert c._age_months("2 Years") > 12

    def test_multiple_sizes(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Yasya"},
            "link": "https://paws2rescue.com/dog/yasya/",
            "_embedded": {
                "wp:term": [
                    [{"taxonomy": "sex", "name": "Good Girl", "id": 17, "slug": "female"}],
                    [
                        {
                            "taxonomy": "size",
                            "name": "Small to Medium",
                            "id": 30,
                            "slug": "small-to-medium",
                        },
                        {
                            "taxonomy": "size",
                            "name": "Medium",
                            "id": 19,
                            "slug": "medium",
                        },
                    ],
                    [{"taxonomy": "location", "name": "Scotland", "id": 33, "slug": "scotland"}],
                ]
            },
        }
        result = c._parse_single(dog_data)
        assert result is not None
        # Should contain all size names joined
        assert "Small to Medium" in result.status
        assert "Medium" in result.status

    def test_parse_detail_page(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        html = "<html><body><p>Name: Olive</p><p>Age: approx. 7 Months old</p></body></html>"
        age, breed, photo_url = c._parse_detail(html)
        assert age == "approx. 7 Months old"
        assert breed == ""
        assert photo_url == ""

    def test_parse_detail_page_with_breed(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        html = (
            "<html><body>"
            "<p>Name: Lola</p>"
            "<p>Age: approx. 6 Months old</p>"
            "<p>Breed: Shepherd Mix</p>"
            "</body></html>"
        )
        age, breed, photo_url = c._parse_detail(html)
        assert age == "approx. 6 Months old"
        assert breed == "Shepherd Mix"
        assert photo_url == ""


class TestStatusFiltering:
    """Reserved / not-available dogs should be filtered out."""

    def test_skips_reserved_dog(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Toto (Cat Friendly)   Reserved"},
            "link": "https://paws2rescue.com/dog/toto/",
        }
        result = c._parse_single(dog_data)
        assert result is None

    def test_skips_soon_available_dog(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Dougal (Cat Friendly)   Soon Available"},
            "link": "https://paws2rescue.com/dog/dougal/",
        }
        result = c._parse_single(dog_data)
        assert result is None

    def test_skips_available_soon_dog(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Olive (Cat Friendly)   Available Soon"},
            "link": "https://paws2rescue.com/dog/olive/",
        }
        result = c._parse_single(dog_data)
        assert result is None

    def test_keeps_available_dog_with_senior_suffix(self, tmp_path):
        """(Senior) suffix is an age indicator, not a status — keep it."""
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Luna   (Senior)"},
            "link": "https://paws2rescue.com/dog/luna/",
        }
        result = c._parse_single(dog_data)
        assert result is not None
        assert result.name == "Luna   (Senior)"

    def test_keeps_available_dog_no_suffix(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Bella (Cat Friendly)"},
            "link": "https://paws2rescue.com/dog/bella/",
        }
        result = c._parse_single(dog_data)
        assert result is not None
        assert result.name == "Bella (Cat Friendly)"


class TestPhotoUrl:
    def test_extracts_from_listing_card_api_data(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Bella"},
            "link": "https://paws2rescue.com/dog/bella/",
            "_embedded": {
                "wp:term": [
                    [{"taxonomy": "sex", "name": "Good Girl", "id": 17, "slug": "female"}],
                    [{"taxonomy": "size", "name": "Small", "id": 18, "slug": "small"}],
                    [{"taxonomy": "location", "name": "Romania", "id": 15, "slug": "romania"}],
                ]
            },
        }
        result = c._parse_single(dog_data)
        assert result is not None
        assert result.photo_url == ""

    def test_extracts_from_featured_media(self, tmp_path):
        c = Paws2RescueChecker(str(tmp_path))
        dog_data = {
            "title": {"rendered": "Bella"},
            "link": "https://paws2rescue.com/dog/bella/",
            "_embedded": {
                "wp:term": [
                    [{"taxonomy": "sex", "name": "Good Girl", "id": 17, "slug": "female"}],
                    [{"taxonomy": "size", "name": "Small", "id": 18, "slug": "small"}],
                    [{"taxonomy": "location", "name": "Romania", "id": 15, "slug": "romania"}],
                ],
                "wp:featuredmedia": [
                    {"source_url": "https://paws2rescue.com/wp-content/uploads/2026/04/olive.jpg"}
                ],
            },
        }
        result = c._parse_single(dog_data)
        assert result is not None
        assert result.photo_url == "https://paws2rescue.com/wp-content/uploads/2026/04/olive.jpg"
