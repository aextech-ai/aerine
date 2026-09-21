#!/usr/bin/env python3
"""Aerine free-run build step — inject the prepared runs into free-run.html.

Reads every fixtures/*.json and writes them into the <script id="aerine-freerun">
data island, so free-run.html is fully self-contained and opens from file:// with
no server and no fetch. Same pattern as build.py, deliberately.

Runs are ordered by RUN_ORDER below, not by filename, so the picker reads in a
sensible sequence. A fixture not named there is appended after, by filename.

Usage:  python3 build-freerun.py
        python3 build-freerun.py --fixtures <dir> --out <path>   # local verification
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent


def _arg(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        sys.exit(f"ERROR: {flag} needs a value")
    return None


FIX = pathlib.Path(_arg("--fixtures") or (ROOT / "fixtures")).resolve()
OUT = pathlib.Path(_arg("--out") or (ROOT / "free-run.html")).resolve()

# The release gate exists to stop unreleased canon landing in a PUBLIC repo. A
# build that writes nothing into this repo, from fixtures that are not in it,
# cannot do that -- so it is allowed, loudly, and it does not touch the
# committed page. Verifying against real fixtures is exactly what the brief
# asks for; committing them before they are marked is what it forbids.
IN_REPO = OUT.is_relative_to(ROOT) and FIX.is_relative_to(ROOT)

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

    To admit an ergon that is not in data/erga.json, the fixture must carry the
    canon owner's own release marker, inside its `_fixture` block:

        "release": true,
        "release_ruling": "D-17 (founder, 2026-09-21)"

    BOTH are required. A bare boolean is a flag anybody could set; the ruling is
    the provenance, and a release with no ruling behind it is not a release.
    This marker is written by whoever owns the canon. It is not ours to set, and
    setting it here to unblock a build would defeat the only thing this function
    does.
    """
    meta = fx.get("_fixture") or {}
    if meta.get("release") is True and str(meta.get("release_ruling") or "").strip():
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

LABELS = {
    "consumer-ibsd": "SIBO, diarrhoea, gas",
    "consumer-fibre": "Fibre and whole grains",
    "device-gas": "Breath gas",
    "agent-relay": "Agent relay (structured)",
    "unresolved-params": "Nothing located",
}


def normalise(name, fx):
    """Accept the engine's own fixture shape as well as this repo's wrapper.

    engine/fixtures/free-run-<slug>.json puts the payload at the TOP LEVEL
    alongside a `_fixture` block (slug, line, params, k, digests). This repo's
    demo files nest it under `payload` with the params beside it, because the
    params are the form's, not the engine's. Normalise to the wrapper so the
    page reads one shape and the swap is a data change.
    """
    if "_fixture" not in fx:
        return fx
    meta = fx["_fixture"]
    slug = meta.get("slug") or name.replace("free-run-", "")
    payload = {k: v for k, v in fx.items() if k != "_fixture"}
    return {
        "name": slug,
        "label": LABELS.get(slug, slug),
        "lede": meta.get("line", ""),
        "params": meta.get("params", []),
        "_fixture": meta,
        "_demo": fx.get("_demo", False),
        "payload": payload,
    }


files = {p.stem.replace("free-run-", ""): p for p in sorted(FIX.glob("*.json"))}
if not files:
    sys.exit("ERROR: no fixtures found in fixtures/")

ordered = [n for n in RUN_ORDER if n in files]
ordered += [n for n in sorted(files) if n not in RUN_ORDER]

public = {e["ergon_id"]: e for e in json.loads((ROOT / "data" / "erga.json").read_text())}

runs, demo_count, leaks = [], 0, []
for name in ordered:
    fx = normalise(name, json.loads(files[name].read_text()))
    payload = fx.get("payload")
    if not isinstance(payload, dict):
        sys.exit(f"ERROR: {name}.json has no payload object")
    missing = [k for k in REQUIRED_PAYLOAD_KEYS if k not in payload]
    if missing:
        sys.exit(f"ERROR: {name}.json payload is missing {', '.join(missing)}")
    fx.setdefault("name", name)
    if IN_REPO:
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
          "data/erga.json on main, or the fixture's _fixture block must carry BOTH\n"
          "  \"release\": true\n"
          "  \"release_ruling\": \"<the ruling that released it>\"\n"
          "written by the canon owner. If you are unsure whether something may be\n"
          "committed here, it may not."
    )

if not IN_REPO:
    print("LOCAL VERIFICATION BUILD -- release gate not applied.")
    print(f"  fixtures: {FIX}")
    print(f"  out:      {OUT}")
    print("  Nothing is written into the repository. Do not commit this output.")

html = (ROOT / "free-run.html").read_text()
pattern = re.compile(
    r'(<script id="aerine-freerun" type="application/json">).*?(</script>)',
    re.DOTALL,
)
if not pattern.search(html):
    sys.exit('ERROR: run placeholder <script id="aerine-freerun"> not found in free-run.html')

payload_json = json.dumps(runs, ensure_ascii=False, separators=(",", ":"))
html2 = pattern.sub(lambda m: m.group(1) + payload_json + m.group(2), html, count=1)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html2)

print(f"Injected {len(runs)} runs ({len(payload_json)} bytes) into {OUT.name}")
print("  order: " + ", ".join(r["name"] for r in runs))
for r in runs:
    meta = r.get("_fixture") or {}
    if meta.get("release") is True:
        print(f"  released: {r['name']} — {meta.get('release_ruling')}")

if demo_count:
    print(f"  NOTE: {demo_count} of {len(runs)} runs carry _demo:true — the page will "
          f"show the demonstration banner for those. Real engine fixtures must not "
          f"carry that flag.")
