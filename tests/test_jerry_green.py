from sites.jerry_green import JerryGreenChecker


class TestParseAgeMonths:
    def test_zero_years_one_month(self):
        assert JerryGreenChecker._parse_age_months("0 years 1 months") == 1

    def test_one_year(self):
        assert JerryGreenChecker._parse_age_months("1 year 0 months") == 12

    def test_seven_years(self):
        assert JerryGreenChecker._parse_age_months("7 years 11 months") == 95

    def test_empty_string(self):
        assert JerryGreenChecker._parse_age_months("") is None

    def test_unparseable(self):
        assert JerryGreenChecker._parse_age_months("Unknown") is None


class TestExtractSize:
    def test_small(self, tmp_path):
        html = '<div class="card__attributes"><ul class="tick-list"><li>Small breed</li></ul></div>'
        from bs4 import BeautifulSoup
        card = BeautifulSoup(html, "html.parser")
        assert JerryGreenChecker._extract_size(card) == "Small"

    def test_medium(self, tmp_path):
        html = (
            '<div class="card__attributes">'
            '<ul class="tick-list"><li>Medium breed</li></ul></div>'
        )
        from bs4 import BeautifulSoup
        card = BeautifulSoup(html, "html.parser")
        assert JerryGreenChecker._extract_size(card) == "Medium"

    def test_large(self, tmp_path):
        html = '<div class="card__attributes"><ul class="tick-list"><li>Large breed</li></ul></div>'
        from bs4 import BeautifulSoup
        card = BeautifulSoup(html, "html.parser")
        assert JerryGreenChecker._extract_size(card) == "Large"

    def test_no_size(self, tmp_path):
        html = (
            '<div class="card__attributes">'
            '<ul class="tick-list"><li>Housetrained</li></ul></div>'
        )
        from bs4 import BeautifulSoup
        card = BeautifulSoup(html, "html.parser")
        assert JerryGreenChecker._extract_size(card) == ""

    def test_no_tick_list(self, tmp_path):
        html = "<div></div>"
        from bs4 import BeautifulSoup
        card = BeautifulSoup(html, "html.parser")
        assert JerryGreenChecker._extract_size(card) == ""


class TestParse:
    def test_no_cards(self, tmp_path):
        c = JerryGreenChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_single_card_passes_filter(self, tmp_path):
        html = """
        <div class="card dog">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/luna/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Luna</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Weimaraner Cross</li>
                  <li class="age">0 years 8 months</li>
                  <li class="sex">Female</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list">
                <li>Medium breed</li>
                <li>Housetrained</li>
              </ul>
            </div>
            <div class="card__image">
              <div class="sticker"><span>I'm Available</span></div>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.breed == "Weimaraner Cross"
        assert d.age == "0 years 8 months"
        assert d.gender == "Female"
        assert d.url == "https://www.jerrygreendogs.org.uk/dogs/luna/"
        assert d.status == "I'm Available"

    def test_male_filtered_out(self, tmp_path):
        html = """
        <div class="card dog">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/max/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Max</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Labrador</li>
                  <li class="age">0 years 6 months</li>
                  <li class="sex">Male</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Medium breed</li></ul>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_too_old_filtered_out(self, tmp_path):
        html = """
        <div class="card dog">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/oldie/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Oldie</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Poodle</li>
                  <li class="age">2 years 0 months</li>
                  <li class="sex">Female</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Small breed</li></ul>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_large_breed_filtered_out(self, tmp_path):
        html = """
        <div class="card dog">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/big/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Big</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Great Dane</li>
                  <li class="age">0 years 3 months</li>
                  <li class="sex">Female</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Large breed</li></ul>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_card_missing_link_skipped(self, tmp_path):
        html = (
            '<div class="card dog">'
            '<h2 class="card__title"><span class="chevron-wrap">Ghost</span></h2>'
            '</div>'
        )
        c = JerryGreenChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_missing_optional_fields(self, tmp_path):
        html = """
        <div class="card dog">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/min/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Min</span></h2>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Small breed</li></ul>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        dogs = c.parse(html)
        # No gender field → not Female → filtered out
        assert dogs == []
