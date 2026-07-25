import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from distance_lookup import DistanceLookup
from dog_rescue import load_env, main


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

    def test_no_new_dogs(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        with (
            patch("sites.all_dogs_matter.AllDogsMatterChecker.check", return_value=[]),
            patch("sites.cotswolds.CotswoldsChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.jerry_green.JerryGreenChecker.check", return_value=[]),
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.paws2rescue.Paws2RescueChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("sites.raystede.RaystedeChecker.check", return_value=[]),
            patch("sites.rspca_brighton.RSPCABrightonChecker.check", return_value=[]),
            patch("sites.rspca_leeds.RSPCALeedsChecker.check", return_value=[]),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch(
                "sites.south_east_dog_rescue.SouthEastDogRescueChecker.check",
                return_value=[],
            ),
            patch("sites.spaniel_aid.SpanielAidChecker.check", return_value=[]),
            patch("sites.teckels.TeckelsChecker.check", return_value=[]),
            patch("sites.wythall.WythallChecker.check", return_value=[]),
            patch("sites.gsdr.GsdrChecker.check", return_value=[]),
            patch("builtins.print") as mock_print,
        ):
            main()
            mock_print.assert_called_with("No new dogs since last check.")

    def test_sends_email_on_new_dogs(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        fake_dog = type("Dog", (), {
            "name": "Bella",
            "age": "6 Months",
            "gender": "Female",
            "breed": "Spaniel",
            "url": "https://example.org",
            "status": "Available",
            "location": "Cardiff",
            "photo_url": "",
        })()

        with (
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.check", return_value=[fake_dog]
            ),
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                return_value="=== Section ===",
            ),
            patch("sites.cotswolds.CotswoldsChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.jerry_green.JerryGreenChecker.check", return_value=[]),
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.paws2rescue.Paws2RescueChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("sites.raystede.RaystedeChecker.check", return_value=[]),
            patch("sites.rspca_brighton.RSPCABrightonChecker.check", return_value=[]),
            patch("sites.rspca_leeds.RSPCALeedsChecker.check", return_value=[]),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch(
                "sites.south_east_dog_rescue.SouthEastDogRescueChecker.check",
                return_value=[],
            ),
            patch("sites.spaniel_aid.SpanielAidChecker.check", return_value=[]),
            patch("subprocess.run") as mock_run,
        ):
            main()
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            assert args[0] == ["msmtp", "-t"]
            assert "test@example.com" in kwargs["input"]
            assert "=== Section ===" in kwargs["input"]

    def test_msmtp_not_found_exits(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        fake_dog = type("Dog", (), {
            "name": "Bella",
            "age": "6",
            "gender": "Female",
            "breed": "X",
            "url": "https://a",
            "status": "",
            "location": "",
            "photo_url": "",
        })()

        with (
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.check",
                return_value=[fake_dog],
            ),
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                return_value="X",
            ),
            patch("sites.cotswolds.CotswoldsChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.jerry_green.JerryGreenChecker.check", return_value=[]),
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.paws2rescue.Paws2RescueChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("sites.raystede.RaystedeChecker.check", return_value=[]),
            patch("sites.rspca_brighton.RSPCABrightonChecker.check", return_value=[]),
            patch("sites.rspca_leeds.RSPCALeedsChecker.check", return_value=[]),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch(
                "sites.south_east_dog_rescue.SouthEastDogRescueChecker.check",
                return_value=[],
            ),
            patch("sites.spaniel_aid.SpanielAidChecker.check", return_value=[]),
            patch("sites.teckels.TeckelsChecker.check", return_value=[]),
            patch("sites.wythall.WythallChecker.check", return_value=[]),
            patch("sites.gsdr.GsdrChecker.check", return_value=[]),
            patch("subprocess.run", side_effect=FileNotFoundError),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

    def test_subprocess_error_exits(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        fake_dog = type("Dog", (), {
            "name": "Bella",
            "age": "6",
            "gender": "Female",
            "breed": "X",
            "url": "https://a",
            "status": "",
            "location": "",
            "photo_url": "",
        })()

        with (
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.check",
                return_value=[fake_dog],
            ),
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                return_value="X",
            ),
            patch("sites.cotswolds.CotswoldsChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.jerry_green.JerryGreenChecker.check", return_value=[]),
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.paws2rescue.Paws2RescueChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("sites.raystede.RaystedeChecker.check", return_value=[]),
            patch("sites.rspca_brighton.RSPCABrightonChecker.check", return_value=[]),
            patch("sites.rspca_leeds.RSPCALeedsChecker.check", return_value=[]),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch(
                "sites.south_east_dog_rescue.SouthEastDogRescueChecker.check",
                return_value=[],
            ),
            patch("sites.spaniel_aid.SpanielAidChecker.check", return_value=[]),
            patch("sites.teckels.TeckelsChecker.check", return_value=[]),
            patch("sites.wythall.WythallChecker.check", return_value=[]),
            patch("sites.gsdr.GsdrChecker.check", return_value=[]),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "msmtp"),
            ),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

    def test_checker_error_does_not_block_others(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text("EMAIL=test@example.com\n")

        fake_dog = type("Dog", (), {
            "name": "Bella",
            "age": "6",
            "gender": "Female",
            "breed": "X",
            "url": "https://a",
            "status": "",
            "location": "",
            "photo_url": "",
        })()

        with (
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.check",
                side_effect=RuntimeError("boom"),
            ),
            patch("sites.cotswolds.CotswoldsChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.jerry_green.JerryGreenChecker.check", return_value=[]),
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.paws2rescue.Paws2RescueChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("sites.raystede.RaystedeChecker.check", return_value=[]),
            patch("sites.rspca_brighton.RSPCABrightonChecker.check", return_value=[]),
            patch("sites.rspca_leeds.RSPCALeedsChecker.check", return_value=[]),
            patch(
                "sites.scsr.SCSRChecker.check", return_value=[fake_dog]
            ),
            patch(
                "sites.scsr.SCSRChecker.format_section",
                return_value="=== SCSR ===",
            ),
            patch(
                "sites.south_east_dog_rescue.SouthEastDogRescueChecker.check",
                return_value=[],
            ),
            patch("sites.spaniel_aid.SpanielAidChecker.check", return_value=[]),
            patch("sites.teckels.TeckelsChecker.check", return_value=[]),
            patch("sites.wythall.WythallChecker.check", return_value=[]),
            patch("sites.gsdr.GsdrChecker.check", return_value=[]),
            patch("subprocess.run") as mock_run,
        ):
            main()
            mock_run.assert_called_once()
            assert "=== SCSR ===" in mock_run.call_args.kwargs["input"]

    def test_distance_filtering_excludes_far_dogs(self, tmp_path: Path, monkeypatch):
        """Dogs from centers beyond MAX_DISTANCE_MILES are excluded from email."""
        monkeypatch.setattr("dog_rescue.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("dog_rescue.DATA_DIR", tmp_path)
        (tmp_path / ".env").write_text(
            "EMAIL=test@example.com\nMAX_DISTANCE_MILES=100\n"
        )

        near_dog = type("Dog", (), {
            "name": "Bella",
            "age": "6 Months",
            "gender": "Female",
            "breed": "Spaniel",
            "url": "https://example.org/near",
            "status": "Available",
            "location": "Cardiff",
            "photo_url": "",
        })()
        far_dog = type("Dog", (), {
            "name": "Luna",
            "age": "8 Months",
            "gender": "Female",
            "breed": "Lab",
            "url": "https://example.org/far",
            "status": "Available",
            "location": "Edinburgh",
            "photo_url": "",
        })()

        with (
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.check",
                return_value=[near_dog, far_dog],
            ),
            patch(
                "sites.all_dogs_matter.AllDogsMatterChecker.format_section",
                return_value="=== Section ===",
            ) as mock_format,
            patch("sites.cotswolds.CotswoldsChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.jerry_green.JerryGreenChecker.check", return_value=[]),
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.paws2rescue.Paws2RescueChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("sites.raystede.RaystedeChecker.check", return_value=[]),
            patch("sites.rspca_brighton.RSPCABrightonChecker.check", return_value=[]),
            patch("sites.rspca_leeds.RSPCALeedsChecker.check", return_value=[]),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch(
                "sites.south_east_dog_rescue.SouthEastDogRescueChecker.check",
                return_value=[],
            ),
            patch("sites.spaniel_aid.SpanielAidChecker.check", return_value=[]),
            patch("sites.teckels.TeckelsChecker.check", return_value=[]),
            patch("sites.wythall.WythallChecker.check", return_value=[]),
            patch("sites.gsdr.GsdrChecker.check", return_value=[]),
            patch.object(DistanceLookup, "_load", return_value=None),
            patch.object(
                DistanceLookup,
                "get_distance",
                side_effect=lambda center: {"Cardiff": 80.0, "Edinburgh": 320.0}.get(center),
            ),
            patch("subprocess.run"),
        ):
            main()
            # format_section called with only the near dog (far dog filtered out)
            call_args = mock_format.call_args[0]
            filtered_dogs = call_args[0]
            assert len(filtered_dogs) == 1
            assert filtered_dogs[0].name == "Bella"
            assert filtered_dogs[0].location == "Cardiff"
