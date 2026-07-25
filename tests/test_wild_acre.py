"""Tests for Wild Acre Rescue site checker."""

import datetime

import pytest

from sites.wild_acre import (
    WildAcreChecker,
    _age_months,
    _format_age,
    _infer_gender,
    _months_since,
    _parse_age,
    _parse_breed,
    _titlecase_breed,
)

# ── Page fixtures ───────────────────────────────────────────────────

LISTING_ONE_DOG = """<html><body><main id="content">
<div data-elementor-type="wp-page">
<div class="e-con-inner">
<div class="elementor-element elementor-element-7b26d22 elementor-position-left elementor-vertical-align-middle elementor-widget elementor-widget-image-box" data-id="7b26d22">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img decoding="async" width="296" height="300"
             src="https://wildacrerescue.co.uk/wp-content/uploads/2024/02/zak-296x300.jpg"
             class="attachment-medium size-medium wp-image-1205" alt=""/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Zak</h3>
        <p class="elementor-image-box-description">Meet Zak. DOB July 2022
Zak we believe is a patterdale x chihuahua x French bulldog.
If you are looking for a dog with a HUGE personality and a HUGE amount of energy, Zak might just be the dog for you.
Zak came into rescue as he was suffering separation anxiety. The foster home has worked really hard to help Zak with this and he can now be left for short periods of time.
He also came in with cherry eye originally in one eye, but since he has been in rescue the other eye also has needed surgery.
Zak is good with everyone but is a very bouncy dog.
If you think you are the home for Zak please send a message to the page.
We only rehome within the West Midlands.
Homecheck and adoption fee apply.</p>
      </div>
    </div>
  </div>
</div>
</div>
</div>
</main></body></html>"""

LISTING_TWO_DOGS = """<html><body><main id="content">
<div data-elementor-type="wp-page">
<div class="e-con-inner">
<div class="elementor-element elementor-element-7b26d22 elementor-widget elementor-widget-image-box">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img src="https://wildacrerescue.co.uk/wp-content/uploads/2024/02/zak.jpg"/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Zak</h3>
        <p class="elementor-image-box-description">Meet Zak. DOB July 2022
Zak we believe is a patterdale x chihuahua x French bulldog.
Zak came into rescue as he was suffering separation anxiety.
We only rehome within the West Midlands.</p>
      </div>
    </div>
  </div>
</div>
<div class="elementor-element elementor-element-8c37e33 elementor-widget elementor-widget-image-box">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img src="https://wildacrerescue.co.uk/wp-content/uploads/2024/03/luna.jpg"/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Luna</h3>
        <p class="elementor-image-box-description">Meet Luna. DOB March 2025
Luna is a jack russell terrier.
She is a sweet little girl who loves to play.
Luna is looking for a home where she can be the centre of attention.</p>
      </div>
    </div>
  </div>
</div>
</div>
</div>
</main></body></html>"""

LISTING_DOG_NO_DOB = """<html><body><main id="content">
<div data-elementor-type="wp-page">
<div class="e-con-inner">
<div class="elementor-element elementor-element-7b26d22 elementor-widget elementor-widget-image-box">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img src="https://wildacrerescue.co.uk/wp-content/uploads/2024/02/rosie.jpg"/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Rosie</h3>
        <p class="elementor-image-box-description">Meet Rosie. Rosie is a staffordshire bull terrier cross.
She is 6 months old and a typical puppy. She loves everyone she meets.</p>
      </div>
    </div>
  </div>
</div>
</div>
</div>
</main></body></html>"""

LISTING_EMPTY = """<html><body><main id="content">
<div data-elementor-type="wp-page">
<div class="e-con-inner">
<p>No dogs currently available for adoption.</p>
</div>
</div>
</main></body></html>"""

LISTING_MALE_FEMALE_MIX = """<html><body><main id="content">
<div data-elementor-type="wp-page">
<div class="e-con-inner">
<div class="elementor-element elementor-element-7b26d22 elementor-widget elementor-widget-image-box">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img src="https://wildacrerescue.co.uk/wp-content/uploads/2024/02/max.jpg"/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Max</h3>
        <p class="elementor-image-box-description">Meet Max. DOB January 2024
Max is a labrador cross.
He is a very good boy who loves his walks.</p>
      </div>
    </div>
  </div>
</div>
<div class="elementor-element elementor-element-8c37e33 elementor-widget elementor-widget-image-box">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img src="https://wildacrerescue.co.uk/wp-content/uploads/2024/03/daisy.jpg"/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Daisy</h3>
        <p class="elementor-image-box-description">Meet Daisy. 6 months old
Daisy is a cocker spaniel.
She is a beautiful girl with a lovely temperament.</p>
      </div>
    </div>
  </div>
</div>
</div>
</div>
</main></body></html>"""


# ── Parse: listing page ─────────────────────────────────────────────

class TestParse:
    def test_parses_single_dog(self):
        c = WildAcreChecker("data")
        dogs = c.parse(LISTING_ONE_DOG)
        assert len(dogs) == 1
        zak = dogs[0]
        assert zak.name == "Zak"
        assert zak.gender == "Male"
        assert "Patterdale" in zak.breed
        assert "Chihuahua" in zak.breed
        assert "French Bulldog" in zak.breed
        assert zak.status == "Available"
        assert zak.location == "West Midlands"
        assert "zak-296x300" in zak.photo_url

    def test_parses_two_dogs(self):
        c = WildAcreChecker("data")
        dogs = c.parse(LISTING_TWO_DOGS)
        assert len(dogs) == 2

        zak = [d for d in dogs if d.name == "Zak"][0]
        assert zak.gender == "Male"
        assert "Patterdale" in zak.breed

        luna = [d for d in dogs if d.name == "Luna"][0]
        assert luna.gender == "Female"
        assert "Jack Russell Terrier" in luna.breed

    def test_empty_listing(self):
        c = WildAcreChecker("data")
        dogs = c.parse(LISTING_EMPTY)
        assert dogs == []

    def test_photo_url_extracted(self):
        c = WildAcreChecker("data")
        dogs = c.parse(LISTING_ONE_DOG)
        assert "zak-296x300.jpg" in dogs[0].photo_url

    def test_url_is_listing_page(self):
        c = WildAcreChecker("data")
        dogs = c.parse(LISTING_ONE_DOG)
        assert dogs[0].url == "https://wildacrerescue.co.uk/dogs-for-adoption/"


# ── Gender inference ────────────────────────────────────────────────

class TestInferGender:
    def test_male_he(self):
        desc = "Zak came into rescue as he was suffering."
        assert _infer_gender(desc, "Zak") == "Male"

    def test_male_his(self):
        desc = "Max loves his walks."
        assert _infer_gender(desc, "Max") == "Male"

    def test_male_boy(self):
        desc = "He is a very good boy."
        assert _infer_gender(desc, "Max") == "Male"

    def test_female_she(self):
        desc = "She is a sweet little girl."
        assert _infer_gender(desc, "Luna") == "Female"

    def test_female_her(self):
        desc = "She loves everyone she meets and her toys."
        assert _infer_gender(desc, "Rosie") == "Female"

    def test_female_girl(self):
        desc = "a beautiful girl with a lovely temperament"
        assert _infer_gender(desc, "Daisy") == "Female"

    def test_no_gender_words(self):
        assert _infer_gender("Crossbreed 2 years old", "Unknown") == ""

    def test_tie_breaks_female(self):
        assert _infer_gender("good boy and girl", "Tie") == "Female"


# ── Breed parsing ───────────────────────────────────────────────────

class TestParseBreed:
    def test_is_a(self):
        assert _parse_breed("Luna is a jack russell terrier. She") == "Jack Russell Terrier"

    def test_we_believe_is_a(self):
        assert "Patterdale" in _parse_breed(
            "Zak we believe is a patterdale x chihuahua x French bulldog."
        )

    def test_cross_breed(self):
        result = _parse_breed("Rosie is a staffordshire bull terrier cross.")
        assert "Staffordshire Bull Terrier" in result

    def test_no_breed(self):
        assert _parse_breed("Just a dog looking for a home.") == ""

    def test_appears_to_be(self):
        result = _parse_breed("Milo appears to be a border collie mix.")
        assert "Border Collie" in result

    def test_probably(self):
        result = _parse_breed("Probably a lurcher with some terrier.")
        assert "Lurcher" in result

    def test_may_be(self):
        # "we believe may be a X"
        result = _parse_breed("Patch we believe may be a spaniel cross.")
        assert "Spaniel" in result


# ── Breed title-casing ──────────────────────────────────────────────

class TestTitlecaseBreed:
    def test_simple(self):
        assert _titlecase_breed("patterdale x chihuahua") == "Patterdale X Chihuahua"

    def test_single_breed(self):
        assert _titlecase_breed("french bulldog") == "French Bulldog"

    def test_three_way_cross(self):
        result = _titlecase_breed("patterdale x chihuahua x french bulldog")
        assert result == "Patterdale X Chihuahua X French Bulldog"

    def test_slash_separator(self):
        result = _titlecase_breed("border collie / springer spaniel")
        assert "Border Collie" in result
        assert "Springer Spaniel" in result


# ── Age parsing ─────────────────────────────────────────────────────

class TestParseAge:
    def test_dob_july_2022(self):
        desc = "Meet Zak. DOB July 2022\nZak we believe is a..."
        age = _parse_age(desc)
        # Age should be in months or years based on current date
        # July 2022 → around 4 years in July 2026
        assert "years" in age or "months" in age

    def test_dob_with_day(self):
        desc = "DOB 15 March 2025"
        age = _parse_age(desc)
        assert "months" in age or "years" in age

    def test_explicit_months(self):
        desc = "Rosie is 6 months old and a typical puppy."
        age = _parse_age(desc)
        assert age == "6 months"

    def test_explicit_years(self):
        desc = "Rex is 4 years old and loves walks."
        age = _parse_age(desc)
        assert age == "4 years"

    def test_no_age(self):
        assert _parse_age("Just a dog needing a home.") == ""

    def test_dob_abbreviated_month(self):
        desc = "DOB Jan 2023 Meet Bruno."
        age = _parse_age(desc)
        assert "years" in age or "months" in age


# ── Age formatting ──────────────────────────────────────────────────

class TestFormatAge:
    def test_zero_months(self):
        assert _format_age(0) == ""

    def test_one_month(self):
        assert _format_age(1) == "1 month"

    def test_six_months(self):
        assert _format_age(6) == "6 months"

    def test_one_year(self):
        assert _format_age(12) == "1 year"

    def test_one_year_three_months(self):
        assert _format_age(15) == "1 year 3 months"

    def test_two_years(self):
        assert _format_age(24) == "2 years"


# ── Age calculation ─────────────────────────────────────────────────

class TestAgeMonths:
    def test_months(self):
        assert _age_months("8 months") == 8

    def test_years(self):
        assert _age_months("2 years") == 24

    def test_years_and_months(self):
        assert _age_months("1 year 3 months") == 15

    def test_empty(self):
        assert _age_months("") == 999

    def test_unparseable(self):
        assert _age_months("Senior") == 999


# ── Months since ────────────────────────────────────────────────────

class TestMonthsSince:
    def test_one_year_ago(self):
        today = datetime.date.today()
        one_year_ago = today.replace(year=today.year - 1)
        assert _months_since(one_year_ago) == 12

    def test_six_months_ago(self):
        today = datetime.date.today()
        month = today.month - 6
        year = today.year
        if month < 1:
            month += 12
            year -= 1
        six_months_ago = today.replace(year=year, month=month)
        assert _months_since(six_months_ago) == 6


# ── Integration ─────────────────────────────────────────────────────

class TestCheckIntegration:
    def test_check_filters_by_age_and_gender(self, monkeypatch, tmp_path):
        """Only female dogs ≤ 12 months pass the filter."""
        c = WildAcreChecker(str(tmp_path))

        def mock_fetch():
            return LISTING_MALE_FEMALE_MIX

        monkeypatch.setattr(c, "fetch", mock_fetch)

        dogs = c.check()
        names = {d.name for d in dogs}

        # Max: Male → excluded
        assert "Max" not in names
        # Daisy: 6 months old, Female → passes
        assert "Daisy" in names

    def test_check_respects_cache(self, monkeypatch, tmp_path):
        """Second run with no changes returns empty list."""
        data_dir = str(tmp_path)
        c = WildAcreChecker(data_dir)

        def mock_fetch():
            return LISTING_TWO_DOGS

        monkeypatch.setattr(c, "fetch", mock_fetch)

        # First run
        dogs1 = c.check()
        # Zak: Male → excluded. Luna: DOB March 2025, Female → ~1yr 4mo (too old)
        # So first run may or may not match depending on current date
        # Just verify first run populates cache
        assert c._data_path.exists()

        # Second run — no changes, should return empty
        dogs2 = c.check()
        assert dogs2 == []

    def test_check_with_passing_puppy(self, monkeypatch, tmp_path):
        """A female puppy passes filter and is returned."""
        data_dir = str(tmp_path)
        c = WildAcreChecker(data_dir)

        # Compute a DOB that makes the dog exactly 3 months old
        today = datetime.date.today()
        month = today.month - 3
        year = today.year
        if month < 1:
            month += 12
            year -= 1
        month_name = datetime.date(year, month, 1).strftime("%B")

        listing = f"""<html><body><main id="content">
<div data-elementor-type="wp-page">
<div class="e-con-inner">
<div class="elementor-element elementor-element-7b26d22 elementor-widget elementor-widget-image-box">
  <div class="elementor-widget-container">
    <div class="elementor-image-box-wrapper">
      <figure class="elementor-image-box-img">
        <img src="https://example.com/puppy.jpg"/>
      </figure>
      <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Poppy</h3>
        <p class="elementor-image-box-description">Meet Poppy. DOB {month_name} {year}
Poppy is a french bulldog.
She is a sweet little girl who loves cuddles.</p>
      </div>
    </div>
  </div>
</div>
</div>
</div>
</main></body></html>"""

        def mock_fetch():
            return listing

        monkeypatch.setattr(c, "fetch", mock_fetch)
        dogs = c.check()
        names = {d.name for d in dogs}
        # Poppy is female, 3 months → should pass
        assert "Poppy" in names
