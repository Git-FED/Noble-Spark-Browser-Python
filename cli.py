"""Noble Spark CLI — one-shot browser jobs from the command line.

Examples:
  python3 cli.py open https://example.com --text
  python3 cli.py open https://example.com --shot shots/home.png
  python3 cli.py open https://example.com --links
"""

import argparse
import json
import sys

from browser import NobleSparkBrowser


def main():
    parser = argparse.ArgumentParser(description="Noble Spark — headless browser for Muse")
    parser.add_argument("command", choices=["open"], help="what to do")
    parser.add_argument("url", help="page to open")
    parser.add_argument("--text", action="store_true", help="print the page text")
    parser.add_argument("--links", action="store_true", help="print the page links as JSON")
    parser.add_argument("--shot", metavar="PATH", help="save a PNG screenshot here")
    parser.add_argument("--headed", action="store_true", help="show a real window (needs a screen)")
    args = parser.parse_args()

    browser = NobleSparkBrowser(headless=not args.headed)
    try:
        result = browser.open(args.url)
        print("URL:   %s" % result["url"])
        print("Title: %s" % result["title"])
        if args.text:
            print("--- text ---")
            print(browser.text())
        if args.links:
            print("--- links ---")
            print(json.dumps(browser.links(), indent=2))
        if args.shot:
            print("Shot:  %s" % browser.screenshot(args.shot))
    finally:
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
