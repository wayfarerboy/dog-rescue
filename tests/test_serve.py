"""Tests for serve.py — local HTML server with live ignore toggles."""

from __future__ import annotations

from pathlib import Path

import serve


def test_ensure_html_writes_file(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "cotswolds.txt").write_text(
        "Available | Bella | 6 Months | Female | Spaniel | Cardiff |  | https://ex.org/b\n"
    )

    monkeypatch.setattr(serve, "DATA_DIR", data_dir)
    monkeypatch.setattr(serve, "HTML_PATH", tmp_path / "dogs.html")

    serve._ensure_html()

    html = (tmp_path / "dogs.html").read_text()
    assert "Bella" in html
    assert "disc-btn" in html
