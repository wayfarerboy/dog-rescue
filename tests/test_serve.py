"""Tests for serve.py — local HTML server with live ignore toggles."""

from __future__ import annotations

import time
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


def test_reload_broadcasts_to_events_when_html_changes(tmp_path: Path, monkeypatch):
    """A page connected to /events is told to reload when dogs.html changes."""
    import http.client
    import threading

    html = tmp_path / "dogs.html"
    html.write_text("<html>v1</html>")
    monkeypatch.setattr(serve, "HTML_PATH", html)

    server = serve.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=serve._watch_html, daemon=True).start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("GET", "/events")
        resp = conn.getresponse()
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "text/event-stream"

        # Changing dogs.html should trigger a reload broadcast.
        html.write_text("<html>v2</html>")

        lines = []
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = resp.readline()
            if not line:
                break
            lines.append(line.decode())
            if "event: reload" in lines[-1]:
                break
        assert any("event: reload" in ln for ln in lines), f"no reload event: {lines!r}"
        conn.close()
    finally:
        server.shutdown()
        server.server_close()


def test_reload_post_endpoint(tmp_path: Path, monkeypatch):
    """POST /reload broadcasts a reload to /events clients."""
    import http.client
    import threading
    import urllib.request

    html = tmp_path / "dogs.html"
    html.write_text("<html>v1</html>")
    monkeypatch.setattr(serve, "HTML_PATH", html)

    server = serve.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("GET", "/events")
        resp = conn.getresponse()
        assert resp.status == 200

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/reload", data=b"") as r:
            assert r.status == 200

        lines = []
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = resp.readline()
            if not line:
                break
            lines.append(line.decode())
            if "event: reload" in lines[-1]:
                break
        assert any("event: reload" in ln for ln in lines), f"no reload event: {lines!r}"
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
