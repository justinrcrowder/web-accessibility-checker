"""WCAG 2.1 accessibility auditor.

Python port of the Rust `wcag-audit` CLI. Fetches a webpage and checks for
common accessibility issues. The check logic mirrors the original Rust
implementation rule-for-rule.
"""

from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = "wcag-audit/1.0"
REQUEST_TIMEOUT = 15  # seconds


@dataclass
class Issue:
    rule: str
    detail: str


def audit(html: str) -> list[Issue]:
    """Run all WCAG checks against an HTML document and return found issues."""
    doc = BeautifulSoup(html, "html.parser")
    issues: list[Issue] = []

    # 1. Missing <title>
    title = doc.find("title")
    if title is None or not title.get_text().strip():
        issues.append(Issue(
            "Missing page title",
            "Add a descriptive <title> element — screen readers announce it "
            "when a page loads.",
        ))

    # 2. Missing lang attribute on <html>
    html_el = doc.find("html")
    if html_el is not None and not (html_el.get("lang") or "").strip():
        issues.append(Issue(
            "Missing lang attribute",
            'Add lang="en" (or appropriate language code) to the <html> element.',
        ))

    # 3. Images missing alt text
    missing_alt = sum(1 for img in doc.find_all("img") if img.get("alt") is None)
    if missing_alt > 0:
        issues.append(Issue(
            "Images missing alt attribute",
            f"{missing_alt} <img> element(s) have no alt attribute. "
            'Add alt="description" or alt="" for decorative images.',
        ))

    # 4. Inputs missing associated labels
    skip_types = {"hidden", "submit", "button", "reset", "image"}
    unlabelled = 0
    for inp in doc.find_all("input"):
        if (inp.get("type") or "").lower() in skip_types:
            continue
        input_id = inp.get("id") or ""
        aria_label = (inp.get("aria-label") or "").strip()
        aria_labelledby = (inp.get("aria-labelledby") or "").strip()
        has_label = bool(input_id) and doc.select_one(
            f'label[for="{input_id}"]'
        ) is not None
        if not has_label and not aria_label and not aria_labelledby:
            unlabelled += 1
    if unlabelled > 0:
        issues.append(Issue(
            "Form inputs without labels",
            f"{unlabelled} input(s) lack a <label>, aria-label, or "
            "aria-labelledby. Screen readers cannot identify unlabelled fields.",
        ))

    # 5. Links with no accessible text
    empty_links = 0
    for a in doc.find_all("a"):
        text = a.get_text().strip()
        aria = (a.get("aria-label") or "").strip()
        title_attr = (a.get("title") or "").strip()
        has_img_alt = any(
            (img.get("alt") or "").strip()
            for img in a.find_all("img")
        )
        if not text and not aria and not title_attr and not has_img_alt:
            empty_links += 1
    if empty_links > 0:
        issues.append(Issue(
            "Links with no accessible text",
            f"{empty_links} <a> element(s) have no visible text, aria-label, "
            'or title. Screen reader users will hear "link" with no context.',
        ))

    # 6. Buttons with no accessible text
    empty_buttons = 0
    for btn in doc.find_all("button"):
        text = btn.get_text().strip()
        aria = (btn.get("aria-label") or "").strip()
        if not text and not aria:
            empty_buttons += 1
    if empty_buttons > 0:
        issues.append(Issue(
            "Buttons with no accessible text",
            f"{empty_buttons} <button> element(s) have no text or aria-label.",
        ))

    # 7. Skipped heading levels
    levels = [
        int(h.name[1])
        for h in doc.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    ]
    skips = [
        f"h{a} → h{b}"
        for a, b in zip(levels, levels[1:])
        if b > a + 1
    ]
    if skips:
        issues.append(Issue(
            "Skipped heading levels",
            f"Heading hierarchy jumps: {', '.join(skips)}. Skipping levels "
            "confuses screen reader navigation.",
        ))

    # 8. Multiple <h1> elements
    h1_count = len(doc.find_all("h1"))
    if h1_count > 1:
        issues.append(Issue(
            "Multiple <h1> elements",
            f"Found {h1_count} <h1> elements. Each page should have exactly "
            "one <h1> to clearly identify the main topic.",
        ))

    return issues


@dataclass
class AuditResult:
    url: str
    ok: bool                 # whether the page was fetched successfully
    issues: list[Issue]
    error: str | None = None


def audit_url(url: str, session: requests.Session | None = None) -> AuditResult:
    """Fetch a URL and audit it. Captures fetch errors instead of raising."""
    sess = session or requests.Session()
    try:
        resp = sess.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return AuditResult(url=url, ok=False, issues=[], error=str(e))

    return AuditResult(url=url, ok=True, issues=audit(resp.text))
