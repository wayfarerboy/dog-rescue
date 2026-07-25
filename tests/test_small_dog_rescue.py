"""Tests for Small Dog Rescue site checker."""

import pytest

from sites.small_dog_rescue import (
    SmallDogRescueChecker,
    _extract_age,
    _extract_breed,
    _extract_name,
    _infer_gender,
)


# ── Listing page fixtures ──────────────────────────────────────────

LISTING_ONE_DOG = """<!DOCTYPE html><html><body>
<div id="comp-moosbc8c" class="N8MGzv _v6ohL PO9MfV comp-moosbc8c wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
PLEASE NOTE RESCUE DOES NOT REHOME WITH ALL DAYS WORKERS...
</h4></div>

<div id="comp-mryv8ke0" class="comp-mryv8ke0 PuvQOs wixui-horizontal-line"></div>

<div id="comp-mryva4ne" class="N9h19D comp-mryva4ne wixui-image">
<div class="WvSioz">
<img src="https://static.wixstatic.com/media/ddc865_bella~mv2.jpg/v1/fill/w_322,h_252,al_c,q_80,usm_0.66_1.00_0.01/bella.jpg" style="object-fit:cover" width="322" height="252"/>
</div></div>

<div id="comp-mryvbsm4" class="N8MGzv _v6ohL PO9MfV comp-mryvbsm4 wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Bella stunning beautiful tiny girl, good with other dogs she has lost
her pal, so belle needs to have at least 1 small dog in household as she
missing her pal but in foster home she has 4 playmates and she loving it,
she has been spayed and had a dental so all good, she in foster home with
Lyn in Willenhall. adoption fee &pound;395.
</h4></div>

<div id="comp-mryvj9by" class="comp-mryvj9by PuvQOs wixui-horizontal-line"></div>
</body></html>"""

LISTING_TWO_DOGS = """<!DOCTYPE html><html><body>
<div id="comp-aaa" class="comp-aaa wixui-horizontal-line"></div>

<div id="comp-bbb" class="comp-bbb wixui-image">
<div class="WvSioz">
<img src="https://static.wixstatic.com/media/bella.jpg/v1/fill/w_322,h_252/bella.jpg" width="322" height="252"/>
</div></div>

<div id="comp-ccc" class="comp-ccc wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Bella stunning beautiful tiny girl, good with other dogs.
she is around 4 years old and a chihuahua cross.
</h4></div>

<div id="comp-ddd" class="comp-ddd wixui-horizontal-line"></div>

<div id="comp-eee" class="comp-eee wixui-image">
<div class="WvSioz">
<img src="https://static.wixstatic.com/media/max.jpg/v1/fill/w_322,h_252/max.jpg" width="322" height="252"/>
</div></div>

<div id="comp-fff" class="comp-fff wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Max lovely little boy, 5 months old, pug cross.
He is very friendly and loves to play.
</h4></div>
</body></html>"""

LISTING_DOG_WITH_BORN_YEAR = """<!DOCTYPE html><html><body>
<div id="comp-img" class="comp-img wixui-image">
<img src="https://static.wixstatic.com/media/rosie.jpg/v1/fill/w_322,h_252/rosie.jpg" width="322" height="252"/>
</div>
<div id="comp-txt" class="comp-txt wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Rosie this sweet girl was born in September 2025 and is a tiny
yorkshire terrier cross. She loves cuddles.
</h4></div>
</body></html>"""

LISTING_NO_DOGS = """<!DOCTYPE html><html><body>
<div class="wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
DOGS FOR REHOMING. PLEASE NOTE...
</h4></div>
</body></html>"""

LISTING_DOG_RESERVED = """<!DOCTYPE html><html><body>
<div id="comp-img" class="comp-img wixui-image">
<img src="https://static.wixstatic.com/media/luna.jpg/v1/fill/w_322,h_252/luna.jpg" width="322" height="252"/>
</div>
<div id="comp-txt" class="comp-txt wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Luna reserved this lovely girl is a pomeranian, 2 years old.
</h4></div>
</body></html>"""

LISTING_DOG_REHOMED = """<!DOCTYPE html><html><body>
<div id="comp-img" class="comp-img wixui-image">
<img src="https://static.wixstatic.com/media/daisy.jpg/v1/fill/w_322,h_252/daisy.jpg" width="322" height="252"/>
</div>
<div id="comp-txt" class="comp-txt wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Daisy rehomed
</h4></div>
</body></html>"""

LISTING_DOG_WITH_AGE_RANGE = """<!DOCTYPE html><html><body>
<div id="comp-img" class="comp-img wixui-image">
<img src="https://static.wixstatic.com/media/molly.jpg/v1/fill/w_322,h_252/molly.jpg" width="322" height="252"/>
</div>
<div id="comp-txt" class="comp-txt wixui-rich-text">
<h4 class="font_4 wixui-rich-text__text">
meet Molly she is a sweet girl, 2-3 years old, crossbreed.
</h4></div>
</body></html>"""


# ── unit tests: _extract_name ──────────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("meet Bella stunning beautiful tiny girl", "Bella"),
        ("meet Max lovely little boy, 5 months old", "Max"),
        ("meet Rosie this sweet girl was born in September", "Rosie"),
        ("meet Charlie-Boy the terrier cross", "Charlie-boy"),
        ("DOGS FOR REHOMING", ""),
        ("", ""),
    ],
)
def test_extract_name(text, expected):
    assert _extract_name(text) == expected


# ── unit tests: _extract_breed ────────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("meet Bella stunning beautiful tiny girl", "Mixed Breed"),
        ("chihuahua cross good with other dogs", "Chihuahua Cross"),
        ("pug cross very friendly", "Pug Cross"),
        ("yorkshire terrier cross she loves cuddles", "Yorkshire Terrier Cross"),
        ("shih tzu cross sweet boy", "Shih Tzu Cross"),
        ("crossbreed friendly girl", "Crossbreed"),
        ("staffordshire bull terrier cross girl", "Staffordshire Bull Terrier Cross"),
        ("pomeranian 2 years old girl", "Pomeranian"),
        ("dachshund cross tiny boy", "Dachshund Cross"),
        ("jack russell cross playful", "Jack Russell Cross"),
        ("cavalier king charles spaniel sweet", "Cavalier King Charles Spaniel"),
        ("cocker spaniel lovely girl", "Cocker Spaniel"),
        ("bichon frise fluffy", "Bichon Frise"),
        ("poodle cross smart girl", "Poodle Cross"),
        ("poodle very clever", "Poodle"),
        ("a cross of something", "Crossbreed"),
    ],
)
def test_extract_breed(text, expected):
    assert _extract_breed(text) == expected


# ── unit tests: _extract_age ──────────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("she is 4 years old and a chihuahua", "4 years old"),
        ("lovely little boy, 5 months old, pug", "5 months old"),
        ("she is 2-3 years old, crossbreed", "2-3 years"),
        ("born in September 2025, yorkshire", "1 years old"),  # depends on current year
        ("10 years and 9 months old", "10 years 9 months"),
        ("a 7-year-old crossbreed", "7 years old"),
        ("5-month-old terrier cross puppy", "5 months old"),
        ("just a sweet girl with no age info", ""),
        ("", ""),
    ],
)
def test_extract_age(text, expected):
    result = _extract_age(text)
    if "born" in text.lower():
        # born-year based age depends on current year; just check it's non-empty
        assert result != ""
    else:
        assert result == expected


# ── unit tests: _infer_gender ─────────────────────────────────────

def test_infer_gender_female():
    assert _infer_gender("meet Bella stunning beautiful tiny girl", "Bella") == "Female"


def test_infer_gender_male():
    assert _infer_gender("meet Max lovely little boy, 5 months old", "Max") == "Male"


def test_infer_gender_female_pronouns():
    assert _infer_gender("she is a sweet dog who loves her walks", "Rosie") == "Female"


def test_infer_gender_male_pronouns():
    assert _infer_gender("he is a good boy who loves his toys", "Rex") == "Male"


def test_infer_gender_ambiguous():
    assert _infer_gender("a lovely dog looking for a home", "Pat") == ""


# ── unit tests: _age_months ────────────────────────────────────────

@pytest.mark.parametrize(
    "age_str,expected",
    [
        ("4 years old", 48),
        ("5 months old", 5),
        ("2-3 years", 24),
        ("10 years 9 months", 129),
        ("7 years old", 84),
        ("1 year old", 12),
        ("", 999),
        ("Unknown", 999),
    ],
)
def test_age_months(age_str, expected):
    assert SmallDogRescueChecker._age_months(age_str) == expected


# ── integration: parse() ───────────────────────────────────────────

def test_parse_one_dog():
    checker = SmallDogRescueChecker("data")
    dogs = checker.parse(LISTING_ONE_DOG)
    assert len(dogs) == 1
    assert dogs[0].name == "Bella"
    assert dogs[0].gender == "Female"
    assert dogs[0].status == "Available"
    assert dogs[0].location == "Cliveglen, Landywood Lane, Great Wyrley, Walsall WS6 7AJ"
    assert dogs[0].url == "https://www.smalldogrescue.co.uk/dogs-for-rehoming"
    assert "bella" in dogs[0].photo_url.lower()


def test_parse_two_dogs():
    checker = SmallDogRescueChecker("data")
    dogs = checker.parse(LISTING_TWO_DOGS)
    assert len(dogs) == 2

    bella = [d for d in dogs if d.name == "Bella"][0]
    assert bella.gender == "Female"
    assert bella.age == "4 years old"
    assert bella.breed == "Chihuahua Cross"
    assert "bella" in bella.photo_url.lower()

    max_dog = [d for d in dogs if d.name == "Max"][0]
    assert max_dog.gender == "Male"
    assert max_dog.age == "5 months old"
    assert max_dog.breed == "Pug Cross"
    assert "max" in max_dog.photo_url.lower()


def test_parse_no_dogs():
    checker = SmallDogRescueChecker("data")
    dogs = checker.parse(LISTING_NO_DOGS)
    assert dogs == []


def test_parse_empty_html():
    checker = SmallDogRescueChecker("data")
    assert checker.parse("") == []


def test_parse_all_urls_same():
    """All dogs share the same listing page URL (no individual pages)."""
    checker = SmallDogRescueChecker("data")
    dogs = checker.parse(LISTING_TWO_DOGS)
    for dog in dogs:
        assert dog.url == "https://www.smalldogrescue.co.uk/dogs-for-rehoming"


def test_parse_dog_with_status():
    """Dogs with 'reserved' or 'rehomed' in text are still parsed as Available.

    The status filter doesn't apply — the checker extracts Available for all
    and relies on the text being descriptive rather than having explicit
    status fields.
    """
    checker = SmallDogRescueChecker("data")
    reserved = checker.parse(LISTING_DOG_RESERVED)
    assert len(reserved) == 1
    assert reserved[0].status == "Available"

    rehomed = checker.parse(LISTING_DOG_REHOMED)
    assert len(rehomed) == 1
    assert rehomed[0].status == "Available"


# ── integration: check() flow ──────────────────────────────────────

def test_check_filters_female_puppies(monkeypatch, tmp_path):
    """Only female dogs under 12 months pass the filter."""
    checker = SmallDogRescueChecker(str(tmp_path))

    def fake_fetch(self):
        return LISTING_TWO_DOGS

    monkeypatch.setattr(SmallDogRescueChecker, "fetch", fake_fetch)

    new = checker.check()
    # Bella: Female, 4 years → too old
    # Max: Male, 5 months → wrong gender
    assert len(new) == 0


def test_check_finds_matching_dog(monkeypatch, tmp_path):
    """A female puppy should be returned as new."""
    checker = SmallDogRescueChecker(str(tmp_path))

    puppy_html = """<!DOCTYPE html><html><body>
<div id="img1" class="wixui-image">
<img src="https://static.wixstatic.com/media/rosie.jpg/v1/fill/w_322,h_252/rosie.jpg" width="322" height="252"/>
</div>
<div id="txt1" class="wixui-rich-text">
<h4>meet Rosie sweet little girl, 6 months old, chihuahua cross</h4>
</div></body></html>"""

    def fake_fetch(self):
        return puppy_html

    monkeypatch.setattr(SmallDogRescueChecker, "fetch", fake_fetch)

    new = checker.check()
    assert len(new) == 1
    assert new[0].name == "Rosie"
    assert new[0].gender == "Female"
    assert new[0].age == "6 months old"


def test_check_no_new_on_second_run(monkeypatch, tmp_path):
    """Second run with same data returns empty list."""
    checker = SmallDogRescueChecker(str(tmp_path))

    puppy_html = """<!DOCTYPE html><html><body>
<div id="img1" class="wixui-image">
<img src="https://static.wixstatic.com/media/rosie.jpg/v1/fill/w_322,h_252/rosie.jpg" width="322" height="252"/>
</div>
<div id="txt1" class="wixui-rich-text">
<h4>meet Rosie sweet little girl, 6 months old, chihuahua cross</h4>
</div></body></html>"""

    def fake_fetch(self):
        return puppy_html

    monkeypatch.setattr(SmallDogRescueChecker, "fetch", fake_fetch)

    new1 = checker.check()
    assert len(new1) == 1

    new2 = checker.check()
    assert len(new2) == 0


def test_check_saves_cache_on_first_run(monkeypatch, tmp_path):
    """First run creates a cache file even if no matching dogs found."""
    checker = SmallDogRescueChecker(str(tmp_path))

    # All dogs fail the filter
    def fake_fetch(self):
        return LISTING_TWO_DOGS

    monkeypatch.setattr(SmallDogRescueChecker, "fetch", fake_fetch)

    checker.check()
    cache_path = tmp_path / "small-dog-rescue.txt"
    assert cache_path.exists()
    # Should have saved the filtered set (empty)
    assert cache_path.read_text().strip() == ""


def test_parse_born_year():
    checker = SmallDogRescueChecker("data")
    dogs = checker.parse(LISTING_DOG_WITH_BORN_YEAR)
    assert len(dogs) == 1
    assert dogs[0].name == "Rosie"
    assert dogs[0].gender == "Female"
    assert dogs[0].breed == "Yorkshire Terrier Cross"
    assert dogs[0].age != ""  # born-year age computed at runtime


def test_parse_age_range():
    checker = SmallDogRescueChecker("data")
    dogs = checker.parse(LISTING_DOG_WITH_AGE_RANGE)
    assert len(dogs) == 1
    assert dogs[0].name == "Molly"
    assert dogs[0].age == "2-3 years"
    assert dogs[0].breed == "Crossbreed"


def test_photo_fallback_first_image(monkeypatch, tmp_path):
    """When no image precedes a dog, fall back to first image on page."""
    html = """<!DOCTYPE html><html><body>
<div id="img1" class="wixui-image">
<img src="https://static.wixstatic.com/media/first.jpg/v1/fill/first.jpg" width="100" height="100"/>
</div>
<div id="txt1" class="wixui-rich-text">
<h4>meet Luna lovely girl, spaniel cross</h4>
</div></body></html>"""

    checker = SmallDogRescueChecker(str(tmp_path))
    dogs = checker.parse(html)
    assert len(dogs) == 1
    assert "first" in dogs[0].photo_url
