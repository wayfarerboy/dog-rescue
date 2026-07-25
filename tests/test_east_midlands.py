"""Tests for East Midlands Dog Rescue site checker."""

import re

import pytest
from bs4 import BeautifulSoup

from sites.east_midlands import (
    EastMidlandsDogRescueChecker,
    _infer_gender,
    _split_breed_age,
)


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ── Page fixtures ───────────────────────────────────────────────────

LISTING_PAGE_1 = """<html><body><ul class="products">
<li class="product type-product post-12440 status-publish first instock product_cat-uncategorized has-post-thumbnail shipping-taxable product-type-simple">
 <a class="woocommerce-LoopProduct-link woocommerce-loop-product__link" href="https://www.eastmidlandsdogrescue.org/product/bella/">
  <img alt="Bella" class="attachment-woocommerce_thumbnail size-woocommerce_thumbnail" src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/01/bella-300x300.jpeg"/>
  <h2 class="woocommerce-loop-product__title">Bella</h2>
 </a>
</li>
<li class="product type-product post-12441 status-publish instock product_cat-uncategorized has-post-thumbnail shipping-taxable product-type-simple">
 <a class="woocommerce-LoopProduct-link woocommerce-loop-product__link" href="https://www.eastmidlandsdogrescue.org/product/max/">
  <img alt="Max (Reserved) ❤️" class="attachment-woocommerce_thumbnail size-woocommerce_thumbnail" src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/02/max-300x300.jpeg"/>
  <h2 class="woocommerce-loop-product__title">Max (Reserved) ❤️</h2>
 </a>
</li>
<li class="product type-product post-12442 status-publish instock product_cat-uncategorized has-post-thumbnail shipping-taxable product-type-simple">
 <a class="woocommerce-LoopProduct-link woocommerce-loop-product__link" href="https://www.eastmidlandsdogrescue.org/product/ruby/">
  <img alt="Ruby Reserved) ❤️" class="attachment-woocommerce_thumbnail size-woocommerce_thumbnail" src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/03/ruby-300x300.jpeg"/>
  <h2 class="woocommerce-loop-product__title">Ruby Reserved) ❤️</h2>
 </a>
</li>
</ul></body></html>"""

DETAIL_BELLA = """<html><body>
<div class="woocommerce-product-gallery__image">
  <img src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/01/bella-800x800.jpeg"/>
</div>
<div class="woocommerce-Tabs-panel--description">
  <p>French Bulldog 2 years old Bella is a sweet girl who loves cuddles. She needs a quiet home with no other dogs.</p>
</div>
</body></html>"""

DETAIL_MAX = """<html><body>
<div class="woocommerce-product-gallery__image">
  <img src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/02/max-800x800.jpeg"/>
</div>
<div class="woocommerce-Tabs-panel--description">
  <p>Crossbreed 3 years A bouncy lad who would suit an active home.</p>
</div>
</body></html>"""

DETAIL_GRACIE = """<html><body>
<div class="woocommerce-product-gallery__image">
  <img src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/05/gracie-800x800.jpeg"/>
</div>
<div class="woocommerce-Tabs-panel--description">
  <p>Lurcher 8 months old Very timid and broken spirited Will need a kind steady approach to training In a loving sight hound savvy home she will blossom and find her courage</p>
</div>
</body></html>"""

DETAIL_CINDERS = """<html><body>
<div class="woocommerce-product-gallery__image">
  <img src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/04/cinders-800x800.jpeg"/>
</div>
<div class="woocommerce-Tabs-panel--description">
  <p>Saluki 8 years Bonded pair Sweet natured and will make lovely companions for one lucky adopter Support will be offered by the rescue ongoing An adopter with some knowledge of sighthounds required with time and commitment, a safe secure garden, and a willingness to give something back for the love of this adorable mature pair of ladies.</p>
</div>
</body></html>"""

DETAIL_MILES = """<html><body>
<div class="woocommerce-product-gallery__image">
  <img src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/04/miles-800x800.jpeg"/>
</div>
<div class="woocommerce-Tabs-panel--description">
  <p>Poodle (Standard, big lad) 8 years old A truly sweet lad in need of TLC and a quiet local home where he can decompress and blossom into a faithful companion He likes people but would enjoy being an only dog so he can be King of his Castle.</p>
</div>
</body></html>"""

DETAIL_APPROX_AGE = """<html><body>
<div class="woocommerce-Tabs-panel--description">
  <p>Chihuahua (approx 5 years old ) Sweet but very frightened of people, he will need time and commitment.</p>
</div>
</body></html>"""

DETAIL_NO_DESC = """<html><body>
<div class="woocommerce-product-gallery__image">
  <img src="https://www.eastmidlandsdogrescue.org/wp-content/uploads/2026/01/nodesc-800x800.jpeg"/>
</div>
</body></html>"""

LISTING_EMPTY = """<html><body><ul class="products"></ul></body></html>"""


# ── Listing page parsing ────────────────────────────────────────────

class TestParse:
    def test_parses_available_dog(self):
        c = EastMidlandsDogRescueChecker("data")
        dogs = c.parse(LISTING_PAGE_1)
        bella = [d for d in dogs if d.name == "Bella"][0]
        assert bella.status == "Available"
        assert bella.name == "Bella"
        assert bella.url == "https://www.eastmidlandsdogrescue.org/product/bella/"
        assert "bella-300x300" in bella.photo_url

    def test_reserved_detected(self):
        c = EastMidlandsDogRescueChecker("data")
        dogs = c.parse(LISTING_PAGE_1)
        max_dog = [d for d in dogs if d.name == "Max"][0]
        assert max_dog.status == "Reserved"

    def test_reserved_without_opening_paren(self):
        """Ruby Reserved) ❤️ — missing opening paren but still reserved."""
        c = EastMidlandsDogRescueChecker("data")
        dogs = c.parse(LISTING_PAGE_1)
        ruby = [d for d in dogs if d.name == "Ruby"][0]
        assert ruby.status == "Reserved"

    def test_reserved_stripped_from_name(self):
        c = EastMidlandsDogRescueChecker("data")
        dogs = c.parse(LISTING_PAGE_1)
        max_dog = [d for d in dogs if "Max" in d.name][0]
        assert max_dog.name == "Max"

    def test_empty_listing(self):
        c = EastMidlandsDogRescueChecker("data")
        dogs = c.parse(LISTING_EMPTY)
        assert dogs == []

    def test_page_split_marker(self):
        c = EastMidlandsDogRescueChecker("data")
        combined = LISTING_PAGE_1 + "\n<!-- EMDR_PAGE_SPLIT -->\n" + LISTING_PAGE_1
        dogs = c.parse(combined)
        # 3 unique dogs × 2 pages = 6 entries (duplicates not deduped by parse)
        assert len(dogs) == 6


# ── Detail page parsing ─────────────────────────────────────────────

class TestParseDetail:
    def test_breed_and_age_simple(self):
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_BELLA, "Bella")
        assert result["breed"] == "French Bulldog"
        assert result["age"] == "2 years old"

    def test_gender_female(self):
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_BELLA, "Bella")
        assert result["gender"] == "Female"

    def test_gender_male(self):
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_MAX, "Max")
        assert result["gender"] == "Male"

    def test_gender_from_ladies(self):
        """Cinders & Anna uses 'pair of ladies'."""
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_CINDERS, "Cinders & Anna")
        assert result["gender"] == "Female"

    def test_age_without_old_suffix(self):
        """'Saluki 8 years' without 'old'."""
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_CINDERS, "Cinders & Anna")
        assert result["age"] == "8 years"

    def test_breed_with_parens(self):
        """Poodle (Standard, big lad) — parens in breed."""
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_MILES, "Miles")
        assert "Poodle" in result["breed"]
        assert "Standard" in result["breed"]

    def test_male_with_lad(self):
        """'lad' should indicate male."""
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_MILES, "Miles")
        assert result["gender"] == "Male"

    def test_female_from_she(self):
        """'she will blossom' indicates female."""
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_GRACIE, "Gracie")
        assert result["gender"] == "Female"

    def test_approx_age(self):
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_APPROX_AGE, "Test")
        assert result["breed"] == "Chihuahua"
        assert "5" in result["age"]

    def test_missing_description(self):
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_NO_DESC, "NoDesc")
        assert result.get("breed", "") == ""
        assert result.get("age", "") == ""
        assert result.get("gender", "") == ""

    def test_photo_url_extracted(self):
        result = EastMidlandsDogRescueChecker._parse_detail(DETAIL_BELLA, "Bella")
        # Size suffix is stripped; should resolve to original filename
        assert "bella.jpeg" in result["photo_url"]


# ── Breed/age splitting ─────────────────────────────────────────────

class TestSplitBreedAge:
    def test_simple(self):
        breed, age = _split_breed_age("French Bulldog 2 years old Bella is a sweet girl")
        assert breed == "French Bulldog"
        assert age == "2 years old"

    def test_age_without_old(self):
        breed, age = _split_breed_age("Crossbreed 5 years A very deserving lad")
        assert breed == "Crossbreed"
        assert age == "5 years"

    def test_months_old(self):
        breed, age = _split_breed_age("Lurcher 8 months old Very timid")
        assert breed == "Lurcher"
        assert age == "8 months old"

    def test_approx_age(self):
        breed, age = _split_breed_age("Chihuahua approx 5 years old Sweet but frightened")
        assert breed == "Chihuahua"
        assert "5" in age
        assert "years" in age

    def test_approx_age_with_parens(self):
        breed, age = _split_breed_age("Chihuahua (approx 5 years old ) Sweet")
        assert breed == "Chihuahua"
        assert "5" in age
        assert "years" in age

    def test_breed_with_parens(self):
        breed, age = _split_breed_age("Wire haired Dacshund (Teckel) 2 years A stunning girl")
        assert breed == "Wire haired Dacshund (Teckel)"

    def test_breed_with_size_parens(self):
        breed, age = _split_breed_age("Crossbreed (labradoodle size) 2 years old Sweet")
        assert breed == "Crossbreed (labradoodle size)"
        assert age == "2 years old"

    def test_multiword_breed(self):
        breed, age = _split_breed_age("French Bulldog 4 years old Bea has been")
        assert breed == "French Bulldog"

    def test_no_age(self):
        breed, age = _split_breed_age("Crossbreed")
        assert breed == "Crossbreed"
        assert age == ""

    def test_empty(self):
        breed, age = _split_breed_age("")
        assert breed == ""
        assert age == ""

    def test_bonded_pair(self):
        """Age followed by 'Bonded pair' — age still detected."""
        breed, age = _split_breed_age("Saluki 8 years Bonded pair")
        assert breed == "Saluki"
        assert age == "8 years"

    def test_approx_with_slash_age(self):
        breed, age = _split_breed_age("Chihuahuas approx 5/6 years old Very frightened")
        assert breed == "Chihuahuas"
        assert "5/6" in age


# ── Gender inference ────────────────────────────────────────────────

class TestInferGender:
    def test_female_girl(self):
        assert _infer_gender("A sweet girl who loves cuddles", "Bella") == "Female"

    def test_female_she(self):
        assert _infer_gender("she will blossom and find her courage", "Gracie") == "Female"

    def test_female_her(self):
        assert _infer_gender("needs time to help her settle", "Lola") == "Female"

    def test_female_lady(self):
        assert _infer_gender("very sweet little lady looking for a home", "Shelby") == "Female"

    def test_female_ladies(self):
        assert _infer_gender("this adorable mature pair of ladies", "Cinders") == "Female"

    def test_male_lad(self):
        assert _infer_gender("a bouncy lad who would suit an active home", "Max") == "Male"

    def test_male_he(self):
        assert _infer_gender("he will need time to decompress", "Miles") == "Male"

    def test_male_him(self):
        assert _infer_gender("give him time to settle in", "Rex") == "Male"

    def test_male_boy(self):
        assert _infer_gender("a good boy who loves walks", "Buddy") == "Male"

    def test_no_gender_words(self):
        assert _infer_gender("Crossbreed 5 years old", "Unknown") == ""

    def test_tie_breaks_female(self):
        """If counts are equal, female wins."""
        assert _infer_gender("little boy and girl", "Tie") == "Female"

    def test_female_wins_over_ambiguous_lad(self):
        """'she' + 'lad': she wins."""
        assert _infer_gender("she is a lovely little lad", "Mix") == "Female"


# ── Age calculation ─────────────────────────────────────────────────

class TestAgeMonths:
    def test_months(self):
        assert EastMidlandsDogRescueChecker._age_months("8 months old") == 8

    def test_years(self):
        assert EastMidlandsDogRescueChecker._age_months("2 years") == 24

    def test_years_old(self):
        assert EastMidlandsDogRescueChecker._age_months("5 years old") == 60

    def test_approx(self):
        assert EastMidlandsDogRescueChecker._age_months("approx. 7 months old") == 7

    def test_empty(self):
        assert EastMidlandsDogRescueChecker._age_months("") == 999

    def test_unparseable(self):
        assert EastMidlandsDogRescueChecker._age_months("Senior") == 999


# ── Integration ─────────────────────────────────────────────────────

class TestCheckIntegration:
    def test_check_filters_reserved(self, monkeypatch):
        """check() should exclude reserved dogs from results."""
        c = EastMidlandsDogRescueChecker("data")

        def mock_fetch():
            return LISTING_PAGE_1

        def mock_fetch_detail(url):
            if "bella" in url:
                return DETAIL_BELLA
            return DETAIL_MAX

        monkeypatch.setattr(c, "fetch", mock_fetch)
        monkeypatch.setattr(c, "_fetch_detail", mock_fetch_detail)

        dogs = c.check()
        names = {d.name for d in dogs}
        # Max is reserved → excluded. Bella (2 years old) → excluded (age > 12 months)
        # Only dogs with age ≤ 12 months and female pass
        assert "Max" not in names

    def test_check_filters_by_age_and_gender(self, monkeypatch):
        """Only female dogs ≤ 12 months pass the filter."""
        c = EastMidlandsDogRescueChecker("data")

        combined = (
            LISTING_PAGE_1
            + "\n<!-- EMDR_PAGE_SPLIT -->\n"
            + LISTING_EMPTY
        )

        def mock_fetch():
            return combined

        def mock_fetch_detail(url):
            if "bella" in url:
                return DETAIL_BELLA  # Female, 2 years → filtered out (too old)
            if "max" in url:
                return DETAIL_MAX    # Male, 3 years → filtered out
            if "ruby" in url:
                return DETAIL_GRACIE  # Female, 8 months → PASSES (not Ruby's real detail but good test data)
            return DETAIL_NO_DESC

        monkeypatch.setattr(c, "fetch", mock_fetch)
        monkeypatch.setattr(c, "_fetch_detail", mock_fetch_detail)

        dogs = c.check()
        # Only dogs that are female AND ≤ 12 months pass
        # Bella: female but 2 years → excluded
        # Max: male → excluded
        # Ruby: uses Gracie detail → female, 8 months → passes
        passing_names = {d.name for d in dogs}
        assert "Bella" not in passing_names
        assert "Max" not in passing_names
