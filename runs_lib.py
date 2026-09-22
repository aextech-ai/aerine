#!/usr/bin/env python3
"""Shared loader for the prepared runs — the release gate lives here, once.

Two surfaces render the same prepared runs:

    free-run.html   the full read (entry, coverage, returned, absent) — dense
    krites.html     Aerine's read of that same run — what we know, where it
                    thins, what we know there, worth a look

They must never disagree about which runs exist or about what a run may carry
into a PUBLIC repository, so the fixture loading and the release gate are in
this module rather than copied into each build script. A security gate that
exists in two places is a gate that will be half-updated.

Extracted from build-freerun.py 2026-09-21 (job 3d97c936) with the gate
unchanged; build-freerun.py's behaviour and CLI are the same as before.
"""
import json
import pathlib
import sys

REQUIRED_PAYLOAD_KEYS = [
    "entry", "coverage", "weakest", "returned", "absent", "unresolved", "notes",
]

RUN_ORDER = [
    "consumer-ibsd",
    "consumer-fibre",
    "device-gas",
    "agent-relay",
    "unresolved-params",
]

LABELS = {
    "consumer-ibsd": "SIBO, diarrhoea, gas",
    "consumer-fibre": "Fibre and whole grains",
    "device-gas": "Breath gas",
    "agent-relay": "Agent relay (structured)",
    "unresolved-params": "Nothing located",
}


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


def load_runs(root, fixtures_dir, apply_gate):
    """Read, order, validate and gate every fixture. Exits the process on a
    malformed fixture or a release-boundary violation -- both are build
    failures, not warnings.

    Returns (runs, demo_count).
    """
    root = pathlib.Path(root)
    fixtures_dir = pathlib.Path(fixtures_dir)
    files = {p.stem.replace("free-run-", ""): p for p in sorted(fixtures_dir.glob("*.json"))}
    if not files:
        sys.exit(f"ERROR: no fixtures found in {fixtures_dir}")

    ordered = [n for n in RUN_ORDER if n in files]
    ordered += [n for n in sorted(files) if n not in RUN_ORDER]

    public = {e["ergon_id"]: e for e in json.loads((root / "data" / "erga.json").read_text())}

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
        if apply_gate:
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

    return runs, demo_count


def inject(html_path, out_path, island_id, payload_obj):
    """Replace the contents of a <script id="..."> JSON data island in place."""
    import re
    html_path = pathlib.Path(html_path)
    out_path = pathlib.Path(out_path)
    html = html_path.read_text()
    pattern = re.compile(
        r'(<script id="' + re.escape(island_id) + r'" type="application/json">).*?(</script>)',
        re.DOTALL,
    )
    if not pattern.search(html):
        sys.exit(f'ERROR: data island <script id="{island_id}"> not found in {html_path.name}')
    blob = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(pattern.sub(lambda m: m.group(1) + blob + m.group(2), html, count=1))
    return len(blob)


def arg(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        sys.exit(f"ERROR: {flag} needs a value")
    return None
