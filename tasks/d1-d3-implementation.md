# D1 / D2 / D3 — implementation log

Working plan and evidence for the three preview-pipeline defects specified in
`tasks/preview-pipeline-4-defects-spec.md`. D4 is closed (ZK product behaviour, no code change).

All three changes land in one file:
`skills/zul-writer/scripts/preview-zul.py`

Order follows Appendix A of the spec: **D2 → D1 → D3**. D2 first because a mid-animation
capture also poisons the `LAYOUT:` geometry that D1 and D3 are measured against.

## Environment

| Item | Value |
|---|---|
| Launcher jar | `/Users/hawk/Documents/workspace/PLUGIN/zkidea/zk-preview-launcher/build/release/zk-preview-launcher-1.0.2.jar` |
| Suite interpreter | a uv venv with `playwright` — the suite spawns `sys.executable`, so a bare `python3` reports 18/20 failures that are the interpreter, not the contract |
| Compile | `cd zulwriter-showcase && withjdk.sh 17 mvn -o compile` |

## Steps

1. **Baseline** → verify: the existing contract suite is green before anything changes.
2. **D2 repro** → verify: three consecutive captures of a default-animation chart differ.
3. **D2 fix** → verify: same three captures become byte-identical; no author-side change needed.
4. **D1 repro** → verify: a visibly clipped button label produces no `clipped-text` finding.
5. **D1 fix** → verify: the sample reports it; the clean page still prints no `LAYOUT:` block.
6. **D3 repro** → verify: a fixed overflow figure that does not move when the parent grows.
7. **D3 judgement + fix** → verify: the artefact sample goes quiet, a genuine overflow still reports.
8. **Full suite** → verify: every pre-existing check still passes, exit 0.

## Global constraints carried through every step

* The audit runs after the screenshot and must not mutate the page.
* The audit stays wrapped in `try/except` — a bug in it must never fail a good render.
* stdout block order is a contract; `LAYOUT` sits between `CONTROLLERS` and `WARNINGS`.
* Caps may limit what is printed, never what `total` reports.

## Progress

| Step | Status |
|---|---|
| 1 Baseline | **done** -- 20 checks, 0 failed, exit 0 |
| 2 D2 repro | **could not reproduce** -- 12 captures, 3 page shapes, all byte-identical and complete |
| 3 D2 fix | **done** -- `ANIMATION_OFF_JS` + `_settle()`, 260-350ms, no output change anywhere |
| 4 D1 repro | **done** -- nested-clipper case silent at HEAD |
| 5 D1 fix | **done** -- `clipRegionOf()` intersects every clipping ancestor, per axis; case now reported |
| 6 D3 repro | **done** -- 16px at parent heights 34 / 52 / 64, identical, exactly as R6 described |
| 7 D3 fix | **done** -- `escapes-parent` requires ink in the clipped strip; artefacts silent, genuine spill kept |
| 8 Full suite | running -- 20 existing checks plus A15 / A16 / A17 |

## What shipped

| File | Change |
|---|---|
| `skills/zul-writer/scripts/preview-zul.py` | all three fixes |
| `skills/zul-writer/SKILL.md` | `escapes-parent` row now says *visible content* |
| `skills/zul-writer/references/preview-guidelines.md` | intersection rule, ink requirement, new "does not flag" entry |
| `test/run-preview-tests.py` | A15, A16, A17 |
| `preview-fixtures/layout-nested-clip.zul` | D1 regression sample |
| `preview-fixtures/layout-escapes-parent.zul` | D3 regression sample |
| `preview-fixtures/chart-animation.zul` + `ChartAnimationComposer.java` | D2 regression sample |

## Findings as they land

### D2 — the first fixture was too easy, and that is itself worth recording

A `<charts width="640" height="360">` with twelve points renders **complete** in all three
captures, byte-identical. The animation is over before the capture, because `networkidle` plus
`fonts.ready` already cost more than the ~1000ms the entry animation takes.

What R5 actually had, and what the retry uses, is `hflex`/`vflex` sizing. That matters because
zkcharts *defers chart construction to `onSize`* when either flex is set
(`Charts.src.js:141-144`, then the `onSize` branch at `:183-200`) — so the chart starts
animating **after** ZK's sizing pass, which is after the waits the pipeline knows about.

The practical read: the defect needs a chart that is sized responsively, which is exactly how a
dashboard chart gets written and exactly what R5 wrote.

### Incidental: the fixture tripped the `--` XML comment defect

The first draft of `chart-animation.zul` said "Rendered with `--run-controllers`" in an XML
comment and failed to parse. That is the same defect the evaluation found and fixed at source in
`3d485f2` — it is a property of XML, not of the skill, and it catches anyone writing a comment
about a command-line flag.

### D1 — confirmed, cause pinned, fixed

The probe (`preview-fixtures/layout-nested-clip.zul`, five cases) run through the script at HEAD and then
through the patched one:

| Case | At HEAD | Patched |
|---|---|---|
| A `<button>` narrower than its label, no explicit overflow | silent | silent |
| **B text cut by the OUTER of two nested clippers** | **silent** | **`text needs 178px, box is 80px`** |
| C single clipper directly around the text | reported | reported, unchanged |
| D roughly 3px cut | reported | reported, unchanged |
| E fits | silent | silent |

So the cause is the first of the four the spec listed, in a sharper form than "no clipping
ancestor": there *was* one, `clipperOf` returned it, and it was the wrong one. The nearest
clipping ancestor is not what a text run is visible inside -- the **intersection of all of them**
is. A roomy `overflow:hidden` box nested in a narrow one made plainly cut text measure as fitting.

Case A is worth recording as a non-defect: a `<button>` whose label is wider than its width does
not clip in Chrome, the text simply overflows the border box and stays readable, so silence is
the correct answer there and not a second false negative.

**No new false positives.** The three existing layout fixtures re-run against the patched script:

* `layout-clipping.zul` -- the same 4 findings, identical text
* `layout-overflow.zul` -- the same 3 findings, identical text
* `healthy-page.zul` -- still no `LAYOUT:` block at all

### D2 -- the symptom does not reproduce here, and that has to be said plainly

Six captures of the chart fixture -- three at HEAD, three patched -- are **byte-identical to each
other**, and the chart is complete in all of them. That holds for the `width`/`height` version and
for the `hflex`/`vflex` version. The animation is over before the capture, so on this machine
there is nothing for the fix to fix on this page.

That is not proof the defect is imaginary: the mechanism is not in question (Playwright's
`animations="disabled"` covers CSS animations and transitions only, and Highcharts animates
through requestAnimationFrame onto SVG attributes). What is in question is what R5 had that a
minimal fixture does not. Next: a heavier, dashboard-shaped probe, and a direct reading of
whether anything moves after the existing waits.

### D3 — reproduced exactly, judged a measurement artefact, fixed

`preview-fixtures/layout-escapes-parent.zul` puts three status bars in boxes that differ only in
height. At HEAD:

```
escapes-parent | hlayout.sb34 | escapes clipping parent div.region by 16px on the bottom
escapes-parent | hlayout.sb52 | escapes clipping parent div.region by 16px on the bottom
escapes-parent | hlayout.sb64 | escapes clipping parent div.region by 16px on the bottom
escapes-parent | div.spill    | escapes clipping parent div.region by 46px on the bottom
```

**16px at every parent height** — the same behaviour R6 hit at 34, 52 and 64px, reproduced from
first principles rather than guessed at. The mechanism is not the inline-block dot R6 suspected:
it is `height: 100%` plus vertical padding under `box-sizing: content-box`. The child's box is
always *parent + padding*, so the overflow is a constant, and the single move the message invites
— give the parent more room — cannot ever change it.

**Judgement, recorded in the code: (b), a measurement artefact.** The rule measured boxes, and a
box edge crossing a clipping boundary with nothing rendered behind it costs the reader nothing.
`escapes-parent` now requires *ink* in the strip that gets cut: the element's own background or
border, its own text, or a descendant that paints. After the fix:

```
escapes-parent | div.spill | escapes clipping parent div.region by 46px on the bottom
```

The three artefacts are silent; the genuine overflow still reports. That is the difference between
correcting the rule and switching it off, and the fixture asserts both halves.

### Cost of the settle gate

Measured from inside the run rather than inferred from wall clock:

| Page | settle |
|---|---|
| `healthy-page.zul` | 260 ms, still after 2 frames |
| `chart-animation.zul` | 284 ms, still after 2 frames |

Inside the 500ms the spec allows. An earlier wall-clock comparison suggested +1.1s, but that was
measured while another render chain was running on the same machine — the in-run number is the
one to trust.

## Incidental finding, found outside D1-D3 and now FIXED

On the chart page the pipeline **silently skipped its ZK-ready wait**, at HEAD and patched alike,
so it was pre-existing and nothing to do with the three fixes above:

```
-- HEAD / chart-animation --      debug: zk client engine: absent (error page, or no ZK content)
-- HEAD / healthy-page --         debug: zk client engine: mounted
```

### The first diagnosis was wrong, and the network data is what corrected it

I initially recorded this as "zkcharts is big, so `window.zk` is slow". It is not. On the chart
fixture `zk.wpd` finished downloading at **499 ms** and `window.zk` existed at **2,507 ms**, both
long before the `load` event at 6,321 ms; `chart.wpd` arrives afterwards, exactly as expected.
Nothing about loading ZK was ever slow.

What actually happens is that `wait_for_function` evaluates its predicate **on the page's own main
thread**. A 20ms-interval probe shows that thread blocked solid:

```
main-thread stalls over 250ms (chart-animation)
  at    609 ms  blocked for 2,578 ms
  at  3,187 ms  blocked for   930 ms
  at  4,569 ms  blocked for 1,965 ms
  at  6,534 ms  blocked for 4,575 ms   <-- the pipeline starts asking at 6,376 ms
```

The check could not observe a condition that had been true for four seconds. `ZK_READY` resolved
**34 ms** after `window.zk` once the thread freed, so ZK had been fully mounted the whole time --
the message "no ZK content" was wrong twice over. `healthy-page` runs the same course with a 961 ms
stall instead of 4,575 ms, which is the only reason it never showed the fault.

### The fix

Stop asking a question that needs the main thread. Whether a page carries a ZK client engine is now
read from the HTML the server sent -- every ZK page fetches its engine from under `/zkau/`, and the
launcher's own error page does not (measured: 200 with it for both ZK fixtures, 500 without it for
`render-error.zul`). The 5s gate is gone entirely; `ZK_READY` is already false while `window.zk` is
undefined, so it needed no separate gate.

| Page | Before | After |
|---|---|---|
| `chart-animation.zul` | `absent`, mount wait skipped | `mounted` |
| `healthy-page.zul` | `mounted` | `mounted`, unchanged |
| `render-error.zul` | 5s burned before giving up | identified from the response, no wait |

### What it costs, measured per stage rather than by wall clock

Whole-process wall time is not usable for this comparison: Chrome's own launch varies between
4.9s and 8.4s run to run, which swamps the change. Stamping each `--debug` line instead, same
fixture, the commit before this one against this one:

| Stage | Before | After |
|---|---|---|
| startup: python, cached classpath, JDK, jar digest, **JVM up and reporting its port** | 1.30s | 0.70s |
| Chrome launch | 6.20s | 4.87s |
| `goto(wait_until="load")` — includes ZK's first-request init and the .zul compile server-side | 6.91s | 6.50s |
| **the ZK gate** | **5.03s, then the wrong verdict and no mount wait** | **5.70s, then `mounted`** |
| networkidle + fonts + settle | 1.21s | 0.38s |
| screenshot + layout audit | 0.45s | 0.46s |

So the gate itself costs **+0.67s**, not the +3.5s an earlier note in this log claimed — because the
old code was already spending 5.03s on a check that then failed. The server is not where the time
goes either: the JVM is up and serving inside the first 0.7s, and ZK's real startup cost is inside
the `goto`, on the first request.

Covered by **A18**, which asserts both halves: the busy page is recognised as ZK, and the page with
no ZK is still recognised as having none. A check that answered "yes, ZK" for everything would pass
the first half alone.
