#!/usr/bin/env python3
"""Aerine free-run build step — inject the prepared runs into free-run.html.

Reads every fixtures/*.json and writes them into the <script id="aerine-freerun">
data island, so free-run.html is fully self-contained and opens from file:// with
no server and no fetch. Same pattern as build.py, deliberately.

Runs are ordered by RUN_ORDER below, not by filename, so the picker reads in a
sensible sequence. A fixture not named there is appended after, by filename.

Usage:  python3 build-freerun.py
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent
FIX = ROOT / "fixtures"

RUN_ORDER = [
    "consumer-ibsd",
    "consumer-fibre",
    "device-gas",
    "agent-relay",
    "unresolved-params",
]

REQUIRED_PAYLOAD_KEYS = [
    "entry", "coverage", "weakest", "returned", "absent", "unresolved", "notes",
]


def check_release_boundary(name, fx, public):
    """aextech-ai/aerine is PUBLIC. aerine-ergastorion is not.

    A fixture may only carry canon text that is already published in
    data/erga.json on main -- unless it is explicitly marked release-safe by
    whoever owns the canon. This is a build failure rather than a review
    checklist item on purpose: a canon leak into a public repo is not fixable
    after the fact, so the boundary is held by the tool, not by remembering.

    To admit an ergon that is not in data/erga.json, the fixture must carry:
        "_release_safe": true
    and that flag is a claim by the canon owner, not by whoever runs the build.
    """
    if fx.get("_release_safe") is True:
        return []
    problems = []
    for bucket in ("entry", "returned"):
        for n in fx["payload"].get(bucket) or []:
            eid = n.get("ergon_id")
            src = public.get(eid)
            if src is None:
                problems.append(f"{eid} is not published in data/erga.json")
                continue
            for field, pub_field in (("assertion", "assertion"), ("grade", "confidence"), ("desk", "desk")):
                if n.get(field) != src.get(pub_field):
                    problems.append(f"{eid}: {field} does not match data/erga.json")
    return problems

files = {p.stem: p for p in sorted(FIX.glob("*.json"))}
if not files:
    sys.exit("ERROR: no fixtures found in fixtures/")

ordered = [n for n in RUN_ORDER if n in files]
ordered += [n for n in sorted(files) if n not in RUN_ORDER]

public = {e["ergon_id"]: e for e in json.loads((ROOT / "data" / "erga.json").read_text())}

runs, demo_count, leaks = [], 0, []
for name in ordered:
    fx = json.loads(files[name].read_text())
    payload = fx.get("payload")
    if not isinstance(payload, dict):
        sys.exit(f"ERROR: {name}.json has no payload object")
    missing = [k for k in REQUIRED_PAYLOAD_KEYS if k not in payload]
    if missing:
        sys.exit(f"ERROR: {name}.json payload is missing {', '.join(missing)}")
    fx.setdefault("name", name)
    for problem in check_release_boundary(name, fx, public):
        leaks.append(f"  {name}.json: {problem}")
    if fx.get("_demo"):
        demo_count += 1
    runs.append(fx)

if leaks:
    sys.exit(
        "REFUSING TO BUILD -- unreleased canon in a public repository.\n"
        + "\n".join(leaks)
        + "\n\naextech-ai/aerine is public. Every ergon in a fixture must already be in\n"
          "data/erga.json on main, or the fixture must be marked \"_release_safe\": true\n"
          "by the canon owner. If you are unsure whether something may be committed\n"
          "here, it may not."
    )

html = (ROOT / "free-run.html").read_text()
pattern = re.compile(
    r'(<script id="aerine-freerun" type="application/json">).*?(</script>)',
    re.DOTALL,
)
if not pattern.search(html):
    sys.exit('ERROR: run placeholder <script id="aerine-freerun"> not found in free-run.html')

payload_json = json.dumps(runs, ensure_ascii=False, separators=(",", ":"))
html2 = pattern.sub(lambda m: m.group(1) + payload_json + m.group(2), html, count=1)
(ROOT / "free-run.html").write_text(html2)

print(f"Injected {len(runs)} runs ({len(payload_json)} bytes) into free-run.html")
print("  order: " + ", ".join(r["name"] for r in runs))
if demo_count:
    print(f"  NOTE: {demo_count} of {len(runs)} runs carry _demo:true — the page will "
          f"show the demonstration banner for those. Real engine fixtures must not "
          f"carry that flag.")
