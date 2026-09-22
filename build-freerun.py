#!/usr/bin/env python3
"""Aerine free-run build step — inject the prepared runs into free-run.html.

Reads every fixtures/*.json and writes them into the <script id="aerine-freerun">
data island, so free-run.html is fully self-contained and opens from file:// with
no server and no fetch. Same pattern as build.py, deliberately.

Runs are ordered by runs_lib.RUN_ORDER, not by filename, so the picker reads in
a sensible sequence. A fixture not named there is appended after, by filename.

The release gate and the fixture loading live in runs_lib.py, shared with
build-krites.py — two surfaces, one gate.

Usage:  python3 build-freerun.py
        python3 build-freerun.py --fixtures <dir> --out <path>   # local verification
"""
import pathlib

import runs_lib

ROOT = pathlib.Path(__file__).parent

FIX = pathlib.Path(runs_lib.arg("--fixtures") or (ROOT / "fixtures")).resolve()
OUT = pathlib.Path(runs_lib.arg("--out") or (ROOT / "free-run.html")).resolve()

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

if not IN_REPO:
    print("LOCAL VERIFICATION BUILD -- release gate not applied.")
    print(f"  fixtures: {FIX}")
    print(f"  out:      {OUT}")
    print("  The output is outside this repository, so nothing here can leak into it.")

frame = runs_lib.load_frame(ROOT)

size = runs_lib.inject(ROOT / "free-run.html", OUT, "aerine-freerun", runs)
frame_size = runs_lib.inject(OUT, OUT, "aerine-frame", frame)

print(f"Injected {len(runs)} runs ({size} bytes) into {OUT.name}")
print(f"Injected the answer frame ({frame_size} bytes) into {OUT.name}")
print("  order: " + ", ".join(r["name"] for r in runs))
for r in runs:
    meta = r.get("_fixture") or {}
    if meta.get("release") is True:
        print(f"  released: {r['name']} — {meta.get('release_ruling')}")

if demo_count:
    print(f"  NOTE: {demo_count} of {len(runs)} runs carry _demo:true — the page will "
          f"show the demonstration banner for those. Real engine fixtures must not "
          f"carry that flag.")
