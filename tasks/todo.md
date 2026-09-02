# D31 — act on the pilot-01 findings

Approved: option A, fix all four.

## Why the obvious fix is wrong

The naive reading of finding 1 is "also compare `cs.fontWeight` against the declared face's
weight". That would be **actively harmful**. CSS font matching never fails to pick a face: for a
family declaring only weight 400, a request for 900 still selects the 400 face and renders
correctly. Material Icons (declared 400) inside a `font-weight:bold` heading is exactly that, and
a weight-equality test would report it as a broken icon. That is a false positive on a rule the
agent is told to trust — the direction the rule's own comment calls unsafe.

The real failure is **glyph coverage inside the face the browser chose**, and `document.fonts`
cannot report coverage. So the check has to measure the rasterisation, not the declaration.

## Plan

1. [x] Build a reproduction fixture: the pilot page minus its `font-weight:900` rule
       → verify: current code renders blank icons and reports **nothing**
2. [x] Replace the family-only test with a rasterisation comparison: draw the codepoint with the
       pseudo-element's own computed font, and again with the same size/style/weight but a
       non-icon family. Identical rasterisation ⇒ the icon font supplied nothing.
       → verify: fixture now reports; the fixed pilot page still reports nothing
3. [x] Sweep the whole regression corpus for new false positives
       → verify: 0 new findings vs. the pre-change baseline
4. [x] Regression test covering "family resolves, weight selects a face without the glyph"
       → verify: fails on the old implementation, passes on the new
5. [x] SKILL.md Step 4 — cross-reference the chart carve-out at the point the rule is stated
6. [x] charts-guidelines.md — add the MVVM/`model=` path (file currently has zero mentions)
7. [x] SKILL.md Step 5 — warn that `position:fixed` lands at the viewport edge in a
       `--full-page` capture, so the image misplaces it

## Review

All seven items done. The code fix went in twice: the first version compared the glyph against a
**different** font stack (`monospace`), which looks equivalent and is not — when no family in a list
supplies a character the mark comes from the *first* family in that list, so two different lists
disagree even when both lack the glyph. That version was tested against the very page it was written
for and stayed silent. Holding the font constant and varying the codepoint instead is what works.

Evidence, in the order it was gathered:

| Check | Result |
|---|---|
| Fixture = pilot page minus one CSS line, old code | **0 findings**, icons visibly blank |
| Same fixture, new code | **4 findings**, each naming codepoint and weight 400 |
| Pilot page with the line restored, new code | **0 findings** — no false positive |
| 9 known-good showcase pages, new code | **0 findings** on all nine |
| A21 (the original wrong-carrier case) | still exactly 1, still names the label |
| A21b (`icon-weight.zul`) against the old code | silent — so it is a real regression test |
| `run-preview-tests.py` | **35 checks, 0 failed** |
| `run-regression.py` | 42 files, 0 regression / 0 stale / 0 orphan, 5 quarantined |
| `run-schema-query-tests.py` / `run-pattern-tests.py` | 35/0 · 7/0 |

**Version stays at 2.0.0.** It was briefly moved to 2.0.1 on the reading that `doc/README.md`'s
*"the next change to any of the three places is a version bump"* meant per-change; it means per
release, and this branch is not one. See the open item below.

Findings recorded in `doc/effectiveness-measurement.md` §7 and `doc/zk-measured-behaviour.md`
§20 / §17b.

Not done, and deliberately: `make-sandbox.sh` still does not stamp the skill version it copied.
Pilot-01's copy was three commits stale when the run was about to start, which would have measured a
skill nobody ships. It was caught by hand this time.
</content>
