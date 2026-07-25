"""Tests for Starfish Dog Rescue site checker."""
# ruff: noqa: RUF001  # en-dashes in test data match real site content

from sites.starfish import (
    StarfishChecker,
    _extract_age,
    _parse_title,
)


class TestParseTitle:
    def test_standard_format(self):
        name, breed, gender = _parse_title("Bella – French Bulldog – (F)")
        assert name == "Bella"
        assert breed == "French Bulldog"
        assert gender == "Female"

    def test_male(self):
        name, breed, gender = _parse_title("Sebastian – Poodle – (M)")
        assert name == "Sebastian"
        assert breed == "Poodle"
        assert gender == "Male"

    def test_multi_word_name(self):
        name, breed, gender = _parse_title("Mr Fluffy – Crossbreed – (M)")
        assert name == "Mr Fluffy"
        assert breed == "Crossbreed"
        assert gender == "Male"

    def test_fallback_no_emdash(self):
        name, breed, gender = _parse_title("Buddy")
        assert name == "Buddy"
        assert breed == ""
        assert gender == ""


class TestExtractAge:
    def test_month_old(self):
        assert _extract_age("Bella – 9 month old French Bulldog") == "9 months"

    def test_month_old_hyphenated(self):
        assert _extract_age("Sebastian is a 19-month-old Toy Poodle") == "19 months"

    def test_year_old(self):
        assert _extract_age("Max is 3 years old and loves walks") == "3 years"

    def test_year_old_hyphenated(self):
        assert _extract_age("A 5-year-old Labrador") == "5 years"

    def test_aged_months(self):
        assert _extract_age("aged 6 months") == "6 months"

    def test_aged_years(self):
        assert _extract_age("Rover aged 2 years") == "2 years"

    def test_singular_month(self):
        assert _extract_age("1 month old puppy") == "1 month"

    def test_singular_year(self):
        assert _extract_age("1 year old dog") == "1 year"

    def test_no_age(self):
        assert _extract_age("A lovely dog looking for a home") == ""

    def test_first_match_wins(self):
        # "10 months old" appears first
        assert _extract_age("10 months old, nearly 1 year old") == "10 months"


class TestParse:
    def test_no_containers(self, tmp_path):
        c = StarfishChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_empty_available_section(self, tmp_path):
        html = """
        <div class="dp-dfg-container">
            <div class="dp-dfg-items"></div>
        </div>
        """
        c = StarfishChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_only_available_dogs_returned(self, tmp_path):
        """Container 0 dogs are returned; container 1+2 are ignored."""
        listing_html = (
            # Container 0 — available
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Bella – French Bulldog – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Read More</a></div></article>"
            "</div></div>"
            # Container 1 — not ready (should be ignored)
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/winston-labrador-m">'
            "Winston – Labrador – (M)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/winston-labrador-m">'
            "Read More</a></div></article>"
            "</div></div>"
            # Container 2 — reserved (should be ignored)
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/cilla-crossbreed-f">'
            "Cilla – Crossbreed – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/cilla-crossbreed-f">'
            "Read More</a></div></article>"
            "</div></div>"
        )

        detail_html = (
            "<html><body>"
            '<h1>Bella – French Bulldog – (F)</h1>'
            "<p>Bella – 9 month old French Bulldog</p>"
            '<img src="https://starfishdogrescue.co.uk/'
            'wp-content/uploads/2026/07/bella.jpg" />'
            "</body></html>"
        )

        c = StarfishChecker(str(tmp_path))

        # Override _fetch_detail to return canned detail HTML
        original_fetch = c._fetch_detail
        c._fetch_detail = lambda url: detail_html  # type: ignore[method-assign]

        try:
            dogs = c.parse(listing_html)
            assert len(dogs) == 1
            d = dogs[0]
            assert d.name == "Bella"
            assert d.breed == "French Bulldog"
            assert d.gender == "Female"
            assert d.age == "9 months"
            assert d.status == "Available"
            assert d.location == "Gloucestershire"
            assert d.url == "https://starfishdogrescue.co.uk/bella-french-bulldog-f"
            assert "wp-content/uploads/2026/07/bella.jpg" in d.photo_url
        finally:
            c._fetch_detail = original_fetch  # type: ignore[method-assign]

    def test_male_dog(self, tmp_path):
        listing_html = (
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/sebastian-poodle-m">'
            "Sebastian – Poodle – (M)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/sebastian-poodle-m">'
            "Read More</a></div></article>"
            "</div></div>"
        )

        detail_html = (
            "<html><body>"
            '<h1>Sebastian – Poodle – (M)</h1>'
            "<p>Sebastian is a 19-month-old Toy Poodle boy</p>"
            "</body></html>"
        )

        c = StarfishChecker(str(tmp_path))
        original_fetch = c._fetch_detail
        c._fetch_detail = lambda url: detail_html  # type: ignore[method-assign]

        try:
            dogs = c.parse(listing_html)
            assert len(dogs) == 1
            assert dogs[0].name == "Sebastian"
            assert dogs[0].breed == "Poodle"
            assert dogs[0].gender == "Male"
            assert dogs[0].age == "19 months"
        finally:
            c._fetch_detail = original_fetch  # type: ignore[method-assign]

    def test_duplicate_urls_deduplicated(self, tmp_path):
        """Duplicate URLs within the available section are deduplicated."""
        listing_html = (
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Bella – French Bulldog – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Read More</a></div></article>"
            # Duplicate: same URL again
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Bella – French Bulldog – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Read More</a></div></article>"
            "</div></div>"
        )

        detail_html = (
            "<html><body>"
            "<p>9 month old</p>"
            "</body></html>"
        )

        c = StarfishChecker(str(tmp_path))
        original_fetch = c._fetch_detail
        c._fetch_detail = lambda url: detail_html  # type: ignore[method-assign]

        try:
            dogs = c.parse(listing_html)
            assert len(dogs) == 1
        finally:
            c._fetch_detail = original_fetch  # type: ignore[method-assign]

    def test_multiple_available_dogs(self, tmp_path):
        listing_html = (
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Bella – French Bulldog – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Read More</a></div></article>"
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/sebastian-poodle-m">'
            "Sebastian – Poodle – (M)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/sebastian-poodle-m">'
            "Read More</a></div></article>"
            "</div></div>"
        )

        def mock_fetch(url):
            if "bella" in url:
                return "<html><body><p>9 month old</p></body></html>"
            return "<html><body><p>19-month-old</p></body></html>"

        c = StarfishChecker(str(tmp_path))
        original_fetch = c._fetch_detail
        c._fetch_detail = mock_fetch  # type: ignore[method-assign]

        try:
            dogs = c.parse(listing_html)
            assert len(dogs) == 2
            assert {d.name for d in dogs} == {"Bella", "Sebastian"}
        finally:
            c._fetch_detail = original_fetch  # type: ignore[method-assign]

    def test_photo_url_found(self, tmp_path):
        listing_html = (
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Bella – French Bulldog – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Read More</a></div></article>"
            "</div></div>"
        )

        detail_html = (
            "<html><body>"
            "<p>9 month old</p>"
            '<img src="https://starfishdogrescue.co.uk/'
            'wp-content/uploads/2026/07/bella.jpg" />'
            "</body></html>"
        )

        c = StarfishChecker(str(tmp_path))
        original_fetch = c._fetch_detail
        c._fetch_detail = lambda url: detail_html  # type: ignore[method-assign]

        try:
            dogs = c.parse(listing_html)
            assert len(dogs) == 1
            assert "wp-content/uploads/2026/07/bella.jpg" in dogs[0].photo_url
        finally:
            c._fetch_detail = original_fetch  # type: ignore[method-assign]

    def test_no_age_found(self, tmp_path):
        listing_html = (
            '<div class="dp-dfg-container">'
            '<div class="dp-dfg-items">'
            '<article class="dp-dfg-item">'
            '<div class="dp-dfg-header entry-header">'
            '<h2 class="entry-title">'
            '<a href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Bella – French Bulldog – (F)</a></h2></div>"
            '<div class="read-more-wrapper">'
            '<a class="dp-dfg-more-button" '
            'href="https://starfishdogrescue.co.uk/bella-french-bulldog-f">'
            "Read More</a></div></article>"
            "</div></div>"
        )

        detail_html = (
            "<html><body>"
            "<p>A lovely dog looking for a home</p>"
            "</body></html>"
        )

        c = StarfishChecker(str(tmp_path))
        original_fetch = c._fetch_detail
        c._fetch_detail = lambda url: detail_html  # type: ignore[method-assign]

        try:
            dogs = c.parse(listing_html)
            assert len(dogs) == 1
            assert dogs[0].age == ""
        finally:
            c._fetch_detail = original_fetch  # type: ignore[method-assign]
