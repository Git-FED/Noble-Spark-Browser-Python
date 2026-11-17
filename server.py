"""Noble Spark server — talk to the browser over HTTP.

Run:  python3 server.py
Then:  curl -X POST http://127.0.0.1:8901/open -d '{"url": "https://example.com"}'

Listens on 127.0.0.1 only (this machine) unless NOBLE_SPARK_HOST is set.
If NOBLE_SPARK_KEY is set, every request must carry it as
`X-Api-Key: <key>` — otherwise the browser answers anyone who finds it.

Endpoints (all JSON in, JSON out):
  GET  /            status + current URL
  POST /open        {"url": "..."}            -> {"url", "title"}
  GET  /title       page title
  GET  /url         current URL
  POST /text        {}                        -> {"text": "..."}
  POST /links       {}                        -> {"links": [{text, href}]}
  POST /click       {"selector": "text=Log in"}
  POST /fill        {"selector": "#email", "text": "a@b.com"}
  POST /screenshot  {"path": "shots/home.png"} -> {"path": "..."}
  POST /close       {}                        -> shuts the browser down
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from browser import NobleSparkBrowser

HOST = os.environ.get("NOBLE_SPARK_HOST", "127.0.0.1")
PORT = int(os.environ.get("NOBLE_SPARK_PORT", "8901"))
API_KEY = os.environ.get("NOBLE_SPARK_KEY", "")
SHOTS_DIR = os.environ.get("NOBLE_SPARK_SHOTS", "shots")

_browser = None


def get_browser():
    global _browser
    if _browser is None:
        _browser = NobleSparkBrowser(headless=True)
    return _browser


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _authorized(self):
        if not API_KEY:
            return True
        return self.headers.get("X-Api-Key") == API_KEY

    def _route(self, method):
        global _browser
        if not self._authorized():
            return self._send(401, {"error": "bad or missing X-Api-Key"})
        try:
            if method == "GET" and self.path == "/":
                b = _browser
                return self._send(200, {
                    "app": "noble-spark",
                    "status": "ok",
                    "url": b.url() if b else None,
                })
            b = get_browser()
            if method == "GET" and self.path == "/title":
                return self._send(200, {"title": b.title()})
            if method == "GET" and self.path == "/url":
                return self._send(200, {"url": b.url()})
            data = self._read_json() if method == "POST" else {}
            if method == "POST" and self.path == "/open":
                if not data.get("url"):
                    return self._send(400, {"error": "need {\"url\": ...}"})
                return self._send(200, b.open(data["url"]))
            if method == "POST" and self.path == "/text":
                return self._send(200, {"text": b.text()})
            if method == "POST" and self.path == "/links":
                return self._send(200, {"links": b.links()})
            if method == "POST" and self.path == "/click":
                if not data.get("selector"):
                    return self._send(400, {"error": "need {\"selector\": ...}"})
                return self._send(200, b.click(data["selector"]))
            if method == "POST" and self.path == "/fill":
                if not data.get("selector") or "text" not in data:
                    return self._send(400, {"error": "need {\"selector\", \"text\"}"})
                return self._send(200, b.fill(data["selector"], data["text"]))
            if method == "POST" and self.path == "/screenshot":
                os.makedirs(SHOTS_DIR, exist_ok=True)
                path = data.get("path") or os.path.join(SHOTS_DIR, "shot.png")
                return self._send(200, {"path": b.screenshot(path)})
            if method == "POST" and self.path == "/close":
                b.close()
                _browser = None
                return self._send(200, {"closed": True})
            return self._send(404, {"error": "unknown route: %s %s" % (method, self.path)})
        except Exception as exc:  # noqa: BLE001 - report the real error back
            return self._send(500, {"error": str(exc)})

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")


if __name__ == "__main__":
    print("Noble Spark listening on http://%s:%d" % (HOST, PORT), flush=True)
    print("Key auth: %s" % ("ON" if API_KEY else "OFF (local only)"), flush=True)
    print("One request at a time: Playwright's browser lives on this thread.",
          flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
