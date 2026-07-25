from sites.base import Dog


class TestDog:
    def test_as_line(self):
        d = Dog(
            name="Bella",
            age="6 Months",
            gender="Female",
            breed="Cocker Spaniel",
            url="https://example.org/dogs/bella",
            status="Available",
            location="Cardiff",
        )
        line = d.as_line()
        assert line == (
            "Available | Bella | 6 Months | Female | Cocker Spaniel | Cardiff |  | "
            "https://example.org/dogs/bella"
        )

    def test_as_line_empty_status_and_location(self):
        d = Dog(
            name="Max",
            age="1 Year Old",
            gender="Male",
            breed="Labrador",
            url="https://example.org/max",
        )
        assert d.as_line() == (
            " | Max | 1 Year Old | Male | Labrador |  |  | https://example.org/max"
        )

    def test_as_line_unique_url_key(self):
        d1 = Dog(name="A", age="1", gender="F", breed="X", url="https://a")
        d2 = Dog(name="B", age="2", gender="M", breed="Y", url="https://b")
        assert d1.url != d2.url
