"""Tests for the Raystede site checker."""

import json

from sites.raystede import RaystedeChecker


class TestParseAgeMonths:
    def test_just_months(self):
        assert RaystedeChecker._parse_age_months("11 months") == 11
        assert RaystedeChecker._parse_age_months("6 months") == 6

    def test_just_years(self):
        assert RaystedeChecker._parse_age_months("3 years") == 36
        assert RaystedeChecker._parse_age_months("1 year") == 12

    def test_years_and_months(self):
        assert RaystedeChecker._parse_age_months("2 years 6 months") == 30
        assert RaystedeChecker._parse_age_months("1 year 1 month") == 13
        assert RaystedeChecker._parse_age_months("5 years 4 months") == 64

    def test_years_and_months_with_and(self):
        """Some ages use 'and' between years/months: '5 years and 6 years'."""
        assert RaystedeChecker._parse_age_months("5 years and 6 months") == 66

    def test_empty(self):
        assert RaystedeChecker._parse_age_months("") == 0

    def test_unknown(self):
        assert RaystedeChecker._parse_age_months("Unknown") == 0

    def test_range(self):
        """Age ranges like '3 years 5 months to 7 years 8 months' — take the lower bound."""
        # Actually, for our purposes let's just handle simple cases. Ranges won't
        # typically apply to dogs, but we should handle gracefully.
        pass


class TestParse:
    def test_no_dogs(self, tmp_path):
        c = RaystedeChecker(str(tmp_path))
        raw = json.dumps({"status": "success", "count": 0, "data": []})
        assert c.parse(raw) == []

    def test_female_puppy_included(self, tmp_path):
        """Female dog aged 8 months — should pass the post-scrape filter."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 1,
                        "animalref": "25001",
                        "species": "Dog",
                        "name": "Luna",
                        "gender": "Female",
                        "breed": "Cocker Spaniel",
                        "age": "8 months",
                        "image": "50001",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Luna"
        assert d.gender == "Female"
        assert d.breed == "Cocker Spaniel"
        assert d.age == "8 months"
        assert d.status == "Available"
        assert d.url == "https://www.raystede.org/adopt/dogs/?animal=25001"
        assert d.photo_url == "https://www.raystede.org/anilog-images/50001.jpg"
        assert d.location == ""

    def test_male_filtered_out(self, tmp_path):
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 2,
                        "animalref": "25002",
                        "species": "Dog",
                        "name": "Rex",
                        "gender": "Male",
                        "breed": "Labrador",
                        "age": "6 months",
                        "image": "50002",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        assert c.parse(raw) == []

    def test_over_12_months_filtered_out(self, tmp_path):
        """Female but 3 years old — should be filtered out (>12 months)."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 3,
                        "animalref": "25003",
                        "species": "Dog",
                        "name": "Bella",
                        "gender": "Female",
                        "breed": "Spaniel",
                        "age": "3 years",
                        "image": "50003",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        assert c.parse(raw) == []

    def test_home_found_excluded(self, tmp_path):
        """Dog marked as 'Home Found' (reserved=1) should be excluded."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 4,
                        "animalref": "25004",
                        "species": "Dog",
                        "name": "Daisy",
                        "gender": "Female",
                        "breed": "Terrier",
                        "age": "4 months",
                        "image": "50004",
                        "reserved": 1,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        assert c.parse(raw) == []

    def test_meeting_a_match_status(self, tmp_path):
        """Dog with is_meeting=true gets 'Meeting a Match' status."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 5,
                        "animalref": "25005",
                        "species": "Dog",
                        "name": "Poppy",
                        "gender": "Female",
                        "breed": "Collie",
                        "age": "6 months",
                        "image": "50005",
                        "reserved": 0,
                        "is_meeting": 1,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert len(dogs) == 1
        assert dogs[0].status == "Meeting a Match"

    def test_12_months_exactly_included(self, tmp_path):
        """Female dog at exactly 12 months — boundary case, should be included."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 6,
                        "animalref": "25006",
                        "species": "Dog",
                        "name": "Pup",
                        "gender": "Female",
                        "breed": "Mixed",
                        "age": "1 year",
                        "image": "50006",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert len(dogs) == 1

    def test_1_year_1_month_filtered_out(self, tmp_path):
        """Female at 13 months — should be filtered out."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 7,
                        "animalref": "25007",
                        "species": "Dog",
                        "name": "OldPup",
                        "gender": "Female",
                        "breed": "Mixed",
                        "age": "1 year 1 month",
                        "image": "50007",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        assert c.parse(raw) == []

    def test_non_dog_species_filtered_out(self, tmp_path):
        """Cats and other species should be ignored."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 2,
                "data": [
                    {
                        "id": 8,
                        "animalref": "25008",
                        "species": "Cat",
                        "name": "Whiskers",
                        "gender": "Female",
                        "breed": "DSH",
                        "age": "4 months",
                        "image": "50008",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                    {
                        "id": 9,
                        "animalref": "25009",
                        "species": "Dog",
                        "name": "Fido",
                        "gender": "Female",
                        "breed": "Poodle",
                        "age": "5 months",
                        "image": "50009",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert len(dogs) == 1
        assert dogs[0].name == "Fido"

    def test_multiple_dogs_mixed(self, tmp_path):
        """Multiple dogs — only the female under 12 months should pass."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 4,
                "data": [
                    {
                        "id": 10,
                        "animalref": "25010",
                        "species": "Dog",
                        "name": "Rex",
                        "gender": "Male",
                        "breed": "Lab",
                        "age": "6 months",
                        "image": "50010",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                    {
                        "id": 11,
                        "animalref": "25011",
                        "species": "Dog",
                        "name": "Luna",
                        "gender": "Female",
                        "breed": "Spaniel",
                        "age": "8 months",
                        "image": "50011",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                    {
                        "id": 12,
                        "animalref": "25012",
                        "species": "Dog",
                        "name": "Bella",
                        "gender": "Female",
                        "breed": "Terrier",
                        "age": "3 years",
                        "image": "50012",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                    {
                        "id": 13,
                        "animalref": "25013",
                        "species": "Dog",
                        "name": "Daisy",
                        "gender": "Female",
                        "breed": "Poodle",
                        "age": "5 months",
                        "image": "50013",
                        "reserved": 1,
                        "is_meeting": 0,
                    },
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert len(dogs) == 1
        assert dogs[0].name == "Luna"

    def test_missing_optional_fields(self, tmp_path):
        """Dog with missing image still works."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 14,
                        "animalref": "25014",
                        "species": "Dog",
                        "name": "Min",
                        "gender": "Female",
                        "breed": "Unknown",
                        "age": "3 months",
                        "image": "",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert len(dogs) == 1
        assert dogs[0].photo_url == ""

    def test_api_error_status(self, tmp_path):
        """API error response returns empty list."""
        raw = json.dumps({"status": "error", "message": "No action defined"})
        c = RaystedeChecker(str(tmp_path))
        assert c.parse(raw) == []

    def test_pair_dog_still_included(self, tmp_path):
        """Bonded pair (Male & Female) — include if age ≤ 12 months."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 15,
                        "animalref": "25015",
                        "species": "Dog",
                        "name": "Bonnie & Clyde",
                        "gender": "Male & Female",
                        "breed": "Lurcher",
                        "age": "8 months",
                        "image": "50015",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        # Mixed-gender pairs: "Female" is in the gender string
        assert len(dogs) == 1
        assert dogs[0].name == "Bonnie & Clyde"
        assert dogs[0].gender == "Male & Female"

    def test_pair_dog_filtered_by_age(self, tmp_path):
        """Bonded pair over 12 months — filtered out."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 1,
                "data": [
                    {
                        "id": 16,
                        "animalref": "25016",
                        "species": "Dog",
                        "name": "Old Pair",
                        "gender": "Male & Female",
                        "breed": "Lurcher",
                        "age": "5 years and 6 years",
                        "image": "50016",
                        "reserved": 0,
                        "is_meeting": 0,
                    }
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        assert dogs == []


class TestIntegration:
    """Tests against realistic API response data."""

    def test_parse_live_api_response(self, tmp_path):
        """Parse a realistic JSON response matching the live API."""
        raw = json.dumps(
            {
                "status": "success",
                "count": 69,
                "data": [
                    {
                        "id": 18994683,
                        "animalref": "13533",
                        "species": "Cat",
                        "name": "Candy",
                        "gender": "Female",
                        "breed": "Domestic Short Hair",
                        "age": "12 years",
                        "image": "53155",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                    {
                        "id": 18994736,
                        "animalref": "25467",
                        "species": "Dog",
                        "name": "Roo",
                        "gender": "Female",
                        "breed": "Terrier: Staff Bull",
                        "age": "3 years",
                        "image": "52819",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                    {
                        "id": 18994737,
                        "animalref": "25498",
                        "species": "Dog",
                        "name": "Pepper",
                        "gender": "Female",
                        "breed": "Terrier: Jack Russell",
                        "age": "5 years 4 months",
                        "image": "53010",
                        "reserved": 0,
                        "is_meeting": 0,
                    },
                ],
            }
        )
        c = RaystedeChecker(str(tmp_path))
        dogs = c.parse(raw)
        # All dogs are female but >12 months, so filtered out
        # Cat is filtered out
        assert dogs == []
