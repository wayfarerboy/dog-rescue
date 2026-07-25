from bs4 import BeautifulSoup

from sites.pro_dogs_direct import ProDogsDirectChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestHelpers:
    def test_parse_name_with_breed(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article class="post category-dogs">'
            '<header class="entry-header">'
            '<h2 class="entry-title">'
            '<a href="/dog">Luna \u2013 Cavalier King Charles Spaniel</a>'
            "</h2></header></article>"
        ).select_one("article")
        assert c._parse_name(article) == "Luna"

    def test_parse_name_applications_closed(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article class="post">'
            '<h2 class="entry-title">'
            '<a href="/dog">Fern \u2013 APPLICATIONS CLOSED</a>'
            "</h2></article>"
        ).select_one("article")
        assert c._parse_name(article) == "Fern"

    def test_parse_name_no_title(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup("<article></article>").select_one("article")
        assert c._parse_name(article) == ""

    def test_parse_age_gender_year_old(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article><div class="entry-summary">'
            "<p><b>Luna</b></p>"
            "<p><strong>6 Year Old Female </strong></p>"
            "<p><strong>CKC Spaniel</strong></p>"
            "<p><strong>Fostered in Beckenham Kent</strong></p>"
            "</div></article>"
        ).select_one("article")
        age, gender = c._parse_age_gender(article)
        assert age == "6 Year Old"
        assert gender == "Female"

    def test_parse_age_gender_week_old(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article><div class="entry-summary">'
            "<p><strong>12 Week Old Male </strong></p>"
            "</div></article>"
        ).select_one("article")
        age, gender = c._parse_age_gender(article)
        assert age == "12 Week Old"
        assert gender == "Male"

    def test_parse_age_gender_decimal_year(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article><div class="entry-summary">'
            "<p><strong>2.5 Year Old Female </strong></p>"
            "</div></article>"
        ).select_one("article")
        age, gender = c._parse_age_gender(article)
        assert age == "2.5 Year Old"
        assert gender == "Female"

    def test_parse_age_gender_missing(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup("<article></article>").select_one("article")
        age, gender = c._parse_age_gender(article)
        assert age == ""
        assert gender == ""

    def test_parse_breed(self):
        c = ProDogsDirectChecker("/tmp")
        # Need entry-title so _parse_name doesn't interfere
        article = soup(
            '<article>'
            '<h2 class="entry-title"><a href="/dog">Peanut \u2013 Pomeranian</a></h2>'
            '<div class="entry-summary">'
            "<p><strong>Peanut</strong></p>"
            "<p><strong>12 Week Old Male </strong></p>"
            "<p><strong>Pomeranian </strong></p>"
            "<p><strong>Fostered in Uckfield East Sussex</strong></p>"
            "</div></article>"
        ).select_one("article")
        assert c._parse_breed(article) == "Pomeranian"

    def test_parse_breed_missing(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup("<article></article>").select_one("article")
        assert c._parse_breed(article) == ""

    def test_parse_location(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article><div class="entry-summary">'
            "<p><strong>Fostered in Beckenham Kent</strong></p>"
            "</div></article>"
        ).select_one("article")
        assert c._parse_location(article) == "Beckenham Kent"

    def test_parse_location_double_space(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article><div class="entry-summary">'
            "<p><strong>Fostered in  Wokingham Berkshire</strong></p>"
            "</div></article>"
        ).select_one("article")
        assert c._parse_location(article) == "Wokingham Berkshire"

    def test_parse_location_missing(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup("<article></article>").select_one("article")
        assert c._parse_location(article) == ""

    def test_parse_status_applications_closed_category(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article class="post category-applications-closed">'
            '<h2 class="entry-title"><a href="/dog">Fern \u2013 CKC Spaniel</a></h2>'
            "</article>"
        ).select_one("article")
        assert c._parse_status(article) == "Applications Closed"

    def test_parse_status_applications_closed_title(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article class="post category-dogs">'
            '<h2 class="entry-title"><a href="/dog">Fern \u2013 APPLICATIONS CLOSED</a></h2>'
            "</article>"
        ).select_one("article")
        assert c._parse_status(article) == "Applications Closed"

    def test_parse_status_reserved(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article class="post category-dogs">'
            '<h2 class="entry-title"><a href="/dog">Max \u2013 RESERVED</a></h2>'
            "</article>"
        ).select_one("article")
        assert c._parse_status(article) == "Reserved"

    def test_parse_status_available(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article class="post category-dogs">'
            '<h2 class="entry-title"><a href="/dog">Luna \u2013 CKC Spaniel</a></h2>'
            "</article>"
        ).select_one("article")
        assert c._parse_status(article) == ""

    def test_profile_url(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup(
            '<article>'
            '<h2 class="entry-title"><a href="https://prodogsdirect.org.uk/luna/">Luna</a></h2>'
            "</article>"
        ).select_one("article")
        assert c._profile_url(article) == "https://prodogsdirect.org.uk/luna/"

    def test_profile_url_missing(self):
        c = ProDogsDirectChecker("/tmp")
        article = soup("<article></article>").select_one("article")
        assert c._profile_url(article) == ""

    def test_photo_url(self):
        article = soup(
            '<article><div class="entry-thumb">'
            '<img src="https://prodogsdirect.org.uk/wp-content/uploads/2026/07/Luna7-520x650.jpg"/>'
            "</div></article>"
        ).select_one("article")
        assert (
            ProDogsDirectChecker._photo_url(article)
            == "https://prodogsdirect.org.uk/wp-content/uploads/2026/07/Luna7-520x650.jpg"
        )

    def test_photo_url_missing(self):
        article = soup("<article></article>").select_one("article")
        assert ProDogsDirectChecker._photo_url(article) == ""


class TestParse:
    def test_no_articles(self, tmp_path):
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_skips_not_ready_for_adoption(self, tmp_path):
        html = """
        <article class="post category-not-ready-for-adoption sticky">
          <h2 class="entry-title"><a href="/before-you-start">Before you start</a></h2>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_single_dog(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <header class="entry-header">
            <h2 class="entry-title">
              <a href="https://prodogsdirect.org.uk/luna-cavalier-king-charles-spaniel/">
                Luna \u2013 Cavalier King Charles Spaniel
              </a>
            </h2>
          </header>
          <div class="entry-thumb">
            <a href="/luna/">
              <img src="https://prodogsdirect.org.uk/wp-content/uploads/2026/07/Luna7-520x650.jpg"
                />
            </a>
          </div>
          <div class="entry-summary">
            <p><b>Luna</b></p>
            <p><strong>6 Year Old Female </strong></p>
            <p><strong>CKC Spaniel</strong></p>
            <p><strong>Fostered in Beckenham Kent</strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.age == "6 Year Old"
        assert d.gender == "Female"
        assert d.breed == "CKC Spaniel"
        assert d.location == "Beckenham Kent"
        assert d.status == ""
        assert d.url == "https://prodogsdirect.org.uk/luna-cavalier-king-charles-spaniel/"
        assert (
            d.photo_url
            == "https://prodogsdirect.org.uk/wp-content/uploads/2026/07/Luna7-520x650.jpg"
        )

    def test_applications_closed_dog_filtered(self, tmp_path):
        html = """
        <article class="post category-applications-closed">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/fern-ckc-spaniel/">
              Fern \u2013 APPLICATIONS CLOSED
            </a>
          </h2>
          <div class="entry-summary">
            <p><b>Fern</b></p>
            <p><strong>2.5 Year Old Female </strong></p>
            <p><strong>CKC Spaniel</strong></p>
            <p><strong>Fostered in Camberley Surrey</strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 0

    def test_reserved_dog_filtered(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/max-lab/">
              Max \u2013 RESERVED
            </a>
          </h2>
          <div class="entry-summary">
            <p><b>Max</b></p>
            <p><strong>3 Year Old Male </strong></p>
            <p><strong>Labrador</strong></p>
            <p><strong>Fostered in London</strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 0

    def test_only_available_dogs_returned(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/luna/">Luna \u2013 CKC Spaniel</a>
          </h2>
          <div class="entry-summary">
            <p><b>Luna</b></p>
            <p><strong>6 Year Old Female </strong></p>
            <p><strong>CKC Spaniel</strong></p>
            <p><strong>Fostered in Beckenham Kent</strong></p>
          </div>
        </article>
        <article class="post category-applications-closed">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/fern/">Fern \u2013 APPLICATIONS CLOSED</a>
          </h2>
          <div class="entry-summary">
            <p><b>Fern</b></p>
            <p><strong>2.5 Year Old Female </strong></p>
            <p><strong>CKC Spaniel</strong></p>
            <p><strong>Fostered in Camberley Surrey</strong></p>
          </div>
        </article>
        <article class="post category-dogs">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/max/">Max \u2013 RESERVED</a>
          </h2>
          <div class="entry-summary">
            <p><b>Max</b></p>
            <p><strong>3 Year Old Male </strong></p>
            <p><strong>Labrador</strong></p>
            <p><strong>Fostered in London</strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_puppy_male(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/peanut-pomeranian/">
              Peanut \u2013 Pomeranian
            </a>
          </h2>
          <div class="entry-summary">
            <p><strong>Peanut</strong></p>
            <p><strong>12 Week Old Male </strong></p>
            <p><strong>Pomeranian </strong></p>
            <p><strong>Fostered in Uckfield East Sussex</strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Peanut"
        assert d.age == "12 Week Old"
        assert d.gender == "Male"
        assert d.breed == "Pomeranian"
        assert d.location == "Uckfield East Sussex"

    def test_multiple_dogs(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/luna/">Luna \u2013 CKC Spaniel</a>
          </h2>
          <div class="entry-summary">
            <p><b>Luna</b></p>
            <p><strong>6 Year Old Female </strong></p>
            <p><strong>CKC Spaniel</strong></p>
            <p><strong>Fostered in Beckenham Kent</strong></p>
          </div>
        </article>
        <article class="post category-dogs">
          <h2 class="entry-title">
            <a href="https://prodogsdirect.org.uk/lexi/">Lexi \u2013 CKC Spaniel</a>
          </h2>
          <div class="entry-summary">
            <p><strong>Lexi</strong></p>
            <p><strong>4 Year Old Female </strong></p>
            <p><strong>CKC Spaniel</strong></p>
            <p><strong>Fostered in Bracknell Berks</strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 2
        assert dogs[0].name == "Luna"
        assert dogs[1].name == "Lexi"

    def test_missing_name_skipped(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <div class="entry-summary">
            <p><strong>6 Year Old Female </strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_missing_url_skipped(self, tmp_path):
        html = """
        <article class="post category-dogs">
          <h2 class="entry-title">Luna</h2>
          <div class="entry-summary">
            <p><b>Luna</b></p>
            <p><strong>6 Year Old Female </strong></p>
          </div>
        </article>
        """
        c = ProDogsDirectChecker(str(tmp_path))
        assert c.parse(html) == []
