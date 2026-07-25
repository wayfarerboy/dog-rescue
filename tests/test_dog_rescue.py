import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

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
            patch("sites.many_tears.ManyTearsChecker.check", return_value=[]),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
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
        })()

        with (
            patch(
                "sites.many_tears.ManyTearsChecker.check", return_value=[fake_dog]
            ),
            patch(
                "sites.many_tears.ManyTearsChecker.format_section",
                return_value="=== Section ===",
            ),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
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
            "gender": "F",
            "breed": "X",
            "url": "https://a",
            "status": "",
            "location": "",
        })()

        with (
            patch(
                "sites.many_tears.ManyTearsChecker.check", return_value=[fake_dog]
            ),
            patch(
                "sites.many_tears.ManyTearsChecker.format_section",
                return_value="X",
            ),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
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
            "gender": "F",
            "breed": "X",
            "url": "https://a",
            "status": "",
            "location": "",
        })()

        with (
            patch(
                "sites.many_tears.ManyTearsChecker.check", return_value=[fake_dog]
            ),
            patch(
                "sites.many_tears.ManyTearsChecker.format_section",
                return_value="X",
            ),
            patch("sites.scsr.SCSRChecker.check", return_value=[]),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
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
            "gender": "F",
            "breed": "X",
            "url": "https://a",
            "status": "",
            "location": "",
        })()

        with (
            patch(
                "sites.many_tears.ManyTearsChecker.check",
                side_effect=RuntimeError("boom"),
            ),
            patch(
                "sites.scsr.SCSRChecker.check", return_value=[fake_dog]
            ),
            patch(
                "sites.scsr.SCSRChecker.format_section",
                return_value="=== SCSR ===",
            ),
            patch("sites.dogs_trust.DogsTrustChecker.check", return_value=[]),
            patch("sites.pro_dogs_direct.ProDogsDirectChecker.check", return_value=[]),
            patch("subprocess.run") as mock_run,
        ):
            main()
            mock_run.assert_called_once()
            assert "=== SCSR ===" in mock_run.call_args.kwargs["input"]
