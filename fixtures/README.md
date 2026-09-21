# Free-run fixtures

Each file in this directory is **one prepared run** for `free-run.html`.

## Shape

```jsonc
{
  "name":   "consumer-ibsd",        // fixture id, matches the run picker
  "label":  "…",                    // human label for the picker
  "lede":   "…",                    // one line of context for the run
  "params": ["…", "…"],             // what the user typed. NOT part of the engine
                                    //   contract — the form holds this, the
                                    //   engine receives it.
  "payload": { … }                  // EXACTLY the engine contract, untouched
}
```

`payload` is the return value of Keel's `freeRun(params, index, {k})`:

```
entry:      [{ergon_id, desk, assertion, grade}]
coverage:   {symptom, biology, nutrition, mechanism, measurement}
weakest:    ["measurement", "nutrition"]
returned:   [{ergon_id, desk, assertion, grade, edge_weight, via: [ergon_id…]}]
absent:     [{desk, reason}]
unresolved: ["<param>"]
notes:      []
```

The surface renders `payload` and computes nothing from it. Array order is
render order; no sorting, no scoring, no derived counts.

## Provenance of the files currently here

**These are real engine output**, copied unmodified from
`aextech-ai/aerine-ergastorion`, branch `claude/aerine-engine-free-run`,
commit `b328958`. Each one's `_fixture` block says which engine run cut it and
against which corpus:

```jsonc
"generated_by": "engine/build-fixtures.mjs",
"index_content_digest": "sha256:…",   // the index it was cut against
"source_digest": "sha256:…",          // the corpus behind that index
"release": true,
"release_ruling": "D-17 (founder, 2026-09-21)"
```

So an `absent[]` reason in these files is a statement about **the canon**, not
about a subset — which is what makes it a finding rather than an artefact of a
thin demo. The page shows the run's digests in its footer colophon.

An earlier cut of this directory held five **hand-built demonstration
payloads** drawn only from the 8 erga in `data/erga.json`, each carrying
`"_demo": true`. They were correct and honest for building against before the
engine fixtures existed, and they are superseded. **The `_demo` machinery
stays**: any payload that is not engine output must carry that flag, and the
page renders a banner saying so.

Never let a reader have to guess which kind of payload they are looking at.
A released fixture carries its ruling; a hand-built one carries `_demo`.

## Updating the fixtures

Copy the engine's files in and rebuild:

```
cp …/aerine-ergastorion/engine/fixtures/free-run-*.json fixtures/
python3 build-freerun.py
```

The build reads the engine's own shape (payload at top level beside a
`_fixture` block) and normalises it, so this is a data change and not a code
change.

## The release boundary is enforced by the build, not by review

`aextech-ai/aerine` is public. `aerine-ergastorion` is not.

`build-freerun.py` **refuses to build** if any ergon in any fixture is not
already published in `data/erga.json` on `main` — id, assertion, grade and desk
all compared. A fixture carrying canon this repository has not published stops
the build with exit 1 and names the ergon.

To admit an ergon that is not in `data/erga.json`, the fixture's `_fixture`
block must carry **both**:

```json
"release": true,
"release_ruling": "D-17 (founder, 2026-09-21)"
```

Both, because a bare boolean is a flag anybody could set and the ruling is the
provenance — a release with nothing behind it is not a release.

That marker is **written by whoever owns the canon**, not by whoever runs the
build. Do not add it to get a build to pass.

The check is a build failure rather than a checklist item on purpose: a thin
demo is fixable afterwards, and a canon leak into a public repository is not.
