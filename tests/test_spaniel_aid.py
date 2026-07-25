"""Tests for the Spaniel Aid site checker."""

from bs4 import BeautifulSoup

from sites.spaniel_aid import SpanielAidChecker


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestHelpers:
    def test_text(self):
        html = "<div><h4>Bella</h4></div>"
        assert SpanielAidChecker._text(soup(html), "h4") == "Bella"

    def test_text_missing(self):
        assert SpanielAidChecker._text(soup("<div></div>"), "h4") == ""

    def test_parse_age_months_only(self):
        assert SpanielAidChecker._parse_age_months("15 months") == 15
        assert SpanielAidChecker._parse_age_months("9 months") == 9

    def test_parse_age_years_only(self):
        assert SpanielAidChecker._parse_age_months("4 years") == 48
        assert SpanielAidChecker._parse_age_months("1 year") == 12

    def test_parse_age_years_and_months(self):
        assert SpanielAidChecker._parse_age_months("4 years 6 months") == 54
        assert SpanielAidChecker._parse_age_months("2 years 4 months") == 28
        assert SpanielAidChecker._parse_age_months("4 years 1 month") == 49
        assert SpanielAidChecker._parse_age_months("6 years 9 months") == 81

    def test_parse_age_empty(self):
        assert SpanielAidChecker._parse_age_months("") == 0
        assert SpanielAidChecker._parse_age_months("Unknown") == 0

    def test_clean_name_plain(self):
        assert SpanielAidChecker._clean_name("Milo SA5125") == "Milo"

    def test_clean_name_with_reserved_status(self):
        assert (
            SpanielAidChecker._clean_name(
                "Daisy SA5592 \u2013 Reserved while we review the current applications."
            )
            == "Daisy"
        )

    def test_clean_name_with_foster_status(self):
        assert (
            SpanielAidChecker._clean_name("Chisel SA5431 \u2013 Foster View To Adopt")
            == "Chisel"
        )

    def test_clean_name_no_sa_ref(self):
        assert SpanielAidChecker._clean_name("Buddy") == "Buddy"

    def test_extract_status_available(self):
        assert SpanielAidChecker._extract_status("Milo SA5125") == "Available"

    def test_extract_status_reserved(self):
        assert (
            SpanielAidChecker._extract_status(
                "Daisy SA5592 \u2013 Reserved while we review the current applications."
            )
            == "Reserved while we review"
        )

    def test_extract_status_foster(self):
        assert (
            SpanielAidChecker._extract_status("Chisel SA5431 \u2013 Foster View To Adopt")
            == "Foster View To Adopt"
        )

    def test_extract_photo_url(self):
        html = """
        <div>
          <figure class="image-wrapper">
            <img src="https://spanielaid.co.uk/wp-content/uploads/2026/06/photo.jpg" />
          </figure>
        </div>
        """
        card = soup(html)
        assert (
            SpanielAidChecker._photo_url(card)
            == "https://spanielaid.co.uk/wp-content/uploads/2026/06/photo.jpg"
        )

    def test_extract_photo_url_missing(self):
        html = "<div></div>"
        card = soup(html)
        assert SpanielAidChecker._photo_url(card) == ""


class TestParse:
    def test_no_cards(self, tmp_path):
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_female_puppy_included(self, tmp_path):
        """Female dog aged 11 months — should pass the post-scrape filter."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/luna-sa5555/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Luna SA5555</h4>
                    <div class="dynamic">Cocker spaniel</div>
                    <div class="dynamic">11 months</div>
                    <div class="dynamic">Hexham, Northumberland, England</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 8+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.breed == "Cocker spaniel"
        assert d.age == "11 months"
        assert d.gender == "Female"
        assert d.location == "Hexham, Northumberland, England"
        assert d.status == "Available"
        assert d.url == "https://spanielaid.co.uk/spaniel/luna-sa5555/"
        assert d.photo_url == "https://spanielaid.co.uk/wp-content/photo.jpg"

    def test_male_filtered_out(self, tmp_path):
        """Male dog — should be filtered out."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/ralphie-sa5596/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Ralphie SA5596</h4>
                    <div class="dynamic">Cocker spaniel cross</div>
                    <div class="dynamic">9 months</div>
                    <div class="dynamic">Darlington, County Durham</div>
                    <div class="dynamic">Male</div>
                    <div class="dynamic">Yes 12+</div>
                    <div class="dynamic">Yes</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_over_12_months_filtered_out(self, tmp_path):
        """Female but 15 months old — should be filtered out (>12 months)."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/bella-sa5380/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Bella SA5380</h4>
                    <div class="dynamic">Springer spaniel</div>
                    <div class="dynamic">15 months</div>
                    <div class="dynamic">Mold, CH7, North Wales</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 8+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_female_with_years_filtered_out(self, tmp_path):
        """Female but 4 years old — should be filtered out (>12 months)."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/daisy-sa5592/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Daisy SA5592</h4>
                    <div class="dynamic">Cocker spaniel</div>
                    <div class="dynamic">4 years</div>
                    <div class="dynamic">Hexham, Northumberland</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 8+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_reserved_status_filtered_out(self, tmp_path):
        """Female puppy with reserved status should be filtered out."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/daisy-sa5592/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Daisy SA5592 \u2013 Reserved while we review</h4>
                    <div class="dynamic">Cocker spaniel</div>
                    <div class="dynamic">6 months</div>
                    <div class="dynamic">Hexham, Northumberland</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 8+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs == []

    def test_foster_view_to_adopt_filtered_out(self, tmp_path):
        """Female puppy with Foster View To Adopt status should be filtered out."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/chisel-sa5431/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Chisel SA5431 \u2013 Foster View To Adopt</h4>
                    <div class="dynamic">Working cocker spaniel</div>
                    <div class="dynamic">8 months</div>
                    <div class="dynamic">Bristol</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 12+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs == []

    def test_card_missing_link_skipped(self, tmp_path):
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <div class="bricks-layout-inner">
                <div class="content-wrapper">
                  <h4 class="dynamic">Ghost SA0000</h4>
                  <div class="dynamic">Spaniel</div>
                  <div class="dynamic">3 months</div>
                  <div class="dynamic">Nowhere</div>
                  <div class="dynamic">Female</div>
                </div>
              </div>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_12_months_exactly_included(self, tmp_path):
        """Female dog at exactly 12 months — boundary case, should be included."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/pup-sa5555/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Pup SA5555</h4>
                    <div class="dynamic">Spaniel cross</div>
                    <div class="dynamic">12 months</div>
                    <div class="dynamic">Cardiff, Wales</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 12+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1

    def test_multiple_cards_mixed(self, tmp_path):
        """Multiple cards — only the female under 12 months should pass."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/milo-sa5125/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/milo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Milo SA5125</h4>
                    <div class="dynamic">Springer spaniel cross</div>
                    <div class="dynamic">15 months</div>
                    <div class="dynamic">Derbyshire</div>
                    <div class="dynamic">Male</div>
                    <div class="dynamic">Yes 16+</div>
                    <div class="dynamic">Yes</div>
                  </div>
                </div>
              </a>
            </li>
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/luna-sa5555/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/luna.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Luna SA5555</h4>
                    <div class="dynamic">Cocker spaniel</div>
                    <div class="dynamic">8 months</div>
                    <div class="dynamic">Hexham, Northumberland</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 8+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/poppadom-sa5588/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/poppadom.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Poppadom SA5588</h4>
                    <div class="dynamic">Sprollie</div>
                    <div class="dynamic">2 years 4 months</div>
                    <div class="dynamic">Caerphilly, Wales</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 12+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_1_year_old_filtered_out(self, tmp_path):
        """Female at exactly 1 year (12 months) — boundary case, should be included."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/lass-sa5555/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/photo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Lass SA5555</h4>
                    <div class="dynamic">Spaniel</div>
                    <div class="dynamic">1 year</div>
                    <div class="dynamic">London</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 12+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1


class TestIntegration:
    """Tests against a saved copy of the live site HTML."""

    def test_parse_live_html(self, tmp_path):
        """Parse a realistic HTML snippet matching the live site structure."""
        html = """
        <div class="brxe-posts dog-card-style">
          <ul class="bricks-layout-wrapper">
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/milo-sa5125/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/milo.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Milo SA5125</h4>
                    <div class="dynamic">Springer spaniel cross (unknown)</div>
                    <div class="dynamic">15 months</div>
                    <div class="dynamic">Dronfield Woodhouse, Derbyshire, England</div>
                    <div class="dynamic">Male</div>
                    <div class="dynamic">Yes 16+</div>
                    <div class="dynamic">Yes</div>
                  </div>
                </div>
              </a>
            </li>
            <li class="bricks-layout-item repeater-item">
              <a href="https://spanielaid.co.uk/spaniel/daisy-sa5592/">
                <div class="bricks-layout-inner">
                  <figure class="image-wrapper">
                    <img src="https://spanielaid.co.uk/wp-content/daisy.jpg" />
                  </figure>
                  <div class="content-wrapper">
                    <h4 class="dynamic">Daisy SA5592 \u2013 Reserved while we review</h4>
                    <div class="dynamic">Cocker spaniel</div>
                    <div class="dynamic">4 years</div>
                    <div class="dynamic">Hexham, Northumberland, England</div>
                    <div class="dynamic">Female</div>
                    <div class="dynamic">Yes 8+</div>
                    <div class="dynamic">No</div>
                  </div>
                </div>
              </a>
            </li>
          </ul>
        </div>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        # Daisy is Female but 4 years > 12 months, so filtered out
        # Milo is Male, so filtered out
        assert dogs == []
