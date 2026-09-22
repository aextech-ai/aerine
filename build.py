#!/usr/bin/env python3
"""Aerine build step — inject the ergastorion corpus into browser.html.

Reads data/erga.json (the seed subset here; the full Box->git sync is Keel's
step-1 job) and writes it into the <script id="aerine-corpus"> data island so
browser.html is fully self-contained and works from file:// with no network fetch.

browser.html is the v1 catalogue browser (until 2026-09-22 it was index.html;
index.html is now the landing page and carries no corpus).

Usage:  python3 build.py
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent
erga = json.loads((ROOT / "data" / "erga.json").read_text())
html = (ROOT / "browser.html").read_text()

payload = json.dumps(erga, ensure_ascii=False, separators=(",", ":"))
pattern = re.compile(
    r'(<script id="aerine-corpus" type="application/json">).*?(</script>)',
    re.DOTALL,
)
if not pattern.search(html):
    sys.exit("ERROR: corpus placeholder <script id=\"aerine-corpus\"> not found in browser.html")

html2 = pattern.sub(lambda m: m.group(1) + payload + m.group(2), html, count=1)
(ROOT / "browser.html").write_text(html2)
print(f"Injected {len(erga)} erga ({len(payload)} bytes) into browser.html")
