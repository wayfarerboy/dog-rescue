"""Tests for the Wythall Animal Sanctuary site checker."""

from unittest.mock import patch

from sites.wythall import WythallChecker


class TestParseDogUrls:
    def test_extracts_grid_item_links(self):
        """a.grid-item links to /dogs/ should be extracted."""
        from bs4 import BeautifulSoup

        html = """
        <a class="grid-item" href="/dogs/cherry">Cherry</a>
        <a class="grid-item" href="/dogs/crumpet">Crumpet</a>
        <a href="/animal-foster">Foster</a>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = WythallChecker._parse_dog_urls(soup)
        assert len(urls) == 2
        assert urls[0][0] == "Cherry"
        assert urls[0][1] == "https://www.wythallanimalsanctuary.org/dogs/cherry"
        assert urls[1][0] == "Crumpet"
        assert urls[1][1] == "https://www.wythallanimalsanctuary.org/dogs/crumpet"

    def test_no_dogs_returns_empty(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<html></html>", "html.parser")
        assert WythallChecker._parse_dog_urls(soup) == []

    def test_deduplicates_by_url(self):
        """Duplicate URLs should be deduplicated."""
        from bs4 import BeautifulSoup

        html = """
        <a class="grid-item" href="/dogs/cherry">Cherry</a>
        <a class="grid-item" href="/dogs/cherry">Cherry</a>
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = WythallChecker._parse_dog_urls(soup)
        assert len(urls) == 1


class TestParseDetail:
    def test_extracts_breed_sex_age(self):
        """Detail page with 'Label - Value' format in More About Me."""
        html = """
        <title>Crumpet — Wythall Animal Sanctuary</title>
        <h1>Hi, I'm Crumpet</h1>
        <div>
          Breed -Presa X Mastiff Crossbreed
          Size - Large
          Sex - Male
          Age - 4 years
          Colour - Tan & Black Brindle
          Live with children - Adult Only
          Live with other dogs - Medium size friendly female dog
          Live with cats / small animals - No
          Adoption fee - £250
        </div>
        """
        detail = WythallChecker._parse_detail(html, "Crumpet")
        assert detail["name"] == "Crumpet"
        assert detail["breed"] == "Presa X Mastiff Crossbreed"
        assert detail["gender"] == "Male"
        assert detail["age"] == "4 years"
        assert detail["status"] == "Available"

    def test_detects_foster_status(self):
        """Dogs looking for foster-only should have status 'Foster'."""
        html = """
        <title>Cherry - Foster Me <3 — Wythall Animal Sanctuary</title>
        <h1>Hi, I'm Cherry</h1>
        <div>
          I'm looking for a quiet loving foster home <3
          Breed - Bulldog
          Size - Small - Medium
          Sex - Female
          Age - 4 years
          Adoption fee - I am looking for a foster home
        </div>
        """
        detail = WythallChecker._parse_detail(html, "Cherry")
        assert detail["name"] == "Cherry"
        assert detail["breed"] == "Bulldog"
        assert detail["gender"] == "Female"
        assert detail["age"] == "4 years"
        assert detail["status"] == "Foster"

    def test_available_dog_with_adoption_fee(self):
        """A dog with an adoption fee is available for adoption."""
        html = """
        <title>Reggie — Wythall Animal Sanctuary</title>
        <div>
          I'm looking for my forever home
          Breed - Terrier
          Sex - Male
          Age - 2 years
          Adoption fee - £200
        </div>
        """
        detail = WythallChecker._parse_detail(html, "Reggie")
        assert detail["status"] == "Available"

    def test_name_from_title(self):
        """Name extracted from page title even without h1."""
        html = """
        <title>Ronnie — Wythall Animal Sanctuary</title>
        <div>
          Breed - Staffie
          Sex - Male
          Age - 3 years
        </div>
        """
        detail = WythallChecker._parse_detail(html, "fallback")
        assert detail["name"] == "Ronnie"

    def test_fallback_name_with_em_dash(self):
        """Title with em-dash separator."""
        html = """
        <title>Eddie \u2014 Wythall Animal Sanctuary</title>
        <div>
          Breed - Lurcher
          Sex - Male
          Age - 1 year
        </div>
        """
        detail = WythallChecker._parse_detail(html, "fallback")
        assert detail["name"] == "Eddie"

    def test_missing_fields_use_empty_strings(self):
        """Minimal detail page with no structured data."""
        html = """
        <title>Mystery Dog — Wythall Animal Sanctuary</title>
        """
        detail = WythallChecker._parse_detail(html, "Mystery")
        assert detail["name"] == "Mystery Dog"
        assert detail["breed"] == ""
        assert detail["gender"] == ""
        assert detail["age"] == ""

    def test_extracts_from_strong_tags(self):
        """Real Wythall pages use <strong> tags inside <li> elements."""
        html = """
        <title>Crumpet \u2014 Wythall Animal Sanctuary</title>
        <h3>More About Me</h3>
        <ul>
          <li><p><strong>Breed</strong> -Presa X Mastiff Crossbreed</p></li>
          <li><p><strong>Size</strong> - Large</p></li>
          <li><p><strong>Sex -</strong> Male</p></li>
          <li><p><strong>Age</strong> - 4 years</p></li>
        </ul>
        """
        detail = WythallChecker._parse_detail(html, "Crumpet")
        assert detail["breed"] == "Presa X Mastiff Crossbreed"
        assert detail["gender"] == "Male"
        assert detail["age"] == "4 years"

    def test_extracts_from_strong_tags_sex_dash_inside(self):
        """Handle 'Sex -' where dash is inside <strong>."""
        html = """
        <title>Eddie \u2014 Wythall Animal Sanctuary</title>
        <h3>More About Me</h3>
        <ul>
          <li><p><strong>Breed</strong> -Lurcher</p></li>
          <li><p><strong>Sex -</strong> Male</p></li>
          <li><p><strong>Age</strong> - 1 year</p></li>
        </ul>
        """
        detail = WythallChecker._parse_detail(html, "Eddie")
        assert detail["breed"] == "Lurcher"
        assert detail["gender"] == "Male"
        assert detail["age"] == "1 year"

    def test_extracts_from_h4_format(self):
        """Ronnie/Ziggy use <h4><strong>LABEL:</strong> VALUE</h4> format."""
        html = """
        <title>Ronnie \u2014 Wythall Animal Sanctuary</title>
        <h4><strong>AGE:</strong> 1 Year</h4>
        <h4><strong>BREED: </strong> Mixed breed</h4>
        <h4><strong>COLOUR: </strong>Tan + Black</h4>
        """
        detail = WythallChecker._parse_detail(html, "Ronnie")
        assert detail["age"] == "1 Year"
        assert detail["breed"] == "Mixed breed"
        assert detail["name"] == "Ronnie"

    def test_gender_from_entire_male_text(self):
        """Some dogs lack Sex field but have 'Entire male' in text."""
        html = """
        <title>Ziggy \u2014 Wythall Animal Sanctuary</title>
        <h4><strong>AGE:</strong> 1 Year</h4>
        <h4><strong>BREED: </strong> Mixed breed</h4>
        <p>Entire male - I will be rehomed with a neuter contract</p>
        """
        detail = WythallChecker._parse_detail(html, "Ziggy")
        assert detail["age"] == "1 Year"
        assert detail["breed"] == "Mixed breed"
        assert detail["gender"] == "Male"

    def test_extracts_photo_from_squarespace_cdn(self):
        """Photo URL from Squarespace CDN image."""
        html = """
        <title>Cherry — Wythall Animal Sanctuary</title>
        <div>
          Breed - Bulldog
          Sex - Female
          Age - 4 years
        </div>
        <img src="https://images.squarespace-cdn.com/content/v1/abc/dog.jpg" />
        """
        detail = WythallChecker._parse_detail(html, "Cherry")
        assert "images.squarespace-cdn.com" in detail["photo_url"]


class TestParse:
    def test_no_dogs(self, tmp_path):
        c = WythallChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_foster_dog_filtered_out(self, tmp_path):
        """Foster-only dogs should be excluded from parse output."""
        listing_html = """
        <a class="grid-item" href="/dogs/cherry">Cherry</a>
        """
        detail_html = """
        <title>Cherry - Foster Me <3 — Wythall Animal Sanctuary</title>
        <div>
          I'm looking for a quiet loving foster home
          Breed - Bulldog
          Sex - Female
          Age - 4 years
        </div>
        """
        c = WythallChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert dogs == []

    def test_available_dog_included(self, tmp_path):
        """Available dogs should be included."""
        listing_html = """
        <a class="grid-item" href="/dogs/crumpet">Crumpet</a>
        """
        detail_html = """
        <title>Crumpet — Wythall Animal Sanctuary</title>
        <div>
          I'm looking for my forever home
          Breed -Presa X Mastiff Crossbreed
          Size - Large
          Sex - Male
          Age - 4 years
          Adoption fee - £250
        </div>
        <img src="https://images.squarespace-cdn.com/content/v1/abc/crumpet.jpg" />
        """
        c = WythallChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", return_value=detail_html):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Crumpet"
        assert d.breed == "Presa X Mastiff Crossbreed"
        assert d.gender == "Male"
        assert d.age == "4 years"
        assert d.status == "Available"
        assert d.photo_url == "https://images.squarespace-cdn.com/content/v1/abc/crumpet.jpg"
        assert d.url == "https://www.wythallanimalsanctuary.org/dogs/crumpet"
        assert "Wythall Animal Sanctuary" in d.location

    def test_mixed_dogs(self, tmp_path):
        """Available dogs included, foster dogs excluded."""
        listing_html = """
        <a class="grid-item" href="/dogs/crumpet">Crumpet</a>
        <a class="grid-item" href="/dogs/cherry">Cherry</a>
        """

        def mock_fetch(url):
            if "cherry" in url:
                return """<title>Cherry - Foster Me — Wythall Animal Sanctuary</title>
                <div>I'm looking for a quiet loving foster home
                Breed - Bulldog\nSex - Female\nAge - 4 years</div>"""
            if "crumpet" in url:
                return """<title>Crumpet — Wythall Animal Sanctuary</title>
                <div>I'm looking for my forever home
                Breed -Presa X Mastiff\nSex - Male\nAge - 4 years\nAdoption fee - £250</div>"""
            return ""

        c = WythallChecker(str(tmp_path))
        with patch.object(c, "_fetch_detail", side_effect=mock_fetch):
            dogs = c.parse(listing_html)
        assert len(dogs) == 1
        assert dogs[0].name == "Crumpet"
