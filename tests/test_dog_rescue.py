import contextlib
import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

from distance_lookup import DistanceLookup
from dog_rescue import load_env, main
from sites.base import Dog


class _FakeSMTP2GoResponse:
    """Context-manager stand-in for urllib.request.urlopen that fakes a
    successful SMTP2Go send response."""

    def __init__(self, body=None):
        self._body = body if body is not None else (
            b'{"data":{"succeeded":1,"failed":0,"failures":[]}}'
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


class TestLoadEnv:
    def test_file_not_found(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        assert load_env() == {}

    def test_parses_key_value(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\nSUBJECT=Hello\n")
        env = load_env()
        assert env == {"EMAIL": "test@example.com", "SUBJECT": "Hello"}

    def test_handles_quoted_values(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        (tmp_path / ".env").write_text('EMAIL="test@example.com"\n')
        assert load_env()["EMAIL"] == "test@example.com"

    def test_handles_single_quoted_values(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL='test@example.com'\n")
        assert load_env()["EMAIL"] == "test@example.com"

    def test_skips_comments_and_empty_lines(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        (tmp_path / ".env").write_text(
            "# comment\n\n  \nEMAIL=test@example.com\n# another\n"
        )
        assert load_env() == {"EMAIL": "test@example.com"}

    def test_strips_whitespace(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        (tmp_path / ".env").write_text("  EMAIL = test@example.com  \n")
        assert load_env() == {"EMAIL": "test@example.com"}


class TestMain:
    def test_no_email_set_exits(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def _enter_all_checker_patches(self, stack, *, return_value=None, side_effect=None):
        """Enter patches for all known checkers using ExitStack."""
        checkers = [
            "sites.all_dogs_matter.AllDogsMatterChecker.get_all",
            "sites.amicii.AmiciiChecker.get_all",
            "sites.birmingham_dogs_home.BirminghamDogsHomeChecker.get_all",
            "sites.blue_cross.BlueCrossChecker.get_all",
            "sites.brighter_days.BrighterDaysChecker.get_all",
            "sites.cheltenham.CheltenhamChecker.get_all",
            "sites.cotswolds.CotswoldsChecker.get_all",
            "sites.dogs_trust.DogsTrustChecker.get_all",
            "sites.east_midlands.EastMidlandsDogRescueChecker.get_all",
            "sites.forest_dog_rescue.ForestDogRescueChecker.get_all",
            "sites.gsdr.GsdrChecker.get_all",
            "sites.happy_staffie.HappyStaffieChecker.get_all",
            "sites.jerry_green.JerryGreenChecker.get_all",
            "sites.many_tears.ManyTearsChecker.get_all",
            "sites.paws2rescue.Paws2RescueChecker.get_all",
            "sites.pro_dogs_direct.ProDogsDirectChecker.get_all",
            "sites.raystede.RaystedeChecker.get_all",
            "sites.rspca_brighton.RSPCABrightonChecker.get_all",
            "sites.rspca_leeds.RSPCALeedsChecker.get_all",
            "sites.scsr.SCSRChecker.get_all",
            "sites.small_dog_rescue.SmallDogRescueChecker.get_all",
            "sites.south_east_dog_rescue.SouthEastDogRescueChecker.get_all",
            "sites.spaniel_aid.SpanielAidChecker.get_all",
            "sites.starfish.StarfishChecker.get_all",
            "sites.wild_acre.WildAcreChecker.get_all",
            "sites.wythall.WythallChecker.get_all",
        ]
        kwargs = {}
        if side_effect is not None:
            kwargs["side_effect"] = side_effect
        else:
            kwargs["return_value"] = return_value if return_value is not None else []
        for c in checkers:
            stack.enter_context(patch(c, **kwargs))

    def test_no_new_dogs(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        stack = contextlib.ExitStack()
        self._enter_all_checker_patches(stack)
        mock_print = stack.enter_context(patch("builtins.print"))
        try:
            main()
            # Last print is the summary line to stderr
            calls = [c[0][0] for c in mock_print.call_args_list]
            assert any("0 matched criteria — none new." in c for c in calls)
        finally:
            stack.close()

    def test_sends_email_on_new_dogs(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text(
            "EMAIL=test@example.com\nSMTP2GO_API_KEY=api-test\n"
        )

        fake_dog = Dog(
            name="Bella",
            age="6 Months",
            gender="Female",
            breed="Spaniel",
            url="https://example.org/bella",
            status="Available",
            location="Cardiff",
            photo_url="",
        )

        stack = contextlib.ExitStack()
        self._enter_all_checker_patches(stack, return_value=[])
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.get_all", return_value=[fake_dog])
        )
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                  return_value="=== Section ===")
        )
        mock_run = stack.enter_context(patch("subprocess.run"))
        mock_urlopen = stack.enter_context(
            patch("urllib.request.urlopen", return_value=_FakeSMTP2GoResponse())
        )
        try:
            main()
            # The email is sent via the SMTP2Go API, not msmtp/subprocess.
            # subprocess.run is used only to regenerate dogs.html afterwards.
            assert mock_run.call_count == 1
            regen = mock_run.call_args_list[0]
            assert regen.args[0][-2:] == ["--html", "--cached"]
            # Inspect the SMTP2Go request payload.
            req = mock_urlopen.call_args.args[0]
            body = json.loads(req.data.decode())
            assert body["to"] == ["test@example.com"]
            assert "=== Section ===" in body["text_body"]
            assert body["html_body"]
        finally:
            stack.close()

    def test_missing_smtp2go_api_key_exits(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        fake_dog = Dog(
            name="Bella",
            age="6",
            gender="Female",
            breed="X",
            url="https://a",
            status="",
            location="",
            photo_url="",
        )

        stack = contextlib.ExitStack()
        self._enter_all_checker_patches(stack, return_value=[])
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.get_all",
                  return_value=[fake_dog])
        )
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                  return_value="X")
        )
        try:
            with pytest.raises(SystemExit) as exc:
                main()
        finally:
            stack.close()
        assert exc.value.code == 1

    def test_smtp2go_http_error_exits(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text(
            "EMAIL=test@example.com\nSMTP2GO_API_KEY=api-test\n"
        )

        fake_dog = Dog(
            name="Bella",
            age="6",
            gender="Female",
            breed="X",
            url="https://a",
            status="",
            location="",
            photo_url="",
        )

        stack = contextlib.ExitStack()
        self._enter_all_checker_patches(stack, return_value=[])
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.get_all",
                  return_value=[fake_dog])
        )
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                  return_value="X")
        )
        http_err = urllib.error.HTTPError(
            "https://api.smtp2go.com", 401, "Unauthorized", {}, None
        )
        stack.enter_context(
            patch("urllib.request.urlopen", side_effect=http_err)
        )
        try:
            with pytest.raises(SystemExit) as exc:
                main()
        finally:
            stack.close()
        assert exc.value.code == 1

    def test_checker_error_does_not_block_others(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text(
            "EMAIL=test@example.com\nSMTP2GO_API_KEY=api-test\n"
        )

        fake_dog = Dog(
            name="Bella",
            age="6",
            gender="Female",
            breed="X",
            url="https://a",
            status="",
            location="",
            photo_url="",
        )

        stack = contextlib.ExitStack()
        self._enter_all_checker_patches(stack, return_value=[])
        # Override all_dogs_matter to raise
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.get_all",
                  side_effect=RuntimeError("boom"))
        )
        # Override scsr to return dog
        stack.enter_context(
            patch("sites.scsr.SCSRChecker.get_all", return_value=[fake_dog])
        )
        stack.enter_context(
            patch("sites.scsr.SCSRChecker.format_section",
                  return_value="=== SCSR ===")
        )
        mock_run = stack.enter_context(patch("subprocess.run"))
        mock_urlopen = stack.enter_context(
            patch("urllib.request.urlopen", return_value=_FakeSMTP2GoResponse())
        )
        try:
            main()
            assert mock_run.call_count == 1  # dogs.html regen only
            req = mock_urlopen.call_args.args[0]
            body = json.loads(req.data.decode())
            assert "=== SCSR ===" in body["text_body"]
        finally:
            stack.close()

    def test_distance_filtering_excludes_far_dogs(self, tmp_path: Path, monkeypatch):
        """Dogs from centers beyond MAX_DISTANCE_MILES are excluded from email."""
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text(
            "EMAIL=test@example.com\nSMTP2GO_API_KEY=api-test\nMAX_DISTANCE_MILES=100\n"
        )

        near_dog = Dog(
            name="Bella",
            age="6 Months",
            gender="Female",
            breed="Spaniel",
            url="https://example.org/near",
            status="Available",
            location="Cardiff",
            photo_url="",
        )
        far_dog = Dog(
            name="Luna",
            age="8 Months",
            gender="Female",
            breed="Lab",
            url="https://example.org/far",
            status="Available",
            location="Edinburgh",
            photo_url="",
        )

        stack = contextlib.ExitStack()
        self._enter_all_checker_patches(stack, return_value=[])
        # Override all_dogs_matter with test dogs
        stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.get_all",
                  return_value=[near_dog, far_dog])
        )
        mock_format = stack.enter_context(
            patch("sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                  return_value="=== Section ===")
        )
        stack.enter_context(
            patch.object(DistanceLookup, "_load", return_value=None)
        )
        stack.enter_context(
            patch.object(DistanceLookup, "get_distance",
                        side_effect=lambda center: {"Cardiff": 80.0, "Edinburgh": 320.0}.get(center))
        )
        stack.enter_context(patch("subprocess.run"))
        stack.enter_context(
            patch("urllib.request.urlopen", return_value=_FakeSMTP2GoResponse())
        )
        try:
            main()
            # format_section called with only the near dog (far dog filtered out)
            call_args = mock_format.call_args[0]
            filtered_dogs = call_args[0]
            assert len(filtered_dogs) == 1
            assert filtered_dogs[0].name == "Bella"
            assert filtered_dogs[0].location == "Cardiff"
        finally:
            stack.close()
