from sites.spaniel_aid import SpanielAidChecker


class TestHelpers:
    def test_parse_age_months_only(self):
        assert SpanielAidChecker._parse_age_months("15 months") == 15

    def test_parse_age_years_and_months(self):
        assert SpanielAidChecker._parse_age_months("4 years 6 months") == 54

    def test_parse_age_years_only(self):
        assert SpanielAidChecker._parse_age_months("6 years") == 72

    def test_parse_age_single_year(self):
        assert SpanielAidChecker._parse_age_months("1 year") == 12

    def test_parse_age_handles_extra_whitespace(self):
        assert SpanielAidChecker._parse_age_months("  3  years   2  months  ") == 38

    def test_parse_age_zero(self):
        assert SpanielAidChecker._parse_age_months("0 months") == 0

    def test_parse_age_invalid_returns_none(self):
        assert SpanielAidChecker._parse_age_months("unknown") is None

    def test_parse_age_empty_returns_none(self):
        assert SpanielAidChecker._parse_age_months("") is None

    def test_extract_name_and_status_simple(self):
        assert SpanielAidChecker._extract_name_and_status("Milo SA5125") == (
            "Milo SA5125", "Available"
        )

    def test_extract_name_and_status_reserved(self):
        assert SpanielAidChecker._extract_name_and_status(
            "Daisy SA5592 \u2013 Reserved while we review the current applications."
        ) == ("Daisy SA5592", "Reserved while we review the current applications.")

    def test_extract_name_and_status_foster(self):
        assert SpanielAidChecker._extract_name_and_status(
            "Chisel SA5431 \u2013 Foster View To Adopt"
        ) == ("Chisel SA5431", "Foster View To Adopt")


class TestParse:
    def test_no_cards(self, tmp_path):
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse("<html></html>") == []

    def test_single_female_puppy_included(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/luna-sa5000/">
          <div class="bricks-layout-inner">
           <div class="content-wrapper">
            <h4 class="dynamic" data-field-id="obwypa">Luna SA5000</h4>
            <div class="dynamic" data-field-id="aqprwx">
             <img class="dog-icons"/>Cocker Spaniel
            </div>
            <div class="dynamic" data-field-id="euosuj">
             <img class="dog-icons"/>8 months
            </div>
            <div class="dynamic" data-field-id="xglchg">
             <img class="dog-icons"/>Cardiff, Wales
            </div>
            <div class="dynamic" data-field-id="aalwfs">
             <img class="dog-icons"/>Female
            </div>
           </div>
          </div>
         </a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna SA5000"
        assert d.breed == "Cocker Spaniel"
        assert d.age == "8 months"
        assert d.gender == "Female"
        assert d.location == "Cardiff, Wales"
        assert d.status == "Available"
        assert d.url == "https://spanielaid.co.uk/spaniel/luna-sa5000/"

    def test_male_filtered_out(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/rex-sa5001/">
          <div class="bricks-layout-inner">
           <div class="content-wrapper">
            <h4 class="dynamic" data-field-id="obwypa">Rex SA5001</h4>
            <div class="dynamic" data-field-id="aqprwx">
             <img class="dog-icons"/>Springer Spaniel
            </div>
            <div class="dynamic" data-field-id="euosuj">
             <img class="dog-icons"/>6 months
            </div>
            <div class="dynamic" data-field-id="xglchg">
             <img class="dog-icons"/>London
            </div>
            <div class="dynamic" data-field-id="aalwfs">
             <img class="dog-icons"/>Male
            </div>
           </div>
          </div>
         </a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_female_over_12_months_filtered_out(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/bella-sa5002/">
          <div class="bricks-layout-inner">
           <div class="content-wrapper">
            <h4 class="dynamic" data-field-id="obwypa">Bella SA5002</h4>
            <div class="dynamic" data-field-id="aqprwx">
             <img class="dog-icons"/>Cocker Spaniel
            </div>
            <div class="dynamic" data-field-id="euosuj">
             <img class="dog-icons"/>2 years
            </div>
            <div class="dynamic" data-field-id="xglchg">
             <img class="dog-icons"/>Bristol
            </div>
            <div class="dynamic" data-field-id="aalwfs">
             <img class="dog-icons"/>Female
            </div>
           </div>
          </div>
         </a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_female_exactly_12_months_included(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/pup-sa5003/">
          <div class="bricks-layout-inner">
           <div class="content-wrapper">
            <h4 class="dynamic" data-field-id="obwypa">Pup SA5003</h4>
            <div class="dynamic" data-field-id="aqprwx">
             <img class="dog-icons"/>Springer Spaniel
            </div>
            <div class="dynamic" data-field-id="euosuj">
             <img class="dog-icons"/>12 months
            </div>
            <div class="dynamic" data-field-id="xglchg">
             <img class="dog-icons"/>Manchester
            </div>
            <div class="dynamic" data-field-id="aalwfs">
             <img class="dog-icons"/>Female
            </div>
           </div>
          </div>
         </a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Pup SA5003"

    def test_reserved_female_puppy_included(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/daisy-sa5592/">
          <div class="bricks-layout-inner">
           <div class="content-wrapper">
            <h4 class="dynamic" data-field-id="obwypa">
             Daisy SA5592 \u2013 Reserved while we review the current applications.
            </h4>
            <div class="dynamic" data-field-id="aqprwx">
             <img class="dog-icons"/>Cocker spaniel
            </div>
            <div class="dynamic" data-field-id="euosuj">
             <img class="dog-icons"/>5 months
            </div>
            <div class="dynamic" data-field-id="xglchg">
             <img class="dog-icons"/>Hexham, Northumberland, England
            </div>
            <div class="dynamic" data-field-id="aalwfs">
             <img class="dog-icons"/>Female
            </div>
           </div>
          </div>
         </a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Daisy SA5592"
        assert d.status == "Reserved while we review the current applications."
        assert d.gender == "Female"

    def test_missing_link_skipped(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <div class="bricks-layout-inner">
          <div class="content-wrapper">
           <h4 class="dynamic" data-field-id="obwypa">Ghost SA0000</h4>
           <div class="dynamic" data-field-id="aqprwx"><img/>Spaniel</div>
           <div class="dynamic" data-field-id="euosuj"><img/>3 months</div>
           <div class="dynamic" data-field-id="xglchg"><img/>Nowhere</div>
           <div class="dynamic" data-field-id="aalwfs"><img/>Female</div>
          </div>
         </div>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        assert c.parse(html) == []

    def test_missing_fields_default_to_empty(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/min-sa0001/">
          <div class="bricks-layout-inner">
           <div class="content-wrapper">
            <h4 class="dynamic" data-field-id="obwypa">Min SA0001</h4>
           </div>
          </div>
         </a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        # Missing gender → defaults to "", not "Female", so filtered out
        assert c.parse(html) == []

    def test_multiple_mixed_cards(self, tmp_path):
        html = """
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/male-pup/">
          <div class="bricks-layout-inner"><div class="content-wrapper">
           <h4 class="dynamic" data-field-id="obwypa">Rex</h4>
           <div class="dynamic" data-field-id="aqprwx"><img/>Spaniel</div>
           <div class="dynamic" data-field-id="euosuj"><img/>4 months</div>
           <div class="dynamic" data-field-id="xglchg"><img/>Wales</div>
           <div class="dynamic" data-field-id="aalwfs"><img/>Male</div>
          </div></div></a>
        </li>
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/female-pup/">
          <div class="bricks-layout-inner"><div class="content-wrapper">
           <h4 class="dynamic" data-field-id="obwypa">Luna</h4>
           <div class="dynamic" data-field-id="aqprwx"><img/>Springer</div>
           <div class="dynamic" data-field-id="euosuj"><img/>5 months</div>
           <div class="dynamic" data-field-id="xglchg"><img/>Bristol</div>
           <div class="dynamic" data-field-id="aalwfs"><img/>Female</div>
          </div></div></a>
        </li>
        <li class="bricks-layout-item repeater-item brxe-vsyaau">
         <a href="https://spanielaid.co.uk/spaniel/female-adult/">
          <div class="bricks-layout-inner"><div class="content-wrapper">
           <h4 class="dynamic" data-field-id="obwypa">Bella</h4>
           <div class="dynamic" data-field-id="aqprwx"><img/>Cocker</div>
           <div class="dynamic" data-field-id="euosuj"><img/>3 years</div>
           <div class="dynamic" data-field-id="xglchg"><img/>Cardiff</div>
           <div class="dynamic" data-field-id="aalwfs"><img/>Female</div>
          </div></div></a>
        </li>
        """
        c = SpanielAidChecker(str(tmp_path))
        dogs = c.parse(html)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"
