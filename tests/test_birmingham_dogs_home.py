"""Tests for Birmingham Dogs Home site checker."""

import json

from sites.birmingham_dogs_home import BirminghamDogsHomeChecker


def _dog_json(
    *,
    name: str,
    breed: str,
    sex: str,
    age: str,
    centre: str,
    status: str,
    link: str,
    photo_url: str = "",
) -> dict:
    """Build a minimal WP REST API dog entry for testing."""
    entry: dict = {
        "link": link,
        "meta": {
            "name": name,
            "breed": breed,
            "sex": sex,
            "age-in-years-and-months": age,
            "centre": centre,
            "status": status,
        },
    }
    if photo_url:
        entry["_embedded"] = {
            "wp:featuredmedia": [{"source_url": photo_url}],
        }
    return entry


class TestParse:
    def test_empty_response(self, tmp_path):
        c = BirminghamDogsHomeChecker(str(tmp_path))
        assert c.parse("[]") == []

    def test_invalid_json(self, tmp_path):
        c = BirminghamDogsHomeChecker(str(tmp_path))
        assert c.parse("not json") == []

    def test_available_dog_returned(self, tmp_path):
        dogs_json = json.dumps([
            _dog_json(
                name="Harley",
                breed="Akita",
                sex="Male (N)",
                age="10 years, 2 months",
                centre="Wolverhampton Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/harley-138676/",
                photo_url="https://example.com/photo.jpg",
            )
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 1
        d = dogs[0]
        assert d.name == "Harley"
        assert d.breed == "Akita"
        assert d.gender == "Male"
        assert d.age == "10 years, 2 months"
        assert d.location == "Wolverhampton Centre"
        assert d.status == "Available"
        assert d.url == "https://birminghamdogshome.org.uk/dogs/harley-138676/"
        assert d.photo_url == "https://example.com/photo.jpg"

    def test_female_no_neuter_tag(self, tmp_path):
        dogs_json = json.dumps([
            _dog_json(
                name="Rouge",
                breed="Pug",
                sex="Female",
                age="5 years, 0 months",
                centre="Wolverhampton Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/rouge-138713/",
            )
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 1
        assert dogs[0].gender == "Female"

    def test_filters_reserved(self, tmp_path):
        dogs_json = json.dumps([
            _dog_json(
                name="Rover",
                breed="Labrador",
                sex="Male",
                age="2 years",
                centre="Birmingham Centre",
                status="RESERVE",
                link="https://birminghamdogshome.org.uk/dogs/rover-1/",
            ),
            _dog_json(
                name="Buddy",
                breed="Poodle",
                sex="Male",
                age="1 year",
                centre="Birmingham Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/buddy-2/",
            ),
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 1
        assert dogs[0].name == "Buddy"

    def test_filters_onhold(self, tmp_path):
        dogs_json = json.dumps([
            _dog_json(
                name="Snowy",
                breed="Maltese",
                sex="Male",
                age="0 years, 4 months",
                centre="Wolverhampton Centre",
                status="ONHOLD",
                link="https://birminghamdogshome.org.uk/dogs/snowy-138716/",
            ),
            _dog_json(
                name="Harley",
                breed="Akita",
                sex="Male (N)",
                age="10 years",
                centre="Wolverhampton Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/harley-138676/",
            ),
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 1
        assert dogs[0].name == "Harley"

    def test_both_centres_included(self, tmp_path):
        dogs_json = json.dumps([
            _dog_json(
                name="BrumDog",
                breed="Staffy",
                sex="Male",
                age="3 years",
                centre="Birmingham Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/brum-1/",
            ),
            _dog_json(
                name="WolvesDog",
                breed="Greyhound",
                sex="Female",
                age="4 years",
                centre="Wolverhampton Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/wolves-2/",
            ),
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 2
        centres = {d.location for d in dogs}
        assert centres == {"Birmingham Centre", "Wolverhampton Centre"}

    def test_missing_optional_fields(self, tmp_path):
        """Dog with no photo_url should still parse."""
        dogs_json = json.dumps([
            _dog_json(
                name="Ghost",
                breed="Unknown",
                sex="Male",
                age="Unknown",
                centre="Birmingham Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/ghost-999/",
            )
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 1
        assert dogs[0].photo_url == ""

    def test_female_neutered_normalized(self, tmp_path):
        dogs_json = json.dumps([
            _dog_json(
                name="Luna",
                breed="Collie",
                sex="Female (N)",
                age="6 years",
                centre="Birmingham Centre",
                status="AVAIL",
                link="https://birminghamdogshome.org.uk/dogs/luna-3/",
            )
        ])
        c = BirminghamDogsHomeChecker(str(tmp_path))
        dogs = c.parse(dogs_json)
        assert len(dogs) == 1
        assert dogs[0].gender == "Female"
