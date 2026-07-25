"""Tests for Pro Dogs Direct scraper."""

import pytest
from bs4 import BeautifulSoup

from sites.pro_dogs_direct import ProDogsDirectChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestAgeParsing:
    def test_week_old_male(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("12 Week Old Male")
        assert age == "12 Week Old"
        assert gender == "Male"

    def test_week_old_female(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("12 Week Old Female")
        assert age == "12 Week Old"
        assert gender == "Female"

    def test_month_old(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("6 Month Old Female")
        assert age == "6 Month Old"
        assert gender == "Female"

    def test_months_old(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("8 Months Old Female")
        assert age == "8 Months Old"
        assert gender == "Female"

    def test_year_old(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("2 Year Old Female")
        assert age == "2 Year Old"
        assert gender == "Female"

    def test_decimal_year_old(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("2.5 Year Old Female")
        assert age == "2.5 Year Old"
        assert gender == "Female"

    def test_returns_empty_on_unparseable(self):
        checker = ProDogsDirectChecker("/tmp")
        age, gender = checker._parse_age_gender("Unknown text")
        assert age == "Unknown text"
        assert gender == ""


class TestAgeToMonths:
    def test_weeks(self):
        assert ProDogsDirectChecker._age_to_months("12 Week Old") == pytest.approx(2.76, abs=0.1)

    def test_month(self):
        assert ProDogsDirectChecker._age_to_months("6 Month Old") == 6

    def test_months(self):
        assert ProDogsDirectChecker._age_to_months("8 Months Old") == 8

    def test_year(self):
        assert ProDogsDirectChecker._age_to_months("2 Year Old") == 24

    def test_decimal_year(self):
        assert ProDogsDirectChecker._age_to_months("2.5 Year Old") == 30

    def test_one_year(self):
        assert ProDogsDirectChecker._age_to_months("1 Year Old") == 12

    def test_unparseable(self):
        assert ProDogsDirectChecker._age_to_months("???") == 0

    def test_empty(self):
        assert ProDogsDirectChecker._age_to_months("") == 0


class TestStatus:
    def test_available(self):
        html = '<article class="category-dogs clearfix"></article>'
        article = soup(html).select_one("article")
        assert ProDogsDirectChecker._status(article) == "Available"

    def test_applications_closed(self):
        html = '<article class="category-applications-closed clearfix"></article>'
        article = soup(html).select_one("article")
        assert ProDogsDirectChecker._status(article) == "Applications Closed"

    def test_reserved(self):
        html = '<article class="category-reserved-dogs clearfix"></article>'
        article = soup(html).select_one("article")
        assert ProDogsDirectChecker._status(article) == "Reserved"

    def test_rehomed(self):
        html = '<article class="category-rehomed clearfix"></article>'
        article = soup(html).select_one("article")
        assert ProDogsDirectChecker._status(article) == "Rehomed"

    def test_unknown(self):
        html = '<article class="clearfix"></article>'
        article = soup(html).select_one("article")
        assert ProDogsDirectChecker._status(article) == ""


STICKY = (
    '<article class="sticky category-not-ready-for-adoption clearfix">'
    '<header class="entry-header">'
    '<h2 class="entry-title">'
    '<a href="https://prodogsdirect.org.uk/before-you-start/" rel="bookmark">'
    "Before you start...</a></h2></header>"
    '<div class="entry-summary"><p>Intro text</p></div></article>'
)


def _card(href: str, title: str, name: str, age: str, breed: str, location: str,
          category: str = "category-dogs") -> str:
    return (
        f'<article class="{category} clearfix">'
        '<header class="entry-header">'
        f'<h2 class="entry-title"><a href="{href}" rel="bookmark">{title}</a></h2>'
        "</header>"
        '<div class="entry-summary">'
        f"<p><strong>{name}</strong></p>"
        f"<p><strong>{age}</strong></p>"
        f"<p><strong>{breed}</strong></p>"
        f"<p><strong>{location}</strong></p>"
        "</div></article>"
    )


class TestParse:
    def test_empty(self, tmp_path):
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_skips_sticky(self, tmp_path):
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(STICKY) == []

    def test_skips_male(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/peanut-pomeranian/",
            "Peanut - Pomeranian",
            "Peanut", "12 Week Old Male", "Pomeranian",
            "Fostered in Uckfield East Sussex",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_skips_over_12_months(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/luna/",
            "Luna - Cavalier King Charles Spaniel",
            "Luna", "6 Year Old Female", "CKC Spaniel",
            "Fostered in Beckenham Kent",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_female_under_12_months_included(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/bella/",
            "Bella - Cocker Spaniel",
            "Bella", "8 Months Old Female", "Cocker Spaniel",
            "Fostered in Cardiff",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Bella"
        assert d.age == "8 Months Old"
        assert d.gender == "Female"
        assert d.breed == "Cocker Spaniel"
        assert d.location == "Cardiff"
        assert d.url == "https://prodogsdirect.org.uk/bella/"
        assert d.status == "Available"

    def test_female_12_months_exactly_included(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/daisy/",
            "Daisy",
            "Daisy", "1 Year Old Female", "Labrador",
            "Fostered in London",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Daisy"

    def test_applications_closed_status(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/fern/",
            "Fern - APPLICATIONS CLOSED",
            "Fern", "6 Months Old Female", "CKC Spaniel",
            "Fostered in Camberley Surrey",
            category="category-applications-closed",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Fern"
        assert dogs[0].status == "Applications Closed"

    def test_name_extracted_from_title(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/luna-cavalier/",
            "Luna - Cavalier King Charles Spaniel",
            "Luna", "6 Months Old Female", "CKC Spaniel",
            "Fostered in Beckenham Kent",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_location_strips_fostered_prefix(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/bella/",
            "Bella",
            "Bella", "4 Months Old Female", "Spaniel",
            "Fostered in Brighton Sussex",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs[0].location == "Brighton Sussex"

    def test_missing_fields_handled(self, tmp_path):
        html = (
            '<article class="category-dogs clearfix">'
            '<header class="entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://prodogsdirect.org.uk/min/" rel="bookmark">Min</a>'
            "</h2></header>"
            '<div class="entry-summary"></div></article>'
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs == []

    def test_skips_rehomed(self, tmp_path):
        html = _card(
            "https://prodogsdirect.org.uk/old-dog/",
            "Old Dog",
            "Old Dog", "3 Months Old Female", "Poodle",
            "Fostered in London",
            category="category-rehomed",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_multiple_dogs(self, tmp_path):
        card_a = _card(
            "https://prodogsdirect.org.uk/a/", "A",
            "A", "3 Months Old Female", "Poodle", "Fostered in London",
        )
        card_b = _card(
            "https://prodogsdirect.org.uk/b/", "B",
            "B", "8 Weeks Old Female", "Dachshund", "Fostered in Kent",
        )
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(card_a + card_b)
        assert len(dogs) == 2
