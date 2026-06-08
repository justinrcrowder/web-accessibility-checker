# web-accessibility-checker

A Flask web app that checks webpages for common accessibility issues based on
WCAG 2.1 guidelines. This is a Python/web reimplementation of the original Rust
`wcag-audit` CLI.

## What it checks

- Missing page title
- Missing language declaration (`lang` on `<html>`)
- Images without `alt` text
- Form inputs without labels
- Links and buttons with no readable text
- Skipped heading levels
- Multiple `<h1>` elements

## Running it

You need Python 3.10+.

```
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000, paste one or more URLs (one per line), and
click **Audit pages**.

## Demo site

A bundled demo site is served at http://localhost:5000/demo/. It has six pages —
one that passes all checks, and five that each demonstrate a different category
of issue. The home page lists the demo URLs you can paste into the auditor.

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | Flask routes (form, results, demo site) |
| `auditor.py` | The WCAG checks — fetches a URL and returns a list of issues |
| `templates/` | Jinja2 templates (`base`, `index`, `results`) |
| `static/style.css` | Styling |
| `demo-site/` | Bundled demo pages |
