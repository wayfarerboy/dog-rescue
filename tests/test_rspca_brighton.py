from sites.rspca_brighton import RSPCABrightonChecker


class TestParseAgeMonths:
    def test_just_years(self):
        assert RSPCABrightonChecker._parse_age_months("4 years") == 48

    def test_one_year(self):
        assert RSPCABrightonChecker._parse_age_months("1 year") == 12

    def test_years_approx(self):
        assert RSPCABrightonChecker._parse_age_months("2 years approx.") == 24

    def test_just_months(self):
        assert RSPCABrightonChecker._parse_age_months("6 months") == 6

    def test_months_approx(self):
        assert RSPCABrightonChecker._parse_age_months("18 months approx.") == 18

    def test_range_years(self):
        """Lower bound of year range."""
        assert RSPCABrightonChecker._parse_age_months("2-3 years approx.") == 24

    def test_range_years_and_months(self):
        """Mixed range: lower bound is in months."""
        assert RSPCABrightonChecker._parse_age_months("18 months \u2013 2 years approx.") == 18

    def test_range_both_years(self):
        assert RSPCABrightonChecker._parse_age_months("3-4 years approx.") == 36

    def test_empty(self):
        assert RSPCABrightonChecker._parse_age_months("") == 0

    def test_invalid(self):
        assert RSPCABrightonChecker._parse_age_months("unknown") == 0


class TestNormalizeGender:
    def test_female(self):
        assert RSPCABrightonChecker._normalize_gender("Female") == "Female"

    def test_spayed_female(self):
        assert RSPCABrightonChecker._normalize_gender("Spayed Female") == "Female"

    def test_male(self):
        assert RSPCABrightonChecker._normalize_gender("Male") == "Male"

    def test_neutered_male(self):
        assert RSPCABrightonChecker._normalize_gender("Neutered Male") == "Male"

    def test_typo_make(self):
        """'Make' is a known typo for 'Male' on this site."""
        assert RSPCABrightonChecker._normalize_gender("Make") == "Male"

    def test_empty(self):
        assert RSPCABrightonChecker._normalize_gender("") == ""


class TestParseListing:
    """Tests for parsing the listing page HTML."""

    @staticmethod
    def _make_card(name, status, href):
        excerpt = f'<p class="et_pb_portfolio_excerpt">{status}</p>' if status else ""
        return f"""
        <div class="post-12345 project type-project et_pb_portfolio_item et_pb_grid_item">
          <a href="{href}" title="{name}">
            <span class="et_portfolio_image">
              <img alt="{name}" src="https://example.org/photos/{name.lower()}.jpg"/>
              <span class="et_overlay"></span>
            </span>
          </a>
          <h3 class="et_pb_module_header"><a href="{href}" title="{name}">{name}</a></h3>
          {excerpt}
        </div>"""

    @staticmethod
    def _detail_html(breed, age, gender, location="Brighton Centre"):
        return f"""
        <div class="et_pb_post_content">
          <p><strong>Age:</strong><br/>{age}</p>
          <p><strong>Sex:</strong><br/>{gender}</p>
          <p><strong>Breed:</strong><br/>{breed}</p>
          <p><strong>Location:</strong><br/>{location}</p>
        </div>"""

    def test_no_cards(self, tmp_path):
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: ""
        assert c.parse("<html></html>") == []

    def test_female_puppy_included(self, tmp_path):
        html = self._make_card(
            "Luna", "New arrival",
            "https://rspca-brighton.org.uk/project/luna/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Spaniel", "6 months", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.age == "6 months"
        assert d.gender == "Female"
        assert d.breed == "Spaniel"
        assert d.location == "Brighton Centre"
        assert d.url == "https://rspca-brighton.org.uk/project/luna/"
        assert d.status == "New arrival"
        assert d.photo_url == "https://example.org/photos/luna.jpg"

    def test_no_status_card(self, tmp_path):
        """Cards without excerpt paragraph are treated as available."""
        html = self._make_card(
            "Bella", "",  # no status
            "https://rspca-brighton.org.uk/project/bella/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Lab", "5 months", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].status == "Available"

    def test_reserved_skipped(self, tmp_path):
        html = self._make_card(
            "Rex", "Reserved",
            "https://rspca-brighton.org.uk/project/rex/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Lab", "4 months", "Male")
        assert c.parse(html) == []

    def test_no_more_applications_skipped(self, tmp_path):
        html = self._make_card(
            "Spot", "No more applications being taken",
            "https://rspca-brighton.org.uk/project/spot/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Terrier", "5 months", "Male")
        assert c.parse(html) == []

    def test_male_filtered_out(self, tmp_path):
        html = self._make_card(
            "Rex", "New arrival",
            "https://rspca-brighton.org.uk/project/rex/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Labrador", "4 months", "Male")
        assert c.parse(html) == []

    def test_spayed_female_included(self, tmp_path):
        html = self._make_card(
            "Daisy", "",
            "https://rspca-brighton.org.uk/project/daisy/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Bulldog", "8 months", "Spayed Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].gender == "Female"

    def test_make_typo_treated_as_male(self, tmp_path):
        html = self._make_card(
            "Loon", "New arrival",
            "https://rspca-brighton.org.uk/project/loon/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Staffie", "1 year", "Make")
        assert c.parse(html) == []

    def test_over_12_months_filtered(self, tmp_path):
        html = self._make_card(
            "Bella", "New arrival",
            "https://rspca-brighton.org.uk/project/bella/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Spaniel", "2 years", "Female")
        assert c.parse(html) == []

    def test_exactly_12_months_included(self, tmp_path):
        html = self._make_card(
            "Jitterbug", "New arrival",
            "https://rspca-brighton.org.uk/project/jitterbug/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Pocket bully", "1 year approx.", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].age == "1 year approx."

    def test_age_range_lower_bound_over_12_filtered(self, tmp_path):
        """'18 months - 2 years approx.' lower bound is 18 months - filtered out."""
        html = self._make_card(
            "Lark", "",
            "https://rspca-brighton.org.uk/project/lark/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html(
            "Husky cross", "18 months \u2013 2 years approx.", "Female",
        )
        assert c.parse(html) == []

    def test_detail_fetch_failure_skipped(self, tmp_path):
        html = self._make_card(
            "Ghost", "New arrival",
            "https://rspca-brighton.org.uk/project/ghost/",
        )
        c = RSPCABrightonChecker(str(tmp_path))

        def _failing_fetch(url):
            raise Exception("network error")

        c._fetch_detail = _failing_fetch
        assert c.parse(html) == []

    def test_multiple_cards_mixed(self, tmp_path):
        html = (
            self._make_card("Rex", "New arrival",
                            "https://rspca-brighton.org.uk/project/rex/")
            + self._make_card("Luna", "New arrival",
                              "https://rspca-brighton.org.uk/project/luna/")
            + self._make_card("Bella", "Reserved",
                              "https://rspca-brighton.org.uk/project/bella/")
            + self._make_card("Spot", "No more applications being taken",
                              "https://rspca-brighton.org.uk/project/spot/")
        )
        c = RSPCABrightonChecker(str(tmp_path))

        def _fake_detail(url):
            if "luna" in url:
                return self._detail_html("Spaniel", "5 months", "Female")
            if "rex" in url:
                return self._detail_html("Terrier", "4 months", "Male")
            return self._detail_html("Lab", "6 months", "Male")

        c._fetch_detail = _fake_detail
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_breed_missing_on_detail(self, tmp_path):
        html = self._make_card(
            "Mystery", "",
            "https://rspca-brighton.org.uk/project/mystery/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("", "3 months", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].breed == ""

    def test_photo_url_from_img(self, tmp_path):
        html = self._make_card(
            "Dot", "New arrival",
            "https://rspca-brighton.org.uk/project/dot/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html("Terrier", "3 months", "Female")
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].photo_url == "https://example.org/photos/dot.jpg"
        assert dogs[0].location == "Brighton Centre"

    def test_location_extracted(self, tmp_path):
        """Location field is extracted from detail page."""
        html = self._make_card(
            "Maple", "",
            "https://rspca-brighton.org.uk/project/maple/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        c._fetch_detail = lambda url: self._detail_html(
            "Collie cross", "4 months", "Female", location="Patcham Animal Centre"
        )
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].location == "Patcham Animal Centre"

    def test_location_missing_on_detail(self, tmp_path):
        """Location defaults to empty string when not on detail page."""
        html = self._make_card(
            "Ghost", "",
            "https://rspca-brighton.org.uk/project/ghost/",
        )
        c = RSPCABrightonChecker(str(tmp_path))
        # Detail page without Location field
        detail = """
        <div class="et_pb_post_content">
          <p><strong>Age:</strong><br/>3 months</p>
          <p><strong>Sex:</strong><br/>Female</p>
          <p><strong>Breed:</strong><br/>Terrier</p>
        </div>"""
        c._fetch_detail = lambda url: detail
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].location == ""
