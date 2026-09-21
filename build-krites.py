#!/usr/bin/env python3
"""Aerine Krites-read build step — inject the prepared runs into krites.html.

Same runs as build-freerun.py, same gate (runs_lib.py), one extra island: the
PUBLISHED erga from data/erga.json. krites.html renders a claim's full record --
provenance, DOI, verbatim source passage, integrity flags -- for every ergon
this repository actually publishes, and says plainly that the record is not
published here for the ones it does not. A claim that cannot be opened must not
look like a claim nobody wanted to open.

Both islands are data islands for the same reason as build.py: the page is
self-contained and opens from file:// with no server and no fetch.

Usage:  python3 build-krites.py
        python3 build-krites.py --fixtures <dir> --out <path>   # local verification
"""
import json
import pathlib

import runs_lib

ROOT = pathlib.Path(__file__).parent

FIX = pathlib.Path(runs_lib.arg("--fixtures") or (ROOT / "fixtures")).resolve()
OUT = pathlib.Path(runs_lib.arg("--out") or (ROOT / "krites.html")).resolve()

IN_REPO = OUT.is_relative_to(ROOT) and FIX.is_relative_to(ROOT)

runs, demo_count = runs_lib.load_runs(ROOT, FIX, apply_gate=IN_REPO)
published = json.loads((ROOT / "data" / "erga.json").read_text())

if not IN_REPO:
    print("LOCAL VERIFICATION BUILD -- release gate not applied.")
    print(f"  fixtures: {FIX}")
    print(f"  out:      {OUT}")
    print("  Nothing is written into the repository. Do not commit this output.")

runs_size = runs_lib.inject(ROOT / "krites.html", OUT, "aerine-freerun", runs)
corpus_size = runs_lib.inject(OUT, OUT, "aerine-corpus", published)

print(f"Injected {len(runs)} runs ({runs_size} bytes) into {OUT.name}")
print(f"Injected {len(published)} published erga ({corpus_size} bytes) into {OUT.name}")
print("  order: " + ", ".join(r["name"] for r in runs))
for r in runs:
    meta = r.get("_fixture") or {}
    if meta.get("release") is True:
        print(f"  released: {r['name']} — {meta.get('release_ruling')}")

if demo_count:
    print(f"  NOTE: {demo_count} of {len(runs)} runs carry _demo:true — the page will "
          f"show the demonstration banner for those. Real engine fixtures must not "
          f"carry that flag.")
