from sites.many_tears import ManyTearsChecker


class TestTextHelper:
    def test_extracts_text(self):
        html = "<div><span class='icon breed'>Cocker Spaniel</span></div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        assert ManyTearsChecker._text(soup, ".icon.breed") == "Cocker Spaniel"

    def test_missing_selector_returns_empty(self):
        html = "<div></div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        assert ManyTearsChecker._text(soup, ".nope") == ""


class TestParse:
    def test_no_cards(self, tmp_path):
        c = ManyTearsChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_single_card(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/bella">
          <h3>Bella</h3>
          <div class="icon breed">Cocker Spaniel</div>
          <div class="icon age">6 Months</div>
          <div class="icon sex">Female</div>
          <div class="icon location">Carmarthen</div>
        </a>
        """
        c = ManyTearsChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Bella"
        assert d.breed == "Cocker Spaniel"
        assert d.age == "6 Months"
        assert d.gender == "Female"
        assert d.location == "Carmarthen"
        assert d.url == "https://www.manytearsrescue.org/dogs/bella"

    def test_card_missing_href_skipped(self, tmp_path):
        html = '<a class="animal-card"><h3>Ghost</h3></a>'
        c = ManyTearsChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_multiple_cards(self, tmp_path):
        html = """
        <a class="animal-card" href="/dogs/a"><h3>A</h3></a>
        <a class="animal-card" href="/dogs/b"><h3>B</h3></a>
        """
        c = ManyTearsChecker(str(tmp_path))
        assert len(c.parse(html)) == 2

    def test_missing_optional_fields(self, tmp_path):
        html = '<a class="animal-card" href="/dogs/min"><h3>Min</h3></a>'
        c = ManyTearsChecker(str(tmp_path))
        dogs = c.parse(html)
        assert dogs[0].breed == ""
        assert dogs[0].age == ""
