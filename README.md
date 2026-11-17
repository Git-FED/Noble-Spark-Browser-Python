# Noble Spark — a Python browser for Muse

A headless Chromium browser, written in Python, built for Muse to drive.
No window, no buttons to stare at. Muse opens pages, reads text, clicks,
fills forms, and takes screenshots through code.

## What it is

- `browser.py` — the engine. One Chromium browser that stays open.
  Open a page, read its text, click, fill, screenshot, list links.
- `server.py` — talk to the browser over HTTP (JSON in, JSON out).
  Start it once, then send it orders from anywhere on the same machine.
- `cli.py` — one-shot jobs from the command line.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

That's it. Python 3.10+ and those two commands.

## Use it — command line

```bash
python cli.py open https://example.com --text
python cli.py open https://example.com --shot shots/home.png
python cli.py open https://example.com --links
```

## Use it — server

```bash
python server.py
```

Then, from another terminal:

```bash
curl -X POST http://127.0.0.1:8901/open -d '{"url": "https://example.com"}'
curl -X POST http://127.0.0.1:8901/text -d '{}'
curl -X POST http://127.0.0.1:8901/screenshot -d '{"path": "shots/home.png"}'
curl -X POST http://127.0.0.1:8901/click -d '{"selector": "text=Log in"}'
curl -X POST http://127.0.0.1:8901/fill -d '{"selector": "#email", "text": "a@b.com"}'
curl -X POST http://127.0.0.1:8901/links -d '{}'
curl http://127.0.0.1:8901/
```

| Route | What it does |
|---|---|
| `GET /` | Status + current URL |
| `POST /open` | `{"url": "..."}` → `{"url", "title"}` |
| `GET /title`, `GET /url` | Title / current URL |
| `POST /text` | Visible page text |
| `POST /links` | Every link: text + address |
| `POST /click` | `{"selector": "..."}` |
| `POST /fill` | `{"selector": "...", "text": "..."}` |
| `POST /screenshot` | `{"path": "..."}` → saves a PNG |
| `POST /close` | Shuts the browser down |

## Settings (environment variables)

| Variable | Default | What it does |
|---|---|---|
| `NOBLE_SPARK_HOST` | `127.0.0.1` | Where the server listens. Local only by default. |
| `NOBLE_SPARK_PORT` | `8901` | Port. |
| `NOBLE_SPARK_KEY` | _(none)_ | If set, every request must send `X-Api-Key: <key>`. Set this before opening it to the internet. |
| `NOBLE_SPARK_SHOTS` | `shots` | Folder screenshots go in. |

## The rule

The server listens on this machine only unless you change the host.
Do not open it to the internet without setting `NOBLE_SPARK_KEY` first —
an open browser that anyone can drive is an open door.
