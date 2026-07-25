"""Tests for Amicii Dog Rescue site checker (Pets4Homes-based)."""

import json
import re

import pytest

from sites.amicii import (
    BASE_URL,
    AmiciiChecker,
    _age_months_from_str,
    _clean_name,
    _compute_age,
    _extract_breed,
    _extract_gender,
    _resolve_photo,
)


# ── unit tests: _clean_name ────────────────────────────────────────

@pytest.mark.parametrize(
    "title,expected",
    [
        ("💙 RALPHIE - gentle boy needs a quiet home 💙", "Ralphie"),
        ("🐾OWAIN - THE FAMILY DOG YOU'VE BEEN WAITING FOR🐾", "Owain"),
        ("❤️GYPSY - now reserved ❤️", "Gypsy"),
        ("🌼 Daisy - Loyal Companion Seeks Quiet Home 🌼", "Daisy"),
        ("🐾 💙 ATLAS - NOW RESERVED 💙 🐾", "Atlas"),
        ("🏡 Carla ❤️ NOW RESERVED", "Carla"),
        ("🌸 FLO - Now is her time to bloom🌸", "Flo"),
        ("👑 ROCKY 👑 Tiny King Seeks Child-Free Kingdom", "Rocky"),
        ("🐾 ROMA ❤️ SPECIAL GIRL SEEKS SPECIAL HOME 🏡", "Roma"),
        ("🐾 Buddy: adventure dog, cuddle expert ❤️", "Buddy"),
        ("SWEET OSCAR READY FOR HIS FOREVER FAMILY", "Sweet"),
        ("💛🐾 OLWEN 🐾💛", "Olwen"),
        ("🐾 MAX - Professional Napper Seeks Sofa 🐾", "Max"),
        ("🐾 Cedric – Stunning, Loyal Boy", "Cedric"),
        ("Buster – Big Heart, Loyal and Ready to Bond", "Buster"),
        ("🍀 CLOVER - now reserved 🤞🍀", "Clover"),
        ("❤️ DOUGIE ❤️ Big Dog, Bigger Heart", "Dougie"),
        ("TEDDY - SINGLE AND READY TO MINGLE", "Teddy"),
        ("🐾💙 DONNIE WAITING FOR HIS CHANCE 💙🐾", "Donnie"),
        ("🐶 MINNIE - SMALL, BLONDE, FEISTY AND FULL OF LOVE", "Minnie"),
        ("🐾 Charlotte🌟Golden Girl Seeks Sofa & Sunshine ☀️", "Charlotte"),
        ("🐾 Tommy 💙 Your Dog's New Best Friend", "Tommy"),
    ],
)
def test_clean_name(title, expected):
    assert _clean_name(title) == expected


# ── unit tests: _extract_breed ─────────────────────────────────────

def test_extract_breed_mixed():
    attrs = [{"key": "breed", "value": "pets.dogs.breed.mixedBreed"}]
    assert _extract_breed(attrs) == "Mixed Breed"


def test_extract_breed_specific():
    attrs = [{"key": "breed", "value": "pets.dogs.breed.labradorRetriever"}]
    assert _extract_breed(attrs) == "Labrador Retriever"


def test_extract_breed_missing():
    assert _extract_breed([]) == ""


# ── unit tests: _extract_gender ────────────────────────────────────

def test_extract_gender_male():
    attrs = [
        {"key": "numberOfMales", "value": "1"},
        {"key": "numberOfFemales", "value": "0"},
    ]
    assert _extract_gender(attrs) == "Male"


def test_extract_gender_female():
    attrs = [
        {"key": "numberOfMales", "value": "0"},
        {"key": "numberOfFemales", "value": "1"},
    ]
    assert _extract_gender(attrs) == "Female"


def test_extract_gender_neither():
    attrs = [
        {"key": "numberOfMales", "value": "0"},
        {"key": "numberOfFemales", "value": "0"},
    ]
    assert _extract_gender(attrs) == ""


def test_extract_gender_missing():
    assert _extract_gender([]) == ""


def test_extract_gender_male_invalid_female():
    """Male value is non-numeric, female is 0 — should be empty."""
    attrs = [
        {"key": "numberOfMales", "value": "abc"},
        {"key": "numberOfFemales", "value": "0"},
    ]
    assert _extract_gender(attrs) == ""


# ── unit tests: _compute_age ───────────────────────────────────────

def test_compute_age_years():
    # DOB: 2021-08-23 (timestamp ms)
    # In 2026-07, that's ~4 years 11 months
    attrs = [{"key": "dateOfBirth", "value": "1629759600000"}]
    age = _compute_age(attrs)
    assert "4 years" in age or "5 years" in age


def test_compute_age_months():
    # DOB: ~5 months ago
    import time
    five_months_ago = int((time.time() - 5 * 30 * 24 * 3600) * 1000)
    attrs = [{"key": "dateOfBirth", "value": str(five_months_ago)}]
    age = _compute_age(attrs)
    assert "month" in age
    assert "year" not in age


def test_compute_age_recent():
    """Very recent DOB should floor at 1 month."""
    import time
    one_week_ago = int((time.time() - 7 * 24 * 3600) * 1000)
    attrs = [{"key": "dateOfBirth", "value": str(one_week_ago)}]
    age = _compute_age(attrs)
    assert age == "1 month"


def test_compute_age_missing():
    assert _compute_age([]) == ""


def test_compute_age_invalid():
    attrs = [{"key": "dateOfBirth", "value": "not_a_number"}]
    assert _compute_age(attrs) == ""


# ── unit tests: _resolve_photo ─────────────────────────────────────

def test_resolve_photo_replaces_placeholder():
    url = "https://assets.pets4homes.co.uk/originalImages/abc123/##NAME##.jpeg"
    resolved = _resolve_photo(url)
    assert resolved == "https://assets.pets4homes.co.uk/originalImages/abc123/image.jpeg"


def test_resolve_photo_empty():
    assert _resolve_photo("") == ""


def test_resolve_photo_no_placeholder():
    url = "https://assets.pets4homes.co.uk/originalImages/abc123/dog.jpeg"
    assert _resolve_photo(url) == url


# ── unit tests: _age_months_from_str ───────────────────────────────

def test_age_months_years():
    assert _age_months_from_str("2 years") == 24


def test_age_months_months():
    assert _age_months_from_str("8 months") == 8


def test_age_months_combined():
    assert _age_months_from_str("1 year") == 12


def test_age_months_empty():
    assert _age_months_from_str("") == 999


def test_age_months_unparseable():
    assert _age_months_from_str("adult") == 999


# ── fixtures ───────────────────────────────────────────────────────

def _make_item(
    title="Buddy",
    slug="abc123-buddy",
    males=1,
    females=0,
    dob="1704067200000",  # 2024-01-01
    breed_val="pets.dogs.breed.mixedBreed",
    town="Worcester",
    region="Worcestershire",
    status="Active",
    photo_id="abc123",
) -> dict:
    return {
        "id": "test-id",
        "slug": slug,
        "status": status,
        "attributes": [
            {"key": "breed", "value": breed_val},
            {"key": "numberOfMales", "value": str(males)},
            {"key": "numberOfFemales", "value": str(females)},
            {"key": "dateOfBirth", "value": dob},
        ],
        "generalInformation": {
            "title": title,
            "price": {"amount": 180, "currency": "GBP"},
        },
        "profileImage": {
            "originalImage": (
                f"https://assets.pets4homes.co.uk/originalImages/{photo_id}/##NAME##.jpeg"
            ),
        },
        "locationV3": {
            "postalTown": town,
            "adminRegion1": "England",
            "adminRegion2": region,
        },
        "displayDescription": "A lovely dog looking for a home.",
    }


PAGE_1_ITEMS = [
    _make_item("💙 RALPHIE - gentle boy needs a quiet home 💙", "ralphie-slug", males=1, females=0, town="Kidderminster"),
    _make_item("🐾OWAIN - THE FAMILY DOG YOU'VE BEEN WAITING FOR🐾", "owain-slug", males=1, females=0, town="Malvern"),
    _make_item("❤️GYPSY - now reserved ❤️", "gypsy-slug", males=0, females=1, town="Derby", region="Derby", status="Active"),
    _make_item("🌼 Daisy - Loyal Companion Seeks Quiet Home 🌼", "daisy-slug", males=1, females=0, town="Worcester"),
]


def _make_next_json(items, page=1, total_pages=6, total=22):
    """Build a fake __NEXT_DATA__ response for a page."""
    return json.dumps({
        "props": {
            "pageProps": {
                "listings": {
                    "items": items,
                    "metadata": {"page": page, "totalPages": total_pages, "total": total},
                },
            },
        },
    })


def _wrap_html(json_str: str) -> str:
    """Wrap JSON in a minimal HTML page with __NEXT_DATA__ script."""
    return f'<html><head></head><body><script id="__NEXT_DATA__" type="application/json">{json_str}</script></body></html>'


# ── AmiciiChecker tests ────────────────────────────────────────────

class TestAmiciiChecker:
    """Tests for the AmiciiChecker class."""

    def test_extract_json(self):
        html = _wrap_html(_make_next_json(PAGE_1_ITEMS))
        data = AmiciiChecker._extract_json(html)
        items = data["props"]["pageProps"]["listings"]["items"]
        assert len(items) == 4

    def test_extract_json_no_match(self):
        assert AmiciiChecker._extract_json("<html></html>") == {}

    def test_parse_basic(self):
        raw = json.dumps(PAGE_1_ITEMS)
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(raw)
        assert len(dogs) == 4

    def test_parse_names(self):
        raw = json.dumps(PAGE_1_ITEMS)
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(raw)
        names = {d.name for d in dogs}
        assert names == {"Ralphie", "Owain", "Gypsy", "Daisy"}

    def test_parse_genders(self):
        raw = json.dumps(PAGE_1_ITEMS)
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(raw)
        genders = {(d.name, d.gender) for d in dogs}
        assert ("Ralphie", "Male") in genders
        assert ("Owain", "Male") in genders
        assert ("Gypsy", "Female") in genders
        # Daisy: attributes say M=1 F=0 → Male
        assert ("Daisy", "Male") in genders

    def test_parse_reserved(self):
        """Dogs with 'reserved' in title should be marked Reserved."""
        items = [
            _make_item("🍀 CLOVER - now reserved 🤞🍀", "clover-slug", males=0, females=1),
            _make_item("BUDDY", "buddy-slug", males=1, females=0),
        ]
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(json.dumps(items))
        statuses = {(d.name, d.status) for d in dogs}
        assert ("Clover", "Reserved") in statuses
        assert ("Buddy", "Available") in statuses

    def test_parse_skips_inactive(self):
        items = [
            _make_item("ActiveDog - lovely pup", "active-slug", status="Active"),
            _make_item("DraftDog - not ready", "draft-slug", status="Draft"),
        ]
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(json.dumps(items))
        assert len(dogs) == 1
        assert dogs[0].name == "ActiveDog"

    def test_parse_location(self):
        items = [_make_item("Buddy", "buddy-slug", town="Worcester", region="Worcestershire")]
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(json.dumps(items))
        assert dogs[0].location == "Worcester, Worcestershire"

    def test_parse_photo_url(self):
        items = [_make_item("Buddy", "buddy-slug", photo_id="abc123")]
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(json.dumps(items))
        assert "##NAME##" not in dogs[0].photo_url
        assert dogs[0].photo_url == "https://assets.pets4homes.co.uk/originalImages/abc123/image.jpeg"

    def test_parse_detail_url(self):
        items = [_make_item("Buddy", "abc123-buddy")]
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(json.dumps(items))
        assert dogs[0].url == "https://www.pets4homes.co.uk/adoption/dogs/abc123-buddy/"

    def test_parse_breed(self):
        items = [_make_item("Buddy", "buddy-slug")]
        checker = AmiciiChecker("/tmp/test-amicii")
        dogs = checker.parse(json.dumps(items))
        assert dogs[0].breed == "Mixed Breed"

    def test_fetch_multi_page(self, monkeypatch):
        """Simulate 2 pages with fetch()."""
        page1_items = [_make_item(f"Dog{i}", f"slug-{i}") for i in range(1, 5)]
        page2_items = [_make_item(f"Dog{i}", f"slug-{i}") for i in range(5, 7)]

        class MockResponse:
            def __init__(self, text):
                self._text = text
            @property
            def text(self):
                return self._text
            def raise_for_status(self):
                pass

        responses = {
            BASE_URL: MockResponse(_wrap_html(_make_next_json(page1_items, page=1, total_pages=2, total=6))),
            f"{BASE_URL}?page=2": MockResponse(_wrap_html(_make_next_json(page2_items, page=2, total_pages=2, total=6))),
        }

        def mock_get(url, headers=None, timeout=None):
            return responses[url]

        monkeypatch.setattr("requests.get", mock_get)

        checker = AmiciiChecker("/tmp/test-amicii")
        raw = checker.fetch()
        dogs = checker.parse(raw)
        assert len(dogs) == 6

    def test_bypass_distance_filter(self):
        checker = AmiciiChecker("/tmp/test-amicii")
        assert checker.bypass_distance_filter is True


# ── BASE_URL constant ──────────────────────────────────────────────

def test_base_url():
    assert "pets4homes.co.uk" in BASE_URL
    assert "amicii-dog-rescue" in BASE_URL
