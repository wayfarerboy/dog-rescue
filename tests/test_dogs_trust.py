from datetime import date

from sites.dogs_trust import DogsTrustChecker


class TestComputeAge:
    def test_under_one_year(self):
        today = date.today()
        dob = date(today.year, today.month - 5, 1).isoformat()
        assert DogsTrustChecker._compute_age(dob) == "5 Months"

    def test_exactly_one_year(self):
        today = date.today()
        dob = date(today.year - 1, today.month, today.day).isoformat()
        assert DogsTrustChecker._compute_age(dob) == "1 Year Old"

    def test_over_one_year(self):
        today = date.today()
        dob = date(today.year - 2, today.month, today.day).isoformat()
        assert DogsTrustChecker._compute_age(dob) == "2 Years Old"

    def test_empty_string(self):
        assert DogsTrustChecker._compute_age("") == ""

    def test_invalid_date(self):
        assert DogsTrustChecker._compute_age("not-a-date") == "not-a-date"

    def test_zero_months(self):
        today = date.today()
        dob = today.isoformat()
        assert DogsTrustChecker._compute_age(dob) == "0 Months"


class TestParse:
    def test_parse_empty_json(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        assert c.parse("[]") == []

    def test_parse_invalid_json(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        assert c.parse("not json") == []

    def test_parse_single_dog(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        raw = (
            '[{"name":"Bella","dob":"2023-06-15","gender":"F",'
            '"breed":"Labrador","frontEndBreedName":"Labrador Retriever",'
            '"centreName":"Cardiff","status":"Available","url":"/dogs/bella"}]'
        )
        dogs = c.parse(raw)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Bella"
        assert d.gender == "Female"
        assert d.breed == "Labrador Retriever"
        assert d.location == "Cardiff"
        assert d.status == "Available"
        assert d.url == "https://www.dogstrust.org.uk/dogs/bella"

    def test_parse_falls_back_to_breed_field(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        raw = (
            '[{"name":"Rex","dob":"2023-01-01","gender":"M",'
            '"breed":"Mixed","centreName":"London","status":"For Foster",'
            '"url":"/dogs/rex"}]'
        )
        dogs = c.parse(raw)
        assert dogs[0].breed == "Mixed"
        assert dogs[0].gender == "M"  # not "Female" since gender != "F"

    def test_parse_missing_fields(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        dogs = c.parse('[{}]')
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == ""
        assert d.age == ""
        assert d.breed == ""

    def test_parse_multiple_dogs(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        raw = (
            '[{"name":"A","url":"/a"},{"name":"B","url":"/b"},'
            '{"name":"C","url":"/c"}]'
        )
        assert len(c.parse(raw)) == 3
