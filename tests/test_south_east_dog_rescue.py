"""Tests for South East Dog Rescue scraper."""

from sites.south_east_dog_rescue import SouthEastDogRescueChecker


class TestAgeMonths:
    def test_years_old(self):
        assert SouthEastDogRescueChecker._age_months("2 years old") == 24

    def test_single_year(self):
        assert SouthEastDogRescueChecker._age_months("1 year old") == 12

    def test_months_old(self):
        assert SouthEastDogRescueChecker._age_months("6 months old") == 6

    def test_single_month(self):
        assert SouthEastDogRescueChecker._age_months("1 month old") == 1

    def test_empty_returns_999(self):
        assert SouthEastDogRescueChecker._age_months("") == 999

    def test_unparseable_returns_999(self):
        assert SouthEastDogRescueChecker._age_months("unknown") == 999


class TestParse:
    def test_no_cards(self, tmp_path):
        c = SouthEastDogRescueChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_female_puppy_included(self, tmp_path):
        """Female dog under 12 months should be included."""
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/luna-adopt/">
              <div data-gatsby-image-wrapper="" class="gatsby-image-wrapper">
                <img data-main-image=""
                     data-src="https://images.example.org/luna.jpg"/>
              </div>
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Luna</div>
                <ul class="mt-auto">
                  <li>6 months old</li>
                  <li>Female</li>
                  <li>Spaniel</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.age == "6 months old"
        assert d.gender == "Female"
        assert d.breed == "Spaniel"
        assert d.url == "https://www.sedogrescue.co.uk/dogs/luna-adopt/"
        assert d.photo_url == "https://images.example.org/luna.jpg"

    def test_male_filtered_out(self, tmp_path):
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/rex-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Rex</div>
                <ul class="mt-auto">
                  <li>4 months old</li>
                  <li>Male</li>
                  <li>Labrador</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_over_12_months_filtered(self, tmp_path):
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/daisy-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Daisy</div>
                <ul class="mt-auto">
                  <li>2 years old</li>
                  <li>Female</li>
                  <li>Terrier</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_multiple_cards_mixed(self, tmp_path):
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/rex-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Rex</div>
                <ul class="mt-auto">
                  <li>4 months old</li>
                  <li>Male</li>
                  <li>Labrador</li>
                </ul>
              </div>
            </a>
          </li>
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/luna-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Luna</div>
                <ul class="mt-auto">
                  <li>6 months old</li>
                  <li>Female</li>
                  <li>Spaniel</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_age_with_gatsby_comments(self, tmp_path):
        """Age field may contain Gatsby <!-- --> comment placeholders."""
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/bella-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Bella</div>
                <ul class="mt-auto">
                  <li>1 year<!-- --> old</li>
                  <li>Female</li>
                  <li>Cocker Spaniel</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].age == "1 year old"

    def test_missing_optional_fields(self, tmp_path):
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/min-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Min</div>
                <ul class="mt-auto">
                  <li>3 months old</li>
                  <li>Female</li>
                  <li>Terrier</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].photo_url == ""

    def test_12_months_exactly_included(self, tmp_path):
        """Exactly 12 months (1 year) should be included."""
        html = """
        <ul class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
          <li class="relative flex flex-1 transform flex-col rounded-lg
                     border border-gray-100 bg-white shadow-lg
                     transition duration-300 ease-in-out
                     hover:scale-110 hover:shadow">
            <a class="link" href="/dogs/bella-adopt/">
              <div class="prose mt-auto flex flex-1 flex-col p-4">
                <div class="text-grey-800 my-2 border-b-2 border-dotted
                            border-brand-pink pb-2 text-xl font-black">Bella</div>
                <ul class="mt-auto">
                  <li>12 months old</li>
                  <li>Female</li>
                  <li>Pug</li>
                </ul>
              </div>
            </a>
          </li>
        </ul>
        """
        c = SouthEastDogRescueChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Bella"
