"""Noble Spark — a headless Chromium browser for Muse.

Python + Playwright. One browser, kept alive, driven by code:
open a page, read its text, click, fill forms, take screenshots.

This is the engine, not a window. No screen, no buttons to stare at.
Muse drives it through server.py (HTTP) or cli.py (command line).
"""

import os
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _proxy_from_env():
    """Pick up the machine's proxy (HTTPS_PROXY etc.) if one is set.

    Returns (proxy_dict_or_None, behind_proxy_bool). The proxy value is
    read from the environment at launch time — never stored in this repo.
    A proxy that intercepts TLS (most egress proxies) also needs
    ignore_https_errors on the browser context, so that goes on too.
    """
    raw = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    if not raw:
        return None, False
    parsed = urlparse(raw)
    server = "%s://%s:%s" % (
        parsed.scheme or "http",
        parsed.hostname,
        parsed.port or 3128,
    )
    proxy = {"server": server}
    if parsed.username:
        proxy["username"] = parsed.username
    if parsed.password:
        proxy["password"] = parsed.password
    return proxy, True


class NobleSparkBrowser:
    """One Chromium browser that stays open until you close it."""

    def __init__(self, headless=True, user_agent=DEFAULT_USER_AGENT):
        self._pw = sync_playwright().start()
        proxy, behind_proxy = _proxy_from_env()
        launch_kwargs = {"headless": headless, "args": ["--no-sandbox"]}
        if proxy:
            launch_kwargs["proxy"] = proxy
        self.browser = self._pw.chromium.launch(**launch_kwargs)
        self.context = self.browser.new_context(
            user_agent=user_agent,
            ignore_https_errors=behind_proxy,
        )
        self.page = self.context.new_page()
        self.current_url = None

    def open(self, url, wait_until="domcontentloaded", timeout=30000):
        """Go to a URL. Returns the real URL landed on and the page title."""
        self.page.goto(url, wait_until=wait_until, timeout=timeout)
        self.current_url = self.page.url
        return {"url": self.page.url, "title": self.page.title()}

    def title(self):
        return self.page.title()

    def url(self):
        return self.page.url

    def text(self):
        """Visible text of the page body, as a reader would see it."""
        return self.page.inner_text("body")

    def html(self):
        return self.page.content()

    def screenshot(self, path):
        """Save a PNG screenshot of the current view. Returns the path."""
        self.page.screenshot(path=path, full_page=False)
        return path

    def click(self, selector, timeout=10000):
        self.page.click(selector, timeout=timeout)
        return {"clicked": selector, "url": self.page.url}

    def fill(self, selector, text, timeout=10000):
        self.page.fill(selector, text, timeout=timeout)
        return {"filled": selector}

    def links(self, limit=200):
        """Every link on the page: text + address."""
        return self.page.eval_on_selector_all(
            "a[href]",
            """els => els
                .map(e => ({text: (e.innerText || '').trim().slice(0, 120),
                            href: e.href}))
                .filter(l => l.href)
                .slice(0, %d)"""
            % limit,
        )

    def close(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()
