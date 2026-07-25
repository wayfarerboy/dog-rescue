"""Tests for the Teckels Animal Sanctuaries site checker."""

from unittest.mock import patch

from sites.teckels import TeckelsChecker


class TestParseDogUrls:
    def test_extracts_dog_links_from_listing(self):
        """h2.elementor-heading-title links to /animals/ should be extracted."""
        from bs4 import BeautifulSoup

        html = """
        <h2 class="elementor-heading-title elementor-size-default">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/pj/">PJ</a>
        </h2>
        <h2 class="elementor-heading-title elementor-size-default">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/hetty/">Hetty</a>
        </h2>
        <h2 class="elementor-heading-title elementor-size-default">Dogs for Adoption</h2>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = TeckelsChecker._parse_dog_urls(soup)
        assert len(urls) == 2
        assert urls[0] == ("PJ", "https://teckelsanimalsanctuaries.co.uk/animals/pj/")
        assert urls[1] == ("Hetty", "https://teckelsanimalsanctuaries.co.uk/animals/hetty/")

    def test_skips_non_animal_links(self):
        """Only /animals/ links are dog URLs."""
        from bs4 import BeautifulSoup

        html = """
        <h2 class="elementor-heading-title elementor-size-default">
            <a href="https://teckelsanimalsanctuaries.co.uk/donate/">Donate</a>
        </h2>
        <h2 class="elementor-heading-title elementor-size-default">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/amber/">Amber</a>
        </h2>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = TeckelsChecker._parse_dog_urls(soup)
        assert len(urls) == 1
        assert urls[0][0] == "Amber"

    def test_no_dogs_returns_empty(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<html></html>", "html.parser")
        assert TeckelsChecker._parse_dog_urls(soup) == []


class TestParseDetail:
    def test_extracts_age_gender_breed(self):
        """Detail page with h2 fields for Age, Gender, Breed."""
        html = """
        <h1 class="elementor-heading-title">PJ</h1>
        <h2 class="elementor-heading-title">Age: 2 years (approx.)</h2>
        <h2 class="elementor-heading-title">Gender: Male</h2>
        <h2 class="elementor-heading-title">Breed: Pug</h2>
        """
        detail = TeckelsChecker._parse_detail(html, "PJ")
        assert detail["name"] == "PJ"
        assert detail["age"] == "2 years (approx.)"
        assert detail["gender"] == "Male"
        assert detail["breed"] == "Pug"
        assert detail["status"] == "Available"

    def test_extracts_name_from_h1(self):
        """H1 heading gives a better name than fallback."""
        html = """
        <h1 class="elementor-heading-title">Rufus</h1>
        <h2 class="elementor-heading-title">Age: 3 years</h2>
        <h2 class="elementor-heading-title">Gender: Male</h2>
        <h2 class="elementor-heading-title">Breed: Terrier</h2>
        """
        detail = TeckelsChecker._parse_detail(html, "fallback")
        assert detail["name"] == "Rufus"

    def test_fallback_name_when_no_h1(self):
        """Uses fallback when no h1 is found."""
        html = """
        <h2 class="elementor-heading-title">Age: 1 year</h2>
        <h2 class="elementor-heading-title">Gender: Female</h2>
        <h2 class="elementor-heading-title">Breed: Spaniel</h2>
        """
        detail = TeckelsChecker._parse_detail(html, "FallbackName")
        assert detail["name"] == "FallbackName"

    def test_detects_reserved_status(self):
        """Dogs marked as reserved should have status 'Reserved'."""
        html = """
        <h1 class="elementor-heading-title">Buddy</h1>
        <h2 class="elementor-heading-title">Age: 5 years</h2>
        <h2 class="elementor-heading-title">Gender: Male</h2>
        <h2 class="elementor-heading-title">Breed: Labrador</h2>
        <p>Buddy is reserved pending home check.</p>
        """
        detail = TeckelsChecker._parse_detail(html, "Buddy")
        assert detail["status"] == "Reserved"

    def test_extracts_photo_from_jsonld(self):
        """Photo URL comes from JSON-LD thumbnailUrl."""
        html = """
        <h1 class="elementor-heading-title">Luna</h1>
        <h2 class="elementor-heading-title">Age: 1 year</h2>
        <h2 class="elementor-heading-title">Gender: Female</h2>
        <h2 class="elementor-heading-title">Breed: Spaniel</h2>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@graph":[
          {"@type":"WebPage","thumbnailUrl":"https://teckels.example.org/uploads/dog.jpg"}
        ]}
        </script>
        """
        detail = TeckelsChecker._parse_detail(html, "Luna")
        assert detail["photo_url"] == "https://teckels.example.org/uploads/dog.jpg"

    def test_missing_fields_use_empty_strings(self):
        """Missing optional fields should be empty strings."""
        html = """
        <h1 class="elementor-heading-title">Ghost</h1>
        """
        detail = TeckelsChecker._parse_detail(html, "Ghost")
        assert detail["name"] == "Ghost"
        assert detail["age"] == ""
        assert detail["gender"] == ""
        assert detail["breed"] == ""
        assert detail["status"] == "Available"
        assert detail["photo_url"] == ""


class TestParse:
    def test_no_dogs(self, tmp_path):
        c = TeckelsChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_reserved_dog_filtered_out(self, tmp_path):
        """Reserved dogs should be excluded from parse output."""
        listing_html = """
        <h2 class="elementor-heading-title">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/buddy/">Buddy</a>
        </h2>
        """
        detail_html = """
        <h1 class="elementor-heading-title">Buddy</h1>
        <h2 class="elementor-heading-title">Age: 5 years</h2>
        <h2 class="elementor-heading-title">Gender: Male</h2>
        <h2 class="elementor-heading-title">Breed: Labrador</h2>
        <p>Buddy is reserved pending home check.</p>
        """
        c = TeckelsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert dogs == []

    def test_available_dog_included(self, tmp_path):
        """Available dogs should be included."""
        listing_html = """
        <h2 class="elementor-heading-title">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/pj/">PJ</a>
        </h2>
        """
        detail_html = """
        <h1 class="elementor-heading-title">PJ</h1>
        <h2 class="elementor-heading-title">Age: 2 years (approx.)</h2>
        <h2 class="elementor-heading-title">Gender: Male</h2>
        <h2 class="elementor-heading-title">Breed: Pug</h2>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@graph":[
          {"@type":"WebPage","thumbnailUrl":"https://teckels.example.org/uploads/pj.jpg"}
        ]}
        </script>
        """
        c = TeckelsChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "PJ"
        assert d.age == "2 years (approx.)"
        assert d.gender == "Male"
        assert d.breed == "Pug"
        assert d.status == "Available"
        assert d.photo_url == "https://teckels.example.org/uploads/pj.jpg"
        assert d.url == "https://teckelsanimalsanctuaries.co.uk/animals/pj/"
        assert d.location == "Teckels Animal Sanctuaries, Whitminster, Gloucester GL2 7PR"

    def test_multiple_dogs(self, tmp_path):
        """Multiple dogs — all available ones included, reserved skipped."""
        listing_html = """
        <h2 class="elementor-heading-title">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/pj/">PJ</a>
        </h2>
        <h2 class="elementor-heading-title">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/hetty/">Hetty</a>
        </h2>
        <h2 class="elementor-heading-title">
            <a href="https://teckelsanimalsanctuaries.co.uk/animals/buddy/">Buddy</a>
        </h2>
        """
        c = TeckelsChecker(str(tmp_path))

        def mock_fetch(url):
            if "buddy" in url:
                return """<h1 class="elementor-heading-title">Buddy</h1>
                <h2 class="elementor-heading-title">Age: 5 years</h2>
                <h2 class="elementor-heading-title">Gender: Male</h2>
                <h2 class="elementor-heading-title">Breed: Labrador</h2>
                <p>Reserved</p>"""
            if "pj" in url:
                return """<h1 class="elementor-heading-title">PJ</h1>
                <h2 class="elementor-heading-title">Age: 2 years</h2>
                <h2 class="elementor-heading-title">Gender: Male</h2>
                <h2 class="elementor-heading-title">Breed: Pug</h2>"""
            if "hetty" in url:
                return """<h1 class="elementor-heading-title">Hetty</h1>
                <h2 class="elementor-heading-title">Age: 8 years</h2>
                <h2 class="elementor-heading-title">Gender: Female</h2>
                <h2 class="elementor-heading-title">Breed: Cocker Spaniel</h2>"""
            return ""

        with patch.object(c, "_fetch_detail", side_effect=mock_fetch):
            dogs = c.parse(listing_html)
        assert len(dogs) == 2
        names = {d.name for d in dogs}
        assert names == {"PJ", "Hetty"}
