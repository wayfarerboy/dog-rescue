"""Tests for Happy Staffie Rescue site checker."""

import pytest

from sites.happy_staffie import (
    HappyStaffieChecker,
    _extract_age,
    _extract_breed,
    _infer_gender,
    _parse_gallery_status,
)


# ── Gallery HTML fixtures ───────────────────────────────────────────

GALLERY_HTML = """<!DOCTYPE html><html><body>
<div id="wrapper">
  <div id="viewport" class="grid">
    <div class="grid-sizer"></div>

    <div class="item">
      <div class="overlay"></div>
      <img height="472" src="https://static.wixstatic.com/media/359030_sasha~mv2.jpg/v1/fill/w_473,h_472,al_c,q_80,usm_0.33_1.00_0.00/sasha.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Sasha">Sasha</h3>
        <div class="desc">Click for more information</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_luna~mv2.jpg/v1/fill/w_473,h_473,al_c,q_80,usm_0.33_1.00_0.00/luna.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Luna">Luna</h3>
        <div class="desc">Click for more information</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_jack~mv2.jpg/v1/fill/w_473,h_473,al_c,q_80,usm_0.33_1.00_0.00/jack.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Jack">Jack</h3>
        <div class="desc">Click for more information</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_casey~mv2.jpg/v1/fill/w_473,h_473,al_c,q_80,usm_0.33_1.00_0.00/casey.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Casey">Casey</h3>
        <div class="desc">SUSPENDED due to volume of applications</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_deedee~mv2.jpg/v1/fill/w_473,h_473,al_c,q_80,usm_0.33_1.00_0.00/deedee.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Deedee">Deedee</h3>
        <div class="desc">RESERVED</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_darla~mv2.jpg/v1/fill/w_473,h_473,al_c,q_80,usm_0.33_1.00_0.00/darla.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Darla">Darla</h3>
        <div class="desc">RESERVED</div>
      </div>
    </div>

    <!-- Non-dog items that should be skipped -->
    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_donate~mv2.png" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Making a donation to Happy Staffie Rescue">Making a donation to Happy Staffie Rescue</h3>
        <div class="desc">Please click for more information</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_lottery~mv2.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="We're part of a lottery">We're part of a lottery</h3>
        <div class="desc">Click for more information</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_legacy~mv2.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Can you leave a lasting legacy to Happy Staffie?">Can you leave a lasting legacy to Happy Staffie?</h3>
        <div class="desc">Click here for more information</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_foster~mv2.png" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="Fostering">Fostering</h3>
        <div class="desc">Click for more information (image not representative of dogs needing to be fostered)</div>
      </div>
    </div>

    <div class="item">
      <div class="overlay"></div>
      <img height="473" src="https://static.wixstatic.com/media/359030_poster~mv2.jpg" width="473"/>
      <div class="sb-description">
        <h3 class="title" title="2026 Poster FINAL">2026 Poster FINAL</h3>
        <div class="desc"></div>
      </div>
    </div>
  </div>
</div>
</body></html>"""

# ── Detail page fixtures ───────────────────────────────────────────

DETAIL_SASHA = """<html><body>
<header><nav>HOME Adopt Donate</nav></header>
<main>
<h1>Sasha | Happy Staffie Rescue</h1>
<p>Sasha is a small staffie-cross, weighing just 11.2 kilos, and possibly
crossed with something like a Jack Russell. She is small enough to only need
an extra-small size of one of our harnesses. She has a gentle and sweet
personality and is very affectionate and was born September 2015 making her
10 years and 9 months at the time of her arrival.</p>
<h2>The sort of home for Sasha</h2>
<p>No dogs currently in the home</p>
<p>No cats in the home</p>
<p>No small children, recommended minimum age is 10 years</p>
<h2>Handling</h2>
<p>A very friendly little girl, easy to handle and loves to give gentle little kisses.</p>
<h2>Walks</h2>
<p>Due to the very hot weather when she arrived our walks with Sasha have been very limited.</p>
<h2>Play</h2>
<p>She loves snuffling, and loves snuffling in a snuffle box.</p>
<h2>Health</h2>
<p>Sasha has no obvious signs of injury or illness.</p>
<p>If you adopt a dog from Happy Staffie Rescue you could be entitled to five weeks free pet insurance through Agria.</p>
</main>
<footer>Happy Staffie Rescue</footer>
</body></html>"""

DETAIL_LUNA = """<html><body>
<nav>HOME Adopt Donate</nav>
<main>
<p>Luna is a 7-year-old crossbreed that arrived for rehoming on 21 May 2026.
Luna weighed 23.1 kilos when she arrived, and has now trimmed down to a
healthier 22.6 kilos.</p>
<p>She needs a confident and assertive owner, with a good clear voice who can
give her the instructions she needs, and will follow.</p>
<p>Luna was with us some time ago, and was adopted for over a year but the
owner found her difficult to walk.</p>
<h2>The sort of home for Luna</h2>
<p>No dogs currently in the home</p>
<h2>Handling</h2>
<p>A lovely dog, very friendly, very affectionate and easy to handle.</p>
<h2>Walks</h2>
<p>After allowing Luna to settle and acclimatise with us.</p>
<h2>Play</h2>
<p>Luna loves to play.</p>
<h2>Health</h2>
<p>Luna arrived in good health. She is already neutered.</p>
<p>If you adopt a dog from Happy Staffie Rescue you could be entitled to five weeks free pet insurance.</p>
</main>
</body></html>"""

DETAIL_JACK = """<html><body>
<nav>HOME Adopt Donate</nav>
<main>
<p>JackShy boy Jack arrived for rehoming on 10 February 2026.
He is a crossbreed, of medium size and weighs 23.4 kilos.</p>
<p>Jack may look smaller in his photos than he is. He is not a big dog,
but he isn't a small one either. Our vet estimates Jack to be 2-3 years of age.</p>
<h2>The sort of home for Jack</h2>
<p>No dogs or cats in the home</p>
<h2>Handling</h2>
<p>Jack is a bit of an unusual dog.</p>
<h2>Health</h2>
<p>No known health issues.</p>
</main>
</body></html>"""

DETAIL_PUPPY_GIRL = """<html><body>
<main>
<p>Rosie is a 5-month-old terrier cross puppy. She is a sweet little girl
who loves to play and cuddle. She weighs just 6 kilos and is growing fast.</p>
<h2>The sort of home for Rosie</h2>
<p>No cats in the home</p>
</main>
</body></html>"""

DETAIL_BORN_CURRENT_YEAR = """<html><body>
<main>
<p>Bella was born in March 2026 making her just a few months old.
This sweet girl loves everyone she meets.</p>
</main>
</body></html>"""


# ── unit tests: _parse_gallery_status ──────────────────────────────

@pytest.mark.parametrize(
    "desc,expected",
    [
        ("Click for more information", "Available"),
        ("RESERVED", "Reserved"),
        ("REHOMED", "Rehomed"),
        ("SUSPENDED due to volume of applications", "Suspended"),
        ("SUSPENDED", "Suspended"),
        # Non-dog items → None
        ("Please click for more information", None),
        ("Click here for more information", None),
        ("Click for more information (image not representative...)", None),
        ("", None),
        ("Full member of the Association of Dogs and Cats Home", None),
    ],
)
def test_parse_gallery_status(desc, expected):
    assert _parse_gallery_status(desc) == expected


# ── unit tests: _extract_breed ────────────────────────────────────

def test_extract_breed_staffie_cross():
    assert _extract_breed(DETAIL_SASHA, "Sasha") == "Staffie Cross"


def test_extract_breed_crossbreed():
    assert _extract_breed(DETAIL_LUNA, "Luna") == "Crossbreed"


def test_extract_breed_crossbreed_jack():
    assert _extract_breed(DETAIL_JACK, "Jack") == "Crossbreed"


def test_extract_breed_terrier_cross():
    assert _extract_breed(DETAIL_PUPPY_GIRL, "Rosie") == "Terrier Cross"


def test_extract_breed_not_rescue_name():
    """'Staffie' in rescue name should not be matched as a breed."""
    # This text has "Happy Staffie Rescue" but no actual breed mention
    html = """<html><body><main>
    <p>BuddyBuddy is a lovely dog who arrived for rehoming. He is very friendly.</p>
    <h2>The sort of home for Buddy</h2>
    <p>If you adopt a dog from Happy Staffie Rescue you could be entitled to free pet insurance.</p>
    </main></body></html>"""
    assert _extract_breed(html, "Buddy") == "Mixed Breed"


# ── unit tests: _extract_age ──────────────────────────────────────

@pytest.mark.parametrize(
    "html_fixture,expected",
    [
        (DETAIL_SASHA, "10 years 9 months"),
        (DETAIL_LUNA, "7 years old"),
        (DETAIL_JACK, "2-3 years"),
        (DETAIL_PUPPY_GIRL, "5 months old"),
    ],
)
def test_extract_age(html_fixture, expected):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_fixture, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    assert _extract_age(text) == expected


def test_extract_age_born_year():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(DETAIL_BORN_CURRENT_YEAR, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # born in 2026 → current year minus 2026
    from datetime import datetime
    current_year = datetime.now().year
    expected_age = current_year - 2026
    assert _extract_age(text) == f"{expected_age} years old"


def test_extract_age_empty():
    assert _extract_age("") == ""
    assert _extract_age("No age information available") == ""


# ── unit tests: _infer_gender ─────────────────────────────────────

def test_infer_gender_female_sasha():
    assert _infer_gender(DETAIL_SASHA, "Sasha") == "Female"


def test_infer_gender_female_luna():
    assert _infer_gender(DETAIL_LUNA, "Luna") == "Female"


def test_infer_gender_male_jack():
    assert _infer_gender(DETAIL_JACK, "Jack") == "Male"


def test_infer_gender_female_rosie():
    assert _infer_gender(DETAIL_PUPPY_GIRL, "Rosie") == "Female"


def test_infer_gender_ambiguous():
    text = "A lovely dog looking for a home."
    assert _infer_gender(text, "Pat") == ""


# ── unit tests: _age_months ────────────────────────────────────────

@pytest.mark.parametrize(
    "age_str,expected",
    [
        ("10 years 9 months", 129),
        ("7 years old", 84),
        ("5 months old", 5),
        ("2-3 years", 24),
        ("1 year old", 12),
        ("3 years", 36),
        ("", 999),
        ("Unknown", 999),
    ],
)
def test_age_months(age_str, expected):
    assert HappyStaffieChecker._age_months(age_str) == expected


# ── integration: parse() ───────────────────────────────────────────

def test_parse_all_dogs():
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    assert len(dogs) == 6  # 6 real dogs in the fixture

    names = [d.name for d in dogs]
    assert names == ["Sasha", "Luna", "Jack", "Casey", "Deedee", "Darla"]


def test_parse_available():
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    available = [d for d in dogs if d.status == "Available"]
    assert len(available) == 3
    assert [d.name for d in available] == ["Sasha", "Luna", "Jack"]


def test_parse_statuses():
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    statuses = {d.name: d.status for d in dogs}
    assert statuses == {
        "Sasha": "Available",
        "Luna": "Available",
        "Jack": "Available",
        "Casey": "Suspended",
        "Deedee": "Reserved",
        "Darla": "Reserved",
    }


def test_parse_excludes_non_dog_items():
    """Donation posters, lottery ads, etc. should not appear as dogs."""
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    names = [d.name for d in dogs]
    assert "Making a donation to Happy Staffie Rescue" not in names
    assert "We're part of a lottery" not in names
    assert "Fostering" not in names
    assert "2026 Poster FINAL" not in names


def test_parse_urls():
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    assert dogs[0].url == "https://www.happystaffie.co.uk/sasha"
    assert dogs[1].url == "https://www.happystaffie.co.uk/luna"
    assert dogs[4].url == "https://www.happystaffie.co.uk/deedee"


def test_parse_photos():
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    for dog in dogs:
        assert dog.photo_url, f"{dog.name} should have a photo"
        assert "wixstatic.com" in dog.photo_url


def test_parse_location():
    checker = HappyStaffieChecker("data")
    dogs = checker.parse(GALLERY_HTML)
    for dog in dogs:
        assert "Kidderminster" in dog.location


def test_parse_empty():
    checker = HappyStaffieChecker("data")
    assert checker.parse("") == []


# ── integration: _parse_detail ─────────────────────────────────────

def test_parse_detail_sasha():
    result = HappyStaffieChecker._parse_detail(DETAIL_SASHA, "Sasha")
    assert result["breed"] == "Staffie Cross"
    assert result["age"] == "10 years 9 months"
    assert result["gender"] == "Female"


def test_parse_detail_luna():
    result = HappyStaffieChecker._parse_detail(DETAIL_LUNA, "Luna")
    assert result["breed"] == "Crossbreed"
    assert result["age"] == "7 years old"
    assert result["gender"] == "Female"


def test_parse_detail_jack():
    result = HappyStaffieChecker._parse_detail(DETAIL_JACK, "Jack")
    assert result["breed"] == "Crossbreed"
    assert result["age"] == "2-3 years"
    assert result["gender"] == "Male"


# ── integration: check() flow ──────────────────────────────────────

def test_check_no_new_dogs(monkeypatch, tmp_path):
    """When all dogs are already cached, check() returns empty list."""
    checker = HappyStaffieChecker(str(tmp_path))

    def fake_fetch_and_parse(self):
        dogs = checker.parse(GALLERY_HTML)
        # Make them all available for detail scraping
        for d in dogs:
            d.status = "Available"
        return dogs

    def fake_enrich(self, dogs):
        # Simulate detail scraping: all female puppies
        for d in dogs:
            if d.name == "Sasha":
                d.gender = "Female"
                d.age = "10 years 9 months"  # too old
                d.breed = "Staffie Cross"
            elif d.name == "Luna":
                d.gender = "Female"
                d.age = "7 years old"  # too old
                d.breed = "Crossbreed"
            elif d.name == "Jack":
                d.gender = "Male"  # wrong gender
                d.age = "6 months"
                d.breed = "Crossbreed"
            elif d.name == "Darla":
                d.gender = "Female"
                d.age = "5 months old"  # matches!
                d.breed = "Terrier Cross"
            else:
                d.gender = "Male"
                d.age = "3 years"
                d.breed = "Crossbreed"

    monkeypatch.setattr(HappyStaffieChecker, "_fetch_and_parse", fake_fetch_and_parse)
    monkeypatch.setattr(HappyStaffieChecker, "_enrich_from_details", fake_enrich)

    # First run: should find Darla (female, 5 months)
    new = checker.check()
    assert len(new) == 1
    assert new[0].name == "Darla"

    # Second run: Darla already cached, no new dogs
    new2 = checker.check()
    assert len(new2) == 0


def test_check_reserved_excluded(monkeypatch, tmp_path):
    """Reserved/Rehomed/Suspended dogs are not enriched or filtered."""
    checker = HappyStaffieChecker(str(tmp_path))

    def fake_fetch_and_parse(self):
        return checker.parse(GALLERY_HTML)

    def fake_enrich(self, dogs):
        # Should only be called with available dogs
        assert all(d.status == "Available" for d in dogs)
        for d in dogs:
            d.gender = "Male"  # won't pass filter
            d.age = "5 years"
            d.breed = "Crossbreed"

    monkeypatch.setattr(HappyStaffieChecker, "_fetch_and_parse", fake_fetch_and_parse)
    monkeypatch.setattr(HappyStaffieChecker, "_enrich_from_details", fake_enrich)

    new = checker.check()
    assert len(new) == 0  # all available dogs are male, filtered out
