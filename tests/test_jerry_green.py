from sites.jerry_green import JerryGreenChecker


class TestParseAgeMonths:
    def test_zero_years(self):
        assert JerryGreenChecker._parse_age_months("0 years 1 months") == 1

    def test_one_year(self):
        assert JerryGreenChecker._parse_age_months("1 years 0 months") == 12

    def test_mixed(self):
        assert JerryGreenChecker._parse_age_months("2 years 3 months") == 27

    def test_just_months(self):
        assert JerryGreenChecker._parse_age_months("6 months") == 6

    def test_empty(self):
        assert JerryGreenChecker._parse_age_months("") == 0

    def test_invalid(self):
        assert JerryGreenChecker._parse_age_months("unknown") == 0


class TestParse:
    def test_no_cards(self, tmp_path):
        c = JerryGreenChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_female_puppy_small_included(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/luna/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Luna</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Cocker Spaniel</li>
                  <li class="age">0 years 6 months</li>
                  <li class="sex">Female</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list">
                <li>Children 5+</li>
                <li>Small breed</li>
                <li>Secure garden</li>
              </ul>
            </div>
            <div class="card__image">
              <div class="sticker sticker--color-5"><span>I'm Available</span></div>
              <img class="image-0" src="https://example.org/luna.jpg"/>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path), location="nottinghamshire")
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.breed == "Cocker Spaniel"
        assert d.age == "0 years 6 months"
        assert d.gender == "Female"
        assert d.location == "Nottinghamshire"
        assert d.status == "Available"
        assert d.url == "https://www.jerrygreendogs.org.uk/dogs/luna/"
        assert d.photo_url == "https://example.org/luna.jpg"

    def test_male_filtered_out(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/rex/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Rex</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Labrador</li>
                  <li class="age">0 years 3 months</li>
                  <li class="sex">Male</li>
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

    def test_over_12_months_filtered(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/bella/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Bella</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Spaniel</li>
                  <li class="age">1 years 2 months</li>
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

    def test_large_breed_filtered(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/max/">
            <div class="card__body">
              <h2 class="card__title"><span class="chevron-wrap">Max</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Greyhound</li>
                  <li class="age">0 years 8 months</li>
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

    def test_multiple_cards_mixed(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/male/">
            <div class="card__body">
              <h2 class="card__title"><span>Rex</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Lab</li>
                  <li class="age">0 years 4 months</li>
                  <li class="sex">Male</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Small breed</li></ul>
            </div>
          </a>
        </div>
        <div class="card dog" id="dog-2">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/female/">
            <div class="card__body">
              <h2 class="card__title"><span>Luna</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Spaniel</li>
                  <li class="age">0 years 5 months</li>
                  <li class="sex">Female</li>
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
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_reserved_status(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/bella/">
            <div class="card__body">
              <h2 class="card__title"><span>Bella</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Spaniel</li>
                  <li class="age">0 years 3 months</li>
                  <li class="sex">Female</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Small breed</li></ul>
            </div>
            <div class="card__image">
              <div class="sticker sticker--color-5"><span>I'm Reserved</span></div>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].status == "Reserved"

    def test_missing_optional_fields(self, tmp_path):
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/min/">
            <div class="card__body">
              <h2 class="card__title"><span>Min</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Terrier</li>
                  <li class="age">0 years 2 months</li>
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
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].photo_url == ""
        assert dogs[0].status == ""

    def test_no_size_tag_passes(self, tmp_path):
        """Dogs without explicit size tag still pass the filter."""
        html = """
        <div class="card dog" id="dog-1">
          <a class="block-link" href="https://www.jerrygreendogs.org.uk/dogs/unknown/">
            <div class="card__body">
              <h2 class="card__title"><span>Mystery</span></h2>
              <div class="card__excerpt">
                <ul class="details">
                  <li class="breed">Mixed</li>
                  <li class="age">0 years 3 months</li>
                  <li class="sex">Female</li>
                </ul>
              </div>
            </div>
            <div class="card__attributes">
              <ul class="tick-list"><li>Secure garden</li></ul>
            </div>
          </a>
        </div>
        """
        c = JerryGreenChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1


class TestFetch:
    def test_url_includes_location(self, tmp_path):
        c = JerryGreenChecker(str(tmp_path))
        url = c._build_url("north-lincolnshire")
        assert "location=north-lincolnshire" in url
        assert url.startswith("https://www.jerrygreendogs.org.uk/dogs/")
