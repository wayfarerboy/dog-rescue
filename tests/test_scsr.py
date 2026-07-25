from bs4 import BeautifulSoup

from sites.scsr import SCSRChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestHelpers:
    def test_text(self):
        assert SCSRChecker._text(soup("<div><h3>Rover</h3></div>"), "h3") == "Rover"

    def test_text_missing(self):
        assert SCSRChecker._text(soup("<div></div>"), "h3") == ""

    def test_status(self):
        html = '<article><div class="scsr-modern-status"><i></i>Available</div></article>'
        article = soup(html).select_one("article")
        assert SCSRChecker( "/tmp")._status(article) == "Available"

    def test_status_missing(self):
        article = soup("<article></article>").select_one("article")
        assert SCSRChecker("/tmp")._status(article) == ""

    def test_profile_link(self):
        html = '<article><a class="scsr-modern-main-btn" href="https://example.org/dogs/bella">View</a></article>'
        article = soup(html).select_one("article")
        assert SCSRChecker("/tmp")._profile_link(article) == "https://example.org/dogs/bella"

    def test_profile_link_fallback(self):
        html = '<article><a href="https://secondchancespanielrescue.org.uk/dogs/max">View</a></article>'
        article = soup(html).select_one("article")
        assert SCSRChecker("/tmp")._profile_link(article) == (
            "https://secondchancespanielrescue.org.uk/dogs/max"
        )

    def test_profile_link_missing(self):
        article = soup("<article></article>").select_one("article")
        assert SCSRChecker("/tmp")._profile_link(article) == ""

    def test_info_field(self):
        html = """
        <article>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i>
            <span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i>
            <span>8 Months</span>
          </div>
        </article>
        """
        article = soup(html).select_one("article")
        assert SCSRChecker("/tmp")._info_field(article, "venus-mars") == "Female"
        assert SCSRChecker("/tmp")._info_field(article, "calendar-days") == "8 Months"

    def test_info_field_missing(self):
        article = soup("<article></article>").select_one("article")
        assert SCSRChecker("/tmp")._info_field(article, "venus-mars") == ""


class TestParse:
    def test_empty(self, tmp_path):
        c = SCSRChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_filters_to_female_only(self, tmp_path):
        html = """
        <article class="scsr-finder-card">
          <h3>Rex</h3>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Male</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>6 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Wales</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/rex"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_filters_to_month_based_age_only(self, tmp_path):
        html = """
        <article class="scsr-finder-card">
          <h3>Luna</h3>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>2 Years</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Wales</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/luna"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_female_puppy_included(self, tmp_path):
        html = """
        <article class="scsr-finder-card">
          <h3>Bella</h3>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>8 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Cocker Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Cardiff</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/bella"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Bella"
        assert d.gender == "Female"
        assert d.age == "8 Months"
        assert d.breed == "Cocker Spaniel"
        assert d.location == "Cardiff"

    def test_filters_reserved_status(self, tmp_path):
        """Dog with status 'Reserved' should be excluded even if female puppy."""
        html = """
        <article class="scsr-finder-card">
          <h3>Daisy</h3>
          <div class="scsr-modern-status"><i></i>Reserved</div>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>5 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Bristol</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/daisy"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_filters_for_foster_status(self, tmp_path):
        """Dog with status 'For Foster' should be excluded even if female puppy."""
        html = """
        <article class="scsr-finder-card">
          <h3>Poppy</h3>
          <div class="scsr-modern-status"><i></i>For Foster</div>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>3 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Cocker Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Wales</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/poppy"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_available_status_included(self, tmp_path):
        """Dog with status 'Available' (female puppy) should be included."""
        html = """
        <article class="scsr-finder-card">
          <h3>Molly</h3>
          <div class="scsr-modern-status"><i></i>Available</div>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>10 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Springer Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>London</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/molly"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Molly"
        assert dogs[0].status == "Available"

    def test_multiple_mixed(self, tmp_path):
        html = """
        <article class="scsr-finder-card">
          <h3>Rex</h3>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Male</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>6 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Wales</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/rex"></a>
        </article>
        <article class="scsr-finder-card">
          <h3>Luna</h3>
          <div class="scsr-modern-info-box">
            <i class="fa-venus-mars"></i><span>Female</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-calendar-days"></i><span>4 Months</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-dog"></i><span>Springer Spaniel</span>
          </div>
          <div class="scsr-modern-info-box">
            <i class="fa-location-dot"></i><span>Bristol</span>
          </div>
          <a class="scsr-modern-main-btn"
             href="https://example.org/dogs/luna"></a>
        </article>
        """
        c = SCSRChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"
