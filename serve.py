#!/usr/bin/env python3
"""Serve dogs.html with live Discounted-dog toggles.

Run from the repo root (or via the CLI menu -> List Dogs -> Serve HTML):

    python3 serve.py [port]

Starts a local HTTP server. Clicking **Discount** / **Un-discount** on a card
persists the change to data/discounted.txt, so the page and the rest of the
system stay in sync. Press Ctrl-C to stop.
"""

from __future__ import annotations

import json
import socket
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from discount import DiscountedList

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
HTML_PATH = SCRIPT_DIR / "dogs.html"
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"  # serve on all interfaces so other LAN devices can reach us


def _lan_ip() -> str:
    """Best-effort LAN IP of this machine (falls back to localhost)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # does not send data; just picks the route
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _ensure_html() -> None:
    """Regenerate dogs.html from cached data so markers reflect current state."""
    import list_dogs

    discounted = DiscountedList(str(DATA_DIR))
    results = list_dogs.list_cached(str(DATA_DIR))
    HTML_PATH.write_text(list_dogs.format_html(results, discounted=discounted))
    total = sum(len(dogs) for _, dogs in results)
    print(f"Regenerated {HTML_PATH.name} ({total} dogs, {len(discounted)} discounted)")


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj: dict, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self) -> None:
        body = HTML_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html", "/dogs.html"):
            self._serve_html()
        elif path == "/api/discounted":
            dl = DiscountedList(str(DATA_DIR))
            self._send_json({"urls": dl.urls()})
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/discounted/toggle":
            url = (parse_qs(parsed.query).get("url") or [""])[0]
            dl = DiscountedList(str(DATA_DIR))
            now = dl.toggle(url)
            self._send_json({"url": url, "discounted": now})
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args) -> None:  # quieter, to stderr
        sys.stderr.write(f"[{self.address_string()}] " + (fmt % args) + "\n")


def main() -> None:
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    args = sys.argv[1:]
    # Positional port:  python serve.py 9000
    if args and args[0].lstrip("-").isdigit():
        port = int(args[0])
    if "--port" in args:
        port = int(args[args.index("--port") + 1])
    if "--host" in args:
        host = args[args.index("--host") + 1]

    _ensure_html()

    server = ThreadingHTTPServer((host, port), Handler)
    actual_port = server.server_address[1]

    print(f"\n  Serving {HTML_PATH.name}")
    print(f"  This machine : http://127.0.0.1:{actual_port}/")
    if host in ("0.0.0.0", ""):
        print(f"  LAN (others) : http://{_lan_ip()}:{actual_port}/")
    print("  Discounted toggles update data/discounted.txt.")
    print("  Press Ctrl-C to stop.\n")
    webbrowser.open(f"http://127.0.0.1:{actual_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
