#!/usr/bin/env python3
"""Serve dogs.html with live Ignored-dog toggles.

Run from the repo root (or via the CLI menu -> List Dogs -> Serve HTML):

    python3 serve.py [port]

Starts a local HTTP server. Clicking **Ignore** / **Un-ignore** on a card
persists the change to data/ignored.txt, so the page and the rest of the
system stay in sync. Press Ctrl-C to stop.

By default the page is opened in the local default browser. Pass
`--no-browser` to skip that (e.g. when serving to other devices on your LAN
and running this on a headless/SSH machine where the AppleEvent to open a
browser can hang and time out).
"""

from __future__ import annotations

import json
import queue
import socket
import sys
import threading
import time
import webbrowser
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ignore import IgnoredList

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
HTML_PATH = SCRIPT_DIR / "dogs.html"
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"  # serve on all interfaces so other LAN devices can reach us

# SSE clients (queue per connection) + broadcast lock, for auto-reload on new dogs.
_sse_clients: list[queue.Queue] = []
_sse_lock = threading.Lock()


def _broadcast_reload() -> None:
    """Tell every connected page to reload (new dogs found)."""
    with _sse_lock:
        clients = list(_sse_clients)
    for q in clients:
        with suppress(queue.Full):
            q.put_nowait(time.time_ns())


def _watch_html() -> None:
    """Poll dogs.html; when it changes (e.g. regenerated after a daily check)
    broadcast a reload so open pages pick up newly found dogs automatically."""
    last = HTML_PATH.stat().st_mtime_ns if HTML_PATH.exists() else None
    while True:
        time.sleep(1)
        try:
            mtime = HTML_PATH.stat().st_mtime_ns if HTML_PATH.exists() else None
        except OSError:
            mtime = None
        if mtime != last:
            last = mtime
            _broadcast_reload()


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

    ignored = IgnoredList(str(DATA_DIR))
    results = list_dogs.list_cached(str(DATA_DIR))
    HTML_PATH.write_text(list_dogs.format_html(results, ignored=ignored))
    total = sum(len(dogs) for _, dogs in results)
    print(f"Regenerated {HTML_PATH.name} ({total} dogs, {len(ignored)} ignored)")


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

    def _events(self) -> None:
        """Server-Sent Events endpoint: broadcasts a reload when dogs.html changes."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q: queue.Queue = queue.Queue(maxsize=16)
        with _sse_lock:
            _sse_clients.append(q)
        try:
            while True:
                try:
                    q.get(timeout=15)  # a reload signal arrived
                except queue.Empty:
                    try:
                        self.wfile.write(b": ping\n\n")  # keepalive
                        self.wfile.flush()
                    except OSError:
                        break
                    continue
                try:
                    self.wfile.write(b"event: reload\ndata: 1\n\n")
                    self.wfile.flush()
                except OSError:
                    break
        finally:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html", "/dogs.html"):
            self._serve_html()
        elif path == "/api/ignored":
            dl = IgnoredList(str(DATA_DIR))
            self._send_json({"urls": dl.urls()})
        elif path == "/events":
            self._events()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/ignored/toggle":
            url = (parse_qs(parsed.query).get("url") or [""])[0]
            dl = IgnoredList(str(DATA_DIR))
            now = dl.toggle(url)
            self._send_json({"url": url, "ignored": now})
        elif parsed.path == "/reload":
            _broadcast_reload()
            self._send_json({"ok": True})
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args) -> None:  # quieter, to stderr
        sys.stderr.write(f"[{self.address_string()}] " + (fmt % args) + "\n")


def _open_browser(url: str) -> None:
    """Open the page in the default browser without blocking or crashing.

    On macOS `webbrowser.open()` shells out to `osascript open location`, which
    dispatches a GUI AppleEvent to the default browser. In a headless/SSH
    context that call can hang for ~40s and then raise "AppleEvent timed out"
    (-1712), stalling server startup. Run it detached so it can never block
    the server, and swallow any error.
    """

    def _open() -> None:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    open_browser = True
    args = sys.argv[1:]
    if "--no-browser" in args:
        open_browser = False
        args.remove("--no-browser")
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

    threading.Thread(target=_watch_html, daemon=True).start()

    print(f"\n  Serving {HTML_PATH.name}")
    print(f"  This machine : http://127.0.0.1:{actual_port}/")
    if host in ("0.0.0.0", ""):
        print(f"  LAN (others) : http://{_lan_ip()}:{actual_port}/")
    print("  Ignored toggles update data/ignored.txt.")
    if open_browser:
        print("  Press Ctrl-C to stop.\n")
        _open_browser(f"http://127.0.0.1:{actual_port}/")
    else:
        print("  (browser opening disabled: open the This machine / LAN URL yourself)")
        print("  Press Ctrl-C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
