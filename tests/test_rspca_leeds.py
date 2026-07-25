from sites.rspca_leeds import RSPCALeedsChecker


class TestParseAgeMonths:
    def test_just_years(self):
        assert RSPCALeedsChecker._parse_age_months("4 years") == 48

    def test_one_year(self):
        assert RSPCALeedsChecker._parse_age_months("1 year") == 12

    def test_years_and_months(self):
        assert RSPCALeedsChecker._parse_age_months("1 year 7 months") == 19

    def test_years_and_months_approx(self):
        assert RSPCALeedsChecker._parse_age_months("1 year 7 months  (approx)") == 19

    def test_just_months(self):
        assert RSPCALeedsChecker._parse_age_months("6 months") == 6

    def test_empty(self):
        assert RSPCALeedsChecker._parse_age_months("") == 0

    def test_invalid(self):
        assert RSPCALeedsChecker._parse_age_months("unknown") == 0


class TestParseListing:
    """Tests for parsing the listing page HTML."""

    def _make_card(self, name, age, gender, href):
        return f"""
        <article class="wpgb-card wpgb-card-4">
          <div class="wpgb-card-wrapper">
            <div class="wpgb-card-inner">
              <div class="wpgb-card-media wpgb-scheme-light">
                <div class="wpgb-card-media-thumbnail">
                  <div class="wpgb-lazy-load"
                       data-wpgb-src="https://example.org/photos/{name.lower()}.jpg">
                  </div>
                </div>
                <a class="wpgb-card-layer-link" href="{href}"></a>
              </div>
              <div class="wpgb-card-content wpgb-scheme-light">
                <div class="wpgb-card-body">
                  <h3 class="wpgb-block-3"><a href="{href}">{name}</a></h3>
                </div>
                <div class="wpgb-card-footer">
                  <div class="wpgb-block-1">{age}</div>
                  <div class="wpgb-block-2">{gender}</div>
                </div>
              </div>
            </div>
          </div>
        </article>"""

    def _detail_html(self, breed, age="", gender=""):
        rows = ""
        if breed:
            rows += f'<tr class="about-me-row"><th>Breed:</th><td>{breed}</td></tr>'
        if age:
            rows += f'<tr class="about-me-row"><th>Age:</th><td>{age}</td></tr>'
        if gender:
            rows += f'<tr class="about-me-row"><th>Gender:</th><td>{gender}</td></tr>'
        return f"""
        <div class="rspca-pet-post dog">
          <div class="container single-pet">
            <table class="about-me">
              <tbody>{rows}</tbody>
            </table>
          </div>
        </div>"""

    def test_no_cards(self, tmp_path):
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: ""
        assert c.parse("<html></html>") == []

    def test_female_puppy_included(self, tmp_path):
        html = self._make_card(
            "Luna", "6 months", "female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/luna/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Spaniel", "6 months", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.age == "6 months"
        assert d.gender == "Female"
        assert d.breed == "Spaniel"
        assert d.url == "https://www.rspcaleedsandwakefield.org.uk/dogs/luna/"
        assert d.photo_url == "https://example.org/photos/luna.jpg"

    def test_male_filtered_out(self, tmp_path):
        html = self._make_card(
            "Rex", "4 months", "male",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/rex/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Labrador")
        assert c.parse(html) == []

    def test_over_12_months_filtered(self, tmp_path):
        html = self._make_card(
            "Bella", "2 years", "female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/bella/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Spaniel")
        assert c.parse(html) == []

    def test_exactly_12_months_included(self, tmp_path):
        html = self._make_card(
            "Daisy", "1 year", "female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/daisy/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Terrier")
        dogs = c.parse(html)
        assert len(dogs) == 1

    def test_over_12_months_detail_age_overrides(self, tmp_path):
        """Listing says '1 year' but detail says '1 year 7 months' — should be filtered."""
        html = self._make_card(
            "Tia", "1 year", "female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/tia/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Beagle x", "1 year 7 months", "Female")
        dogs = c.parse(html)
        assert dogs == []

    def test_age_from_detail_used_for_display(self, tmp_path):
        """When detail page has more precise age, use it in the Dog object."""
        html = self._make_card(
            "Pup", "0 years", "female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/pup/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Mixed", "3 months", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].age == "3 months"

    def test_multiple_cards_mixed(self, tmp_path):
        html = (
            self._make_card("Rex", "4 months", "male",
                            "https://www.rspcaleedsandwakefield.org.uk/dogs/rex/")
            + self._make_card("Luna", "5 months", "female",
                              "https://www.rspcaleedsandwakefield.org.uk/dogs/luna/")
            + self._make_card("Bella", "3 years", "female",
                              "https://www.rspcaleedsandwakefield.org.uk/dogs/bella/")
        )
        c = RSPCALeedsChecker(str(tmp_path))

        def _fake_detail(url):
            if "luna" in url:
                return self._detail_html("Spaniel")
            if "bella" in url:
                return self._detail_html("Lab")
            return self._detail_html("Terrier")

        c._fetch_detail = _fake_detail
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_breed_missing_on_detail(self, tmp_path):
        html = self._make_card(
            "Mystery", "3 months", "female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/mystery/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].breed == ""

    def test_photo_url_fallback_noscript(self, tmp_path):
        html = """
        <article class="wpgb-card wpgb-card-4">
          <div class="wpgb-card-wrapper">
            <div class="wpgb-card-inner">
              <div class="wpgb-card-media wpgb-scheme-light">
                <div class="wpgb-card-media-thumbnail">
                  <noscript>
                    <img class="wpgb-noscript-img" src="https://example.org/noscript.jpg"/>
                  </noscript>
                </div>
                <a class="wpgb-card-layer-link"
                   href="https://www.rspcaleedsandwakefield.org.uk/dogs/dot/"></a>
              </div>
              <div class="wpgb-card-content wpgb-scheme-light">
                <div class="wpgb-card-body">
                  <h3 class="wpgb-block-3"><a href="/dogs/dot/">Dot</a></h3>
                </div>
                <div class="wpgb-card-footer">
                  <div class="wpgb-block-1">3 months</div>
                  <div class="wpgb-block-2">female</div>
                </div>
              </div>
            </div>
          </div>
        </article>"""
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Terrier")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].photo_url == "https://example.org/noscript.jpg"

    def test_capitalized_gender_normalized(self, tmp_path):
        html = self._make_card(
            "Belle", "4 months", "Female",
            "https://www.rspcaleedsandwakefield.org.uk/dogs/belle/",
        )
        c = RSPCALeedsChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Poodle")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].gender == "Female"
