"""Tests for repair_cache.py."""

from repair_cache import missing_fields, parse_entry


class TestParseEntry:
    def test_full_eight_fields(self):
        line = "Available | Bella | 6 Months | Female | Labrador | Cardiff | https://example.com/photo.jpg | https://example.com/bella"
        parts = parse_entry(line)
        assert len(parts) == 8
        assert parts == [
            "Available",
            "Bella",
            "6 Months",
            "Female",
            "Labrador",
            "Cardiff",
            "https://example.com/photo.jpg",
            "https://example.com/bella",
        ]

    def test_old_format_seven_fields(self):
        """7-field entry (pre-photo_url) gets photo_url empty inserted at index 6."""
        line = "Available | Bella | 6 Months | Female | Labrador | Cardiff | https://example.com/bella"
        parts = parse_entry(line)
        assert len(parts) == 8
        assert parts[6] == ""  # photo_url inserted empty
        assert parts[7] == "https://example.com/bella"

    def test_old_format_https(self):
        """https URLs also detected as old format."""
        line = "Available | Bella | 6 Months | Female | Labrador | Cardiff | https://example.com/bella"
        parts = parse_entry(line)
        assert len(parts) == 8
        assert parts[7] == "https://example.com/bella"

    def test_leading_empty_field(self):
        """Line starts with '| ' — empty first field preserved."""
        line = " | Gwen | 11 weeks | Female | Cavachon | Llanelli | https://example.com/gwen"
        parts = parse_entry(line)
        assert len(parts) == 8
        assert parts[0] == ""  # empty status
        assert parts[1] == "Gwen"

    def test_leading_empty_with_old_format(self):
        """Leading empty + 7 fields → still normalized to 8."""
        line = " | Gwen | 11 weeks | Female | Cavachon | Llanelli | https://example.com/gwen"
        parts = parse_entry(line)
        assert len(parts) == 8
        assert parts[0] == ""  # status empty
        assert parts[6] == ""  # photo_url empty (old format)
        assert parts[7] == "https://example.com/gwen"

    def test_not_old_format_when_last_field_not_url(self):
        """7 fields but last isn't a URL → not treated as old format."""
        line = "a | b | c | d | e | f | g"
        parts = parse_entry(line)
        assert len(parts) == 7  # unchanged

    def test_already_eight_no_change(self):
        line = "Available | Bella | 6 Months | Female | Labrador | Cardiff | https://example.com/p.jpg | https://example.com/bella"
        parts = parse_entry(line)
        assert len(parts) == 8


class TestMissingFields:
    def test_all_present(self):
        parts = ["Available", "Bella", "6M", "Female", "Lab", "Cardiff", "http://p.jpg", "http://b"]
        assert missing_fields(parts) == {}

    def test_empty_fields_not_flagged(self):
        """Empty values within valid positions are not flagged - only
        structurally missing indices matter."""
        parts = ["", "Bella", "6M", "Female", "Lab", "Cardiff", "http://p.jpg", "http://b"]
        assert missing_fields(parts) == {}

    def test_empty_photo_url_not_flagged(self):
        parts = ["Available", "Bella", "6M", "Female", "Lab", "Cardiff", "", "http://b"]
        assert missing_fields(parts) == {}

    def test_multiple_empty_not_flagged(self):
        parts = ["", "Bella", "6M", "Female", "Lab", "", "", "http://b"]
        assert missing_fields(parts) == {}

    def test_too_few_fields(self):
        """Extremely short entry: indices beyond len(parts) are flagged.

        parse_entry would normally normalize old formats before
        missing_fields is called. Direct 5-field input flags
        indices 5-7 as missing (beyond parts length).
        """
        parts = ["Bella", "6M", "Female", "Lab", "http://b"]
        missing = missing_fields(parts)
        # Indices 0-4 are present (no empty checks)
        assert 0 not in missing
        # Indices 5-7 are beyond parts length
        assert 5 in missing  # location
        assert 6 in missing  # photo_url
        assert 7 in missing  # url

    def test_seven_fields_not_flagged_when_normalized(self):
        """After parse_entry normalizes old 7-field format to 8,
        no positions are structurally missing."""
        parts = ["Available", "Bella", "6M", "Female", "Lab", "Cardiff", "", "http://b"]
        missing = missing_fields(parts)
        assert missing == {}
