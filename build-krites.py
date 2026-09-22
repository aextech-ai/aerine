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

# The release gate exists to stop unreleased canon landing in a PUBLIC repo, so
# the question it turns on is ONE question: does this build WRITE INTO THE REPO?
# A build whose output lands outside the tree cannot leak into it, whatever it
# reads -- that is the local-verification case the brief asked for, and it stays
# allowed and loud. A build whose output lands INSIDE the tree is gated, even
# when its fixtures came from somewhere else.
#
# It used to read `OUT.is_relative_to(ROOT) and FIX.is_relative_to(ROOT)`, which
# left the one combination that actually leaks wide open: outside fixtures
# written to an in-repo page skipped the gate AND printed "Nothing is written
# into the repository" while writing into it. Found 2026-09-22 (job 4364393e) by
# constructing the violation and watching it NOT refuse. A gate you have not
# seen fire is a gate you are asserting; this one fired for the wrong input.
IN_REPO = OUT.is_relative_to(ROOT)

runs, demo_count = runs_lib.load_runs(ROOT, FIX, apply_gate=IN_REPO)
published = json.loads((ROOT / "data" / "erga.json").read_text())

if not IN_REPO:
    print("LOCAL VERIFICATION BUILD -- release gate not applied.")
    print(f"  fixtures: {FIX}")
    print(f"  out:      {OUT}")
    print("  The output is outside this repository, so nothing here can leak into it.")

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
