# The Krites read — what the surface needs from the engine

`krites.html` renders Aerine's read of a free run in four parts:

| part | the question | rendered from |
|---|---|---|
| one — **what we know** | what did my entry actually land on? | `entry[]`, `coverage{}` |
| two — **where it thins** | where does this run stop, and why? | `weakest[]`, `absent[]`, `unresolved[]`, `notes[]` |
| three — **what we know there anyway** | what does canon hold in the thin places? | `returned[]` |
| four — **worth a look** | what connects my entry to something I did not ask about? | `returned[].via`, `returned[].edge_weight` |

## The finding: this needed no new engine contract

*(Reached here independently, then confirmed by the poster mid-build: the
`freeRun()` shape is already frozen in `engine/README.md` and the four parts map
onto it one-to-one. This section is what the surface found by building against
it; it is not a restatement of the ruling.)*

**All four parts came out of the existing `freeRun()` return value unchanged.**
Nothing was added to the engine to build this page, and nothing in the payload
is unused by it. The density the founder described is not a missing capability —
it is the same read presented in engine order (entry, coverage, returned,
absent) rather than in the order a reader needs it.

So the recommendation to the engine seat is **not** a `kritesRead()` that emits
a four-part structure. Freezing the four parts in the engine would put the same
state in two places and make the surface's ordering a protocol change. The four
parts are a *reading*, and readings belong in front of the seam.

What the engine should carry is the three facts below, which the surface
currently has to state as "not carried by this payload".

## Three fields the surface is asking for

### 1. `canon_desk_totals: { symptom, biology, nutrition, mechanism, measurement }`

`coverage{}` says how many of *your* claims landed on each desk. It does not
say how much canon holds there, so the page cannot tell a reader the difference
between *"your entry is thin here"* and *"the store is thin here"* — which is
the founder's own distinction and the honest core of part two.

That number already exists in the engine and already leaks into the payload as
prose:

```
absent[0].reason = "canon holds 30 nutrition erga, none of them connected to
                    this entry set by a shared seed ..."
```

A surface that needs the total has to either regex an English sentence or
hard-code a count. Both are wrong. Carry it as a field, for all five desks, on
every run — not only the absent ones.

**Why this matters more than it looks.** Symptom is not the thinnest desk —
measurement is. Symptom is the thinnest desk that carries consumer demand,
which is the sharper fact and the one the read has to be honest about: two of
the three readers arrive through symptoms. A reader who arrives that way
deserves to be told that the store itself is thin there, rather than being left
to infer it from an empty-looking panel.

The per-desk totals are already released — several fixtures' `absent[]` reasons
state them in the clear. What is missing is only that they arrive as a field
rather than as a sentence, on every run rather than on the absent ones.

### 2. `desk_state: { <desk>: "covered" | "thin_read" | "thin_absent" | "thin_silent" | "not_read" }`

The page currently derives each desk's state by membership tests
(`weakest.indexOf`, `absent` lookup, `returned` grouping). That is a reading of
authored fields and it is honest, but it is a rule about what the read *means*,
and rules about meaning belong behind the seam where every surface gets them.

The five states, and why all five have to exist separately:

- `covered` — your entry covered this desk; the run did not read further here.
- `thin_read` — one of the thinnest desks, and the run came back with claims.
- `thin_absent` — one of the thinnest desks, and canon could not be read here;
  `absent[].code` says which kind.
- `thin_silent` — one of the thinnest desks, nothing returned, **no reason
  recorded**. Unknown, not empty.
- `not_read` — neither covered nor read. Nothing was checked here either way.

The last two are the whole reason for the field. On a page about somebody's
health, `thin_absent`, `thin_silent` and `not_read` all render as an empty
panel unless something forces them apart — and "we could not evaluate this"
must never end up looking like "this is clean".

### 3. `returned[].via_seed` — the bridge's own name

Part four's rule is that a suggestion with no visible bridge is a
recommendation, and this product does not recommend. Today `via: [ergon_id…]`
names the claim the link was walked from, and the page prints that claim in
full — so the bridge is visible. What is not visible is **what the two claims
share**, which is the seed the edge was built on. The engine has it at
`egoNetwork()` time.

With it, part four can say *"these two are linked because both are about
`methane_detection`"* — which a reader can judge. Without it, the reader can
see the two ends of a link and has to take the middle on trust.

Structured `chain_hints` in canon already carry `via_seed` on every one of the
authored 1-hops, and `target_ergon` on only a small minority. The engine's
computed edges should carry the same field name as the authored ones — and a
surface keyed on `target_ergon` would render a blank most of the time, which is
why this page treats `via_seed` as the bridge and shows `target_ergon` only
when it is there.

## The `source` block — what the surface does with it (Krites v2)

*Added 2026-09-22, job `4364393e`, D-39 item 6. The contract change is Keel's;
this is the surface's half of it, written down so the render is not a surprise
when the field lands.*

The founder's own reading of what a record should show: *"The ergon id, desk,
grade, and link is a good record to show, I think."* Those four now lead every
record drawer, in that order.

The link is rendered from a `source` block on the node itself, alongside
`ergon_id` / `desk` / `assertion` / `grade`:

```json
"source": { "ref": "…", "doi": "10.1000/x", "url": "https://…", "open_access": true }
```

**The surface offers a link only when `open_access === true`.** That is one
rule in one helper (`paperLink`), not care at a dozen call sites, because the
failure it prevents — the words *"read the paper"* over a paywall or a 404 —
is the page telling a reader something it cannot verify. What the surface does
with each shape, all five proved by construction against a tree carrying them:

| the block says | the card shows |
|---|---|
| `url` + `open_access: true` | `source`, `doi`, and **paper → read the paper ↗ · open access** |
| `doi` + `open_access: true`, no `url` | the same, linked through `https://doi.org/<doi>` |
| `open_access: false` | `source`, `doi` as text; **no link**, and the card says *not marked open access — no free link to offer* |
| no `source` block at all | today's honest text, unchanged; **no link is manufactured from the id** |
| a published ergon (`data/erga.json`) with a `source` block | the whole record *and* the paper link |

`open_access` absent is treated as `false`. A missing flag is not permission.

**What left the card:** the corpus `sha256`. It was printed on every
unpublished record, which made a 64-character digest the most prominent thing
on the commonest card, and it is provenance about the *run* rather than about
the *claim*. It lives once, in the page's colophon, where it already was.

`ref`, `doi`, `url`, `open_access` are the four the surface reads. Anything
else in the block is passed over in silence rather than rendered as an unnamed
row — a renderer that prints whatever it is handed is how private fields reach
a public page.

## Fixture the surface cannot demonstrate

The five released runs cover four of the founder's readers: the consumer
arriving through symptoms (`consumer-ibsd`), the consumer arriving through food
(`consumer-fibre`), the device (`device-gas`), the agent (`agent-relay`), and
the honest-failure case (`unresolved-params`).

**There is no released run for the third reader — the one entering through
butyrate production.** That page cannot be shown without one, and cutting one
here would mean either inventing a payload or publishing canon this repository
has not released. Neither is acceptable, so the gap is named instead: a
`consumer-butyrate` run, cut by `engine/build-fixtures.mjs` and released by
whoever owns the canon, is the one thing missing from the demonstration.

## What the surface will never ask for

- **A ranking, a score or a total.** `krites.html` renders `returned[]` in the
  order the engine ranked it and says so on itself. It does not re-order, and
  it has no maximum to scale against.
- **A verdict.** Grades ride on claims. The page emits no judgement of its own
  about a desk, a run or a reader.
- **A ranking of its own.** Part one's per-desk list is capped at five, strong
  tier before moderate, and emerging is never used to pad it — that is a ruling
  from the job poster, it is stated in the page's own header comment, it is
  stated on the page where it bites, and nothing is dropped: the remainder
  opens in place, in payload order. If the engine would rather own the cap, it
  can carry the capped list and the surface will render exactly what it gets.
- **A recommendation.** Part four renders reading routes. Nothing on the page
  tells a reader to do, take, avoid or change anything, and the disclaimer that
  says so is a boundary the page must keep true.
