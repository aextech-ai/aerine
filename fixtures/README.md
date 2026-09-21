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

**Every file in this directory carries `"_demo": true`. They are hand-built
demonstration payloads. They are NOT engine output.**

They exist so the surface could be built and verified before Keel's engine
fixtures landed. They are drawn **only** from the 8 erga already public in
`data/erga.json` on `main` — nothing from the private `aerine-ergastorion`
canon is in this tree.

Consequence, stated plainly because it changes how the page must be read:
an `absent[]` reason in these files is a statement about **the 8-ergon public
subset**, not about the 171-ergon canon. The page renders a persistent banner
saying so for any payload marked `_demo`.

## Replacing these with real engine fixtures

Drop Keel's five files in, keeping the filenames:

```
consumer-fibre.json  consumer-ibsd.json  agent-relay.json
device-gas.json      unresolved-params.json
```

Remove `"_demo": true` from any file that is genuine engine output — the
banner is keyed on that flag alone, so a real fixture that still carries it
will be under-claimed, and a demo file that loses it will be over-claimed.

Then re-run the build so the data island matches the files:

```
python3 build-freerun.py
```

## The release boundary is enforced by the build, not by review

`aextech-ai/aerine` is public. `aerine-ergastorion` is not.

`build-freerun.py` **refuses to build** if any ergon in any fixture is not
already published in `data/erga.json` on `main` — id, assertion, grade and desk
all compared. A fixture carrying canon this repository has not published stops
the build with exit 1 and names the ergon.

To admit an ergon that is not in `data/erga.json`, the fixture must carry:

```json
"_release_safe": true
```

That flag is **a claim by whoever owns the canon**, not by whoever runs the
build. Do not add it to get a build to pass.

The check is a build failure rather than a checklist item on purpose: a thin
demo is fixable afterwards, and a canon leak into a public repository is not.
