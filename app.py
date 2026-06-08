"""Flask web app for the WCAG 2.1 accessibility auditor.

Enter one or more URLs and get a report of common accessibility issues for
each page. A small demo site is bundled under /demo so you can try it without
needing a live external site.
"""

from urllib.parse import urlparse

import requests
from flask import Flask, render_template, request, send_from_directory

from auditor import AuditResult, audit_url

app = Flask(__name__)

MAX_URLS = 20  # guard against someone pasting a huge list

DEMO_PAGES = [
    "index.html",
    "missing-meta.html",
    "images.html",
    "forms.html",
    "links-buttons.html",
    "headings.html",
]


def demo_urls() -> list[str]:
    """Absolute URLs to the bundled demo pages, based on the current host.

    Works in any environment (localhost, *.workers.dev, custom domain) instead
    of hardcoding a port.
    """
    base = request.host_url.rstrip("/")
    return [f"{base}/demo/{page}" for page in DEMO_PAGES]


def parse_urls(raw: str) -> list[str]:
    """Split textarea input into clean URLs, one per line.

    Skips blanks and lines starting with '#' (matching the CLI's --file format),
    deduplicates while preserving order, and adds a default https:// scheme.
    """
    urls: list[str] = []
    seen = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not urlparse(line).scheme:
            line = "https://" + line
        if line not in seen:
            seen.add(line)
            urls.append(line)
    return urls


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", demo_urls=demo_urls())

    raw = request.form.get("urls", "")
    urls = parse_urls(raw)[:MAX_URLS]

    if not urls:
        return render_template(
            "index.html",
            raw=raw,
            error="Please enter at least one URL.",
            demo_urls=demo_urls(),
        )

    session = requests.Session()
    results: list[AuditResult] = [audit_url(u, session) for u in urls]

    passed = sum(1 for r in results if r.ok and not r.issues)
    failed = sum(1 for r in results if r.ok and r.issues)
    errored = sum(1 for r in results if not r.ok)

    return render_template(
        "results.html",
        raw=raw,
        results=results,
        total=len(results),
        passed=passed,
        failed=failed,
        errored=errored,
    )


@app.route("/demo/")
@app.route("/demo/<path:filename>")
def demo(filename: str = "index.html"):
    """Serve the bundled demo site so users can audit it locally."""
    return send_from_directory("demo-site", filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
