#!/usr/bin/env python3
"""Aerine build step — inject the ergastorion corpus into index.html.

Reads data/erga.json (the seed subset here; the full Box->git sync is Keel's
step-1 job) and writes it into the <script id="aerine-corpus"> data island so
index.html is fully self-contained and works from file:// with no network fetch.

Usage:  python3 build.py
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent
erga = json.loads((ROOT / "data" / "erga.json").read_text())
html = (ROOT / "index.html").read_text()

payload = json.dumps(erga, ensure_ascii=False, separators=(",", ":"))
pattern = re.compile(
    r'(<script id="aerine-corpus" type="application/json">).*?(</script>)',
    re.DOTALL,
)
if not pattern.search(html):
    sys.exit("ERROR: corpus placeholder <script id=\"aerine-corpus\"> not found in index.html")

html2 = pattern.sub(lambda m: m.group(1) + payload + m.group(2), html, count=1)
(ROOT / "index.html").write_text(html2)
print(f"Injected {len(erga)} erga ({len(payload)} bytes) into index.html")
