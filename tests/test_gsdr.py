"""Tests for the German Shepherd Rescue (GSDR) site checker."""

from unittest.mock import patch

from sites.gsdr import GsdrChecker


class TestParseHomepageDogUrls:
    def test_extracts_urgent_dogs(self):
        """Dogs from #owl1 urgent section."""
        from bs4 import BeautifulSoup

        html = """
        <div class="owl-carousel" id="owl1">
          <div><div class="image"><a href="dog1.html"><img/></a></div>
          <div class="name"><a href="rebel-penny-kent-p-6958.html">
            REBEL AND PENNY - KENT</a></div></div>
          <div><div class="image"><a href="dog2.html"><img/></a></div>
          <div class="name"><a href="jazz-sleaford-p-6509.html">Jazz-Sleaford</a></div></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = GsdrChecker._parse_homepage_dog_urls(soup)
        assert len(urls) == 2
        assert urls[0] == ("REBEL AND PENNY - KENT", "rebel-penny-kent-p-6958.html")
        assert urls[1] == ("Jazz-Sleaford", "jazz-sleaford-p-6509.html")

    def test_extracts_featured_dogs(self):
        """Dogs from .box-product section."""
        from bs4 import BeautifulSoup

        html = """
        <div class="box-product">
          <div><div class="image"><a href="dog1.html"><img/></a></div>
          <div class="name"><a href="bruno-sleaford-p-6713.html">Bruno-Sleaford</a></div></div>
          <div><div class="image"><a href="dog2.html"><img/></a></div>
          <div class="name"><a href="fizzy-p-7001.html">Fizzy</a></div></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = GsdrChecker._parse_homepage_dog_urls(soup)
        assert len(urls) == 2
        assert urls[0] == ("Bruno-Sleaford", "bruno-sleaford-p-6713.html")
        assert urls[1] == ("Fizzy", "fizzy-p-7001.html")

    def test_deduplicates_between_sections(self):
        """Dogs appearing in both sections are deduplicated."""
        from bs4 import BeautifulSoup

        html = """
        <div class="owl-carousel" id="owl1">
          <div class="name"><a href="bruno-sleaford-p-6713.html">Bruno-Sleaford</a></div>
        </div>
        <div class="box-product">
          <div class="name"><a href="bruno-sleaford-p-6713.html">Bruno-Sleaford</a></div>
          <div class="name"><a href="fizzy-p-7001.html">Fizzy</a></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = GsdrChecker._parse_homepage_dog_urls(soup)
        assert len(urls) == 2

    def test_no_dogs_returns_empty(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<html></html>", "html.parser")
        assert GsdrChecker._parse_homepage_dog_urls(soup) == []

    def test_missing_urgent_section(self):
        """Only featured section present."""
        from bs4 import BeautifulSoup

        html = """
        <div class="box-product">
          <div class="name"><a href="fizzy-p-7001.html">Fizzy</a></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = GsdrChecker._parse_homepage_dog_urls(soup)
        assert len(urls) == 1


class TestParseDetail:
    def test_extracts_gender_age(self):
        """Detail page with Gender and Age fields."""
        html = """
        <title>Jazz-Sleaford</title>
        <div>
          Gender: Female
          Age: 4
          Color: Black & Tan
          Coat: Long
          Neutered: Yes
          Good with other dogs: Dont Know
          Good with cats: Dont Know
          Good with children: Older children only
        </div>
        <img src="dogimages/Jazz-1.jpg" />
        """
        detail = GsdrChecker._parse_detail(html, "Jazz-Sleaford", "test-url")
        assert detail["name"] == "Jazz-Sleaford"
        assert detail["gender"] == "Female"
        assert detail["age"] == "4"
        assert detail["breed"] == "German Shepherd"
        assert detail["status"] == "Available"
        assert "Jazz-1.jpg" in detail["photo_url"]

    def test_normalizes_age_text(self):
        """Age like '8 YEARS / 10 YEARS' should be lowercased."""
        html = """
        <title>REBEL AND PENNY - KENT</title>
        <div>
          Gender: Male
          Age: 8 YEARS / 10 YEARS
          Color: Black & Tan
          Neutered: Yes
        </div>
        """
        detail = GsdrChecker._parse_detail(html, "REBEL AND PENNY", "test-url")
        assert detail["age"] == "8 years / 10 years"

    def test_fallback_name_when_no_title(self):
        """Uses fallback when title doesn't parse cleanly."""
        html = """
        <title>URGENT! German Shepherd Dog Jazz in Kennels @ GSDR</title>
        <div>
          Gender: Female
          Age: 4
        </div>
        """
        detail = GsdrChecker._parse_detail(html, "Jazz-Sleaford", "test-url")
        # The long title is used as-is since it's under 80 chars
        assert "Jazz" in detail["name"]

    def test_reserved_status_detected(self):
        """Detail page with reserved marker."""
        html = """
        <title>Max-Sleaford</title>
        <div>
          Gender: Male
          Age: 3 years
          <p>This dog is now reserved.</p>
        </div>
        """
        detail = GsdrChecker._parse_detail(html, "Max", "test-url")
        assert detail["status"] == "Reserved"

    def test_photo_from_relative_path(self):
        """Photo src starting with dogimages/ should be made absolute."""
        html = """
        <title>Apollo</title>
        <div>
          Gender: Male
          Age: 2 years
        </div>
        <img src="dogimages/apollo.jpg" />
        """
        detail = GsdrChecker._parse_detail(html, "Apollo", "test-url")
        assert detail["photo_url"] == (
            "https://www.germanshepherdrescue.co.uk/dogimages/apollo.jpg"
        )

    def test_missing_fields_use_empty_strings(self):
        """Minimal detail page."""
        html = """
        <title>Mystery</title>
        """
        detail = GsdrChecker._parse_detail(html, "Mystery", "test-url")
        assert detail["name"] == "Mystery"
        assert detail["gender"] == ""
        assert detail["age"] == ""
        assert detail["breed"] == "German Shepherd"
        assert detail["photo_url"] == ""


class TestParse:
    def test_no_dogs(self, tmp_path):
        c = GsdrChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_available_dog_included(self, tmp_path):
        """Dog from homepage detail should be included."""
        listing_html = """
        <div class="owl-carousel" id="owl1">
          <div class="name"><a href="jazz-sleaford-p-6509.html">Jazz-Sleaford</a></div>
        </div>
        """
        detail_html = """
        <title>Jazz-Sleaford</title>
        <div>
          Gender: Female
          Age: 4
        </div>
        <img src="dogimages/Jazz-1.jpg" />
        """
        c = GsdrChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Jazz-Sleaford"
        assert d.gender == "Female"
        assert d.age == "4"
        assert d.breed == "German Shepherd"
        assert d.status == "Available"
        assert "Jazz-1.jpg" in d.photo_url

    def test_reserved_dog_filtered_out(self, tmp_path):
        """Reserved dogs should be excluded."""
        listing_html = """
        <div class="box-product">
          <div class="name"><a href="max-p-6688.html">Max-Sleaford</a></div>
        </div>
        """
        detail_html = """
        <title>Max-Sleaford</title>
        <div>
          Gender: Male
          Age: 3 years
          <p>This dog is reserved.</p>
        </div>
        """
        c = GsdrChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert dogs == []

    def test_deduplication_in_parse(self, tmp_path):
        """Dogs appearing in both sections appear once."""
        listing_html = """
        <div class="owl-carousel" id="owl1">
          <div class="name"><a href="keira-p-7041.html">Keira - Warwickshire</a></div>
        </div>
        <div class="box-product">
          <div class="name"><a href="keira-p-7041.html">Keira - Warwickshire</a></div>
          <div class="name"><a href="fizzy-p-7001.html">Fizzy</a></div>
        </div>
        """
        detail_keira = """
        <title>Keira - Warwickshire</title>
        <div>Gender: Female\nAge: 5 years</div>
        """
        detail_fizzy = """
        <title>Fizzy</title>
        <div>Gender: Female\nAge: 6 years</div>
        """

        def mock_fetch(url):
            if "keira" in url:
                return detail_keira
            if "fizzy" in url:
                return detail_fizzy
            return ""

        c = GsdrChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", side_effect=mock_fetch):
            dogs = c.parse(listing_html)
        assert len(dogs) == 2
        names = {d.name for d in dogs}
        assert names == {"Keira", "Fizzy"}
