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

Since 2026-09-22 (job 4364393e, D-39 item 2) it also attaches each run's
natural-language QUESTION from questions.json. That is here for the same reason
the gate is: the question a run answers must read identically on both surfaces,
and a copy in each build script is a copy that will drift.
"""
import json
import pathlib
import sys

QUESTIONS_FILE = "questions.json"

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
    "consumer-ibsd": "SIBO, diarrhea, gas",
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


def read_questions(root):
    path = pathlib.Path(root) / QUESTIONS_FILE
    if not path.exists():
        sys.exit(f"ERROR: {QUESTIONS_FILE} not found at {path}")
    return json.loads(path.read_text())


def load_frame(root):
    """The four-move answer frame -- section leads and transitions (D-39 item 4).

    Authored copy, not markup: it lives beside the questions because copy that
    lives only in an Office document has to be hand-transcribed into HTML, and
    hand-transcribed copy drifts from its source silently.

    Underscore-prefixed keys are NOT returned. They are the author's notes and
    the deliberately withheld block (`_withheld_until_intake_exists`, which
    offers a capability this surface does not have and whose own key says not to
    render it until it does). Stripping them here rather than in the renderer is
    the point: a surface that filters on a prefix at paint time is one refactor
    away from painting them, and the withheld block is the single string on this
    page that must never reach a reader by accident.
    """
    frame = read_questions(root).get("frame")
    if frame is None:
        return None

    def strip(node):
        if isinstance(node, dict):
            return {k: strip(v) for k, v in node.items() if not k.startswith("_")}
        return node

    return strip(frame)


def check_parses_to(slug, q, fixture_params):
    """`parses_to` must equal the fixture's `_fixture.params`, IN ORDER.

    Logothetes' check, made a build refusal (his `_the_check_a_build_should_run`,
    Ponder's ask). That equality is the whole claim the surface makes when it
    prints a question above the chips: the chips below the question are asserted
    to be what the question resolved to. If it ever stops holding, the page is
    showing a reader a question that is not what the run was asked -- silently,
    and on a health surface.

    A run carrying no `parses_to` is not an error; the check is on runs that
    make the claim. Order matters because the chips render in payload order, so
    the same set in a different order is a different rendered sentence.

    NEVER reconcile by editing `parses_to`. The fixture is the engine's record
    of what it was given; the question is written to match it, not the reverse.
    """
    pt = q.get("parses_to")
    if pt is None:
        return []
    if list(pt) != list(fixture_params):
        return [
            f"{slug}: parses_to does not equal the fixture's params\n"
            f"    questions.json parses_to : {pt}\n"
            f"    _fixture.params          : {list(fixture_params)}"
        ]
    return []


def load_questions(root, slugs):
    """Read questions.json and return {slug: {question|pending, attribution}}.

    The question is the surface's, not the engine's -- a fixture records what
    freeRun() was given, and a person does not speak in seeds. So it lives in
    its own file at the repo root, beside the build scripts that render it,
    rather than inside fixtures/ where an engine regeneration would own it.

    Two things are refusals rather than warnings:

      - a slug in questions.json with no fixture behind it. A question keyed to
        a run that does not exist renders nowhere, and a silently-never-rendered
        string is exactly the failure a typo produces. The build says so.
      - a `question` that is present but empty. An empty question would render
        as a blank quote above the seeds and read as though the run were asked
        nothing at all.

    A fixture with NO entry here is not an error: it renders the pending line.
    That is the whole point -- the five questions are being written by another
    seat, and this surface must show a run without one rather than invent it.
    """
    doc = read_questions(root)
    runs = doc.get("runs")
    if not isinstance(runs, dict):
        sys.exit(f"ERROR: {QUESTIONS_FILE} has no `runs` object")

    orphans = [s for s in runs if s not in slugs]
    if orphans:
        sys.exit(
            f"ERROR: {QUESTIONS_FILE} names run(s) with no fixture: "
            + ", ".join(sorted(orphans))
            + f"\n  fixtures present: {', '.join(sorted(slugs))}\n"
            "  A question keyed to a run that does not exist renders nowhere."
        )
    for slug, q in runs.items():
        if "question" in q and not str(q["question"]).strip():
            sys.exit(f"ERROR: {QUESTIONS_FILE}: {slug} has an empty `question`")
    return runs


DEFAULT_PENDING = (
    "The question for this run has not been written yet. What the run was "
    "given is below; this page does not invent the question that would have "
    "produced it."
)


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
    questions = load_questions(root, set(files))

    runs, demo_count, leaks, mismatches = [], 0, [], []
    for name in ordered:
        fx = normalise(name, json.loads(files[name].read_text()))
        fx["question"] = questions.get(name) or {"pending": DEFAULT_PENDING}
        payload = fx.get("payload")
        if not isinstance(payload, dict):
            sys.exit(f"ERROR: {name}.json has no payload object")
        missing = [k for k in REQUIRED_PAYLOAD_KEYS if k not in payload]
        if missing:
            sys.exit(f"ERROR: {name}.json payload is missing {', '.join(missing)}")
        fx.setdefault("name", name)
        mismatches += check_parses_to(name, fx["question"], (fx.get("_fixture") or {}).get("params") or [])
        if apply_gate:
            for problem in check_release_boundary(name, fx, public):
                leaks.append(f"  {name}.json: {problem}")
        if fx.get("_demo"):
            demo_count += 1
        runs.append(fx)

    if mismatches:
        sys.exit(
            "REFUSING TO BUILD -- a question does not match what its run was asked.\n  "
            + "\n  ".join(mismatches)
            + "\n\nThe chips under a question are asserted to be what that question resolved\n"
              "to. Fix the question or the fixture -- never `parses_to`, which is only a\n"
              "copy of the engine's own record of the run's params."
        )

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
