# Where ZK knowledge is missing, and where it should live

The skill can now *detect* what went wrong on a rendered page — but detection costs a round. What
knowledge, held before writing, would have made the round unnecessary, and does that knowledge belong in
the Agent Skill, in the ZK docs, or in runnable examples?

Evidence: the six-run evaluation, live retrieval probes against the zk-doc MCP, and a survey of
`DOC/zkbooks` (409 `.zul` files, branch `11.0.0`).

**This document is mostly open work.** Items 1 and 2 below are the unexploited leverage.

---

## 1. The failures have a shape, and it is not ignorance

The agent never failed because it did not know how to build a grid. **It failed because it knew three
plausible spellings and picked a wrong one.**

| What it wanted | Spellings within reach | Work |
|---|---|---|
| an icon next to text | `<label sclass="z-icon-x"/>` · `<span sclass="z-icon-x"/>` · `iconSclass` | 2 of 3 |
| a combobox with a default selection | `<comboitem selected="true">` · `selectedIndex="0"` · `model.addToSelection()` | 1 of 3 |
| a CSS class on a chart | `sclass` · `className` · `zclass` | 2 of 3 |
| a toggle button in ZK 10 | `<togglebutton>` | 0 of 1 — no such component |
| a listbox with fixed rows plus a model | `setModel()` + literal `<listitem>` | unsafe, silently |
| wiring a component in a composer | `@Wire Label x;` on an `<a>` | compiles, `ClassCastException` at runtime |

This matters because **both media the question offers are bad at selection failures**:

- **Prose describes the correct thing.** It rarely enumerates the wrong neighbours — a human reader who
  has already chosen `iconSclass` does not need to be told `<label>` fails.
- **An example demonstrates one correct thing.** It says nothing about the neighbours either, but it does
  something better: it **pre-empts the choice.** An agent that copies a working spelling never reaches
  the fork.

That is the whole answer to "documentation vs. examples", and it is why examples are worth more than more
prose here. It is not the whole answer to the question, because two other options beat both for a large
slice of these failures.

---

## 2. Four places, not two

### Tier 1 — a deterministic check (highest leverage, cheapest)

A check has **100% recall.** Knowledge you must remember is knowledge you can fail to retrieve; a rule
that runs on every file fires every time. `z-icon-*` on `<label>` is the clearest case: it appeared in
3 of 6 runs and **was misdiagnosed all three times**, once shipping a page where every icon was an empty
box. No amount of documentation survives an agent that never searches for it, because the agent did not
know it had a problem.

The infrastructure already exists and is already correct: `validate-zul.py` has five layers, Layer 2
validates against the shipped `assets/zul.xsd` (183 KB), and Layer 4 is version-aware via
`--zk-version`. **What is missing is a handful of rules, not a system.**

*Status: done.* The icon case, `setModel()` beside literal rows, and collapsible state were mechanised
in `preview-zul.py` (per [D18](decisions.md)). The last two landed in `validate-zul.py`:

- **Layer 6, runtime semantics** — a literal `selectedIndex` pointing past the items that exist. Safe
  from markup alone because the index is applied while the component tree is built, *before* any
  Composer runs and before the binder loads a model, so a controller filling the component later
  cannot rescue it. Silent when a `model` is present, since the model's size is unknowable statically.
- **Layer 7, controller cross-check** — `@Wire` field type against the id's component, plus a wired id
  no component declares. Opt-in via `--controller`, so the default output shape is unchanged. It
  declines to judge component families where one element-named class inherits from another
  (`Textbox`/`Combobox`, `Checkbox`/`Radio`, `Box`/`Hbox`, `Row`/`Group`, `Listitem`/`Listgroup`,
  `Button`/`Combobutton`), because without a real class hierarchy a legal ancestor and a wrong type
  are indistinguishable — and a false accusation costs more than a missed defect. Measured against
  the repository's own five controllers and 30 `@Wire` fields: zero false positives; an injected
  `@Wire A` on a `<label>` is caught with the line of the declaration to edit.

### Tier 2 — a pre-write lookup (the gap nobody has filled)

**This is the cheapest unexploited knowledge in the whole system.**

In two runs the agent went and read `zul.xsd` *before* writing an unfamiliar component, and both said the
schema — not the documentation — is what saved them. One learned `<charts>` takes `className`/`zclass`,
not `sclass`; the other learned `<togglebutton>` does not exist in ZK 10.

**They invented that move themselves.** The skill never suggests it, so it happened 2 times out of 6.

The skill **ships the schema but only uses it as a checker.** A checker answers *after* you wrote it
wrong, at the cost of a round. The same file, queried *before* writing, answers for free — exactly,
locally, deterministically, with no retrieval risk at all.

The shape is a small script over a file this repo already carries:

```
zulq.py charts --zk-version 10          →  attributes: className, zclass, … (no sclass)
zulq.py togglebutton --zk-version 10    →  not found in ZK 10
```

Note the boundary: this was classified as a "knowledge track" item and handed off, but **it queries the
skill's own bundled `assets/zul.xsd`, not the ZK website.** It is a tool in this repository. Filed
elsewhere, it risks having no owner.

### Tier 3 — a runnable example (zkbooks)

The survey backs the instinct: **8 of 8 probe topics found**, 63% of files ≤30 lines (near-ideal
retrieval chunks), every example runnable rather than a fragment, and the zul→Java link
machine-parseable through `apply=` / `viewModel=`. For "what is the known-good spelling of X", nothing
beats a file known to run.

zkbooks also already contains the *right kind* of negative example, in exactly one place:
`developersreference/.../uiPattern/hflexVflex.zul` annotates the parent-must-have-height pitfall as
**"Wrong!"** next to the correct form. **Right and wrong side by side in one runnable file is what a
selection failure actually needs**, and it exists in 1 file out of 409.

### Tier 4 — prose documentation

Principles and when-to-use-what. **This tier already works where it is well-indexed** — the mesh-header
query returned the correct document first and named `--zk-mesh-title-background-color`, which is exactly
how one run solved it. Do not spend effort here.

---

## 3. The binding constraint is retrieval, not corpus size

Three live probes against the zk-doc MCP:

| Query | Top hit | Verdict |
|---|---|---|
| icon on a label not showing | `label-template` (0.097); the relevant `font_awesome.md` ranks **4th** | buried under noise |
| combobox default selection | **`treeitem` (0.312)**; combobox 2nd | **actively wrong** |
| mesh header background | correct document, 1st | works |

The middle row is the one to worry about. `treeitem`'s documentation says `<treeitem selected="true">`
pre-selects an item — and **`<comboitem selected="true">` was exactly one run's first failed attempt.**
The retriever did not merely fail to help; it surfaced the wrong answer, from a neighbouring component,
with confidence.

Two consequences:

1. **Adding 409 example files to this retriever will make precision worse before it makes recall
   better.** Near-miss neighbours are what it is already bad at, and examples are almost entirely
   near-miss neighbours of each other. The `mvvmreference/` ↔ `developersreference/.../mvvm/`
   duplication (`form/order2.zul`, `collection/tree.zul`, …) adds a second layer of the same problem.
2. **Some knowledge is unreachable no matter how it is written.** The answer to the `hflex="min"`
   under-measurement is in the docs today — at the bottom of `font_awesome.md`. The run framed its
   problem as layout, the answer lives under fonts, and it shipped a CSS hack it called "a blunt
   instrument, not a diagnosis". No new document fixes that; cross-domain linking or a check does.

---

## 4. The version trap — read this before indexing anything

- `zkbooks` is checked out on branch **`11.0.0`**, and every pom declares an `…-Eval` build of 11.
- The skill declares **ZK 9/10** and defaults `--zk-version` to **10**.

**An example corpus one major version ahead of the target will actively introduce errors.** Not
hypothetical: one run's real failure was writing `<togglebutton>`, a component that does not exist in
ZK 10. Version-sensitive spellings are precisely the class of fact examples are supposed to fix, and a
mis-versioned corpus inverts the benefit.

zkbooks has a **`10.2.0` branch.** Any indexing must be branch-aware, and a retrieved example must carry
its ZK version so the skill can reject or flag an example newer than the project.

Two further durability risks: the eval build pulled from the ZK eval repo typically **expires**, and
there is **no CI anywhere in that repo** — nothing verifies these examples still compile or run. A corpus
the agent copies from, whose runnability is asserted rather than tested, degrades silently.

---

## 5. Recommendations, in priority order

1. ~~**Finish the Tier-1 rules.**~~ **Done** — Layers 6 and 7, see §Tier 1 above.
2. ~~**Turn the shipped `zul.xsd` into a pre-write lookup, and tell the skill to use it.**~~ **Done** —
   `--describe`, with the instruction in Step 2 and a routing-table row so a bare "does ZK 10 have X?"
   reaches it without starting a workflow. No new corpus and no retrieval risk, as designed. The
   remaining measurement is item 6 below: whether renders-per-page actually falls.
3. **Fix retrieval precision before growing the corpus.** The combobox→treeitem result is a concrete,
   reproducible bug with a concrete fix: extract the component name from the query and use it to filter or
   boost. Measure with a fixed query set built from the nine evaluation findings — real questions with
   known-correct answers, which is a better benchmark than synthetic queries.
4. **Then index zkbooks — branch-aligned, chunked, tagged.** In that order, with these preconditions: pin
   to the branch matching the target ZK version (`10.2.0`, not `11.0.0`); chunk `componentreference` on
   `<n:h1>` boundaries, or a query for "avatar with an icon" returns 142 lines; deduplicate
   `mvvmreference` against `developersreference/.../mvvm`; and carry `{component, concept, zk_version}`
   metadata, without which this corpus amplifies the precision problem in §3 rather than fixing it.
5. **Extend the "Wrong! / Right" example pattern.** For a selection failure a contrast example is worth
   more than two correct ones, because it is the only form that teaches that the neighbours are wrong. The
   skill's own `preview-fixtures/icon-carrier.zul` is the same idea, written for the same reason.
   Candidates: the icon carrier table, combobox default selection, `setModel` vs. literal rows.
6. **Leave the prose docs alone** except for two facts that are genuinely absent rather than merely
   unfindable: that `<label>` cannot carry `z-icon-*`, and the MVC counterpart of the model-driven
   two-pass rule — MVC has no ZUL-side literal path at all, so "write the data in, then take it out" is
   MVVM-only advice being applied to both. *(The second has since been written; the first is covered by a
   measurement instead.)*

---

## 6. How to know it worked

The evaluation already supplies the measurement: **renders per page.** The cap was three; runs used 4, 3,
3, 3, 10 and 5. Every render past the first is a round that pre-write knowledge was supposed to prevent.
Re-run the six-design suite after items 1–2 and compare render counts and the misdiagnosis rate on the
icon finding — a direct read on "get it right the first time", needing no new benchmark.

**That re-run is blocked on material, and a substitute measurement has been run instead.** All six
mockups now have finished pages in this repository, so a re-run measures recall rather than generation.
What was measured is the prerequisite question — whether the new tooling gives *right* answers — against
558 external ZUL files and 192 zul/controller pairs. Results, including the two defects it found, are in
[effectiveness-measurement.md](effectiveness-measurement.md).

Worth noting for expectations: in the probe evaluation, the skill *without* the probe still reached the
correct icon diagnosis on its own — it simply cost twice the tool calls. **Detection and prevention both
work; prevention is the one that is cheap.**

---

## 7. The shipped `zul.xsd` is maintained by whack-a-mole — still unresolved

Both Tier 1 and Tier 2 rest on `assets/zul.xsd`, so how it is maintained matters more than its size.
Today it is patched reactively, one bug at a time: git history shows one-off commits for `fileupload` in
`anyGroup`, `toolbarType` children, `groupfoot` in `rowsType` — and a single afternoon's review found two
more *classes* of false positive.

`test/known-failures.txt` currently quarantines **six files** for exactly this reason — four
`test/valid/*` files and two of the skill's own bundled assets (`kanban-board.zul`,
`example-data-management-mvvm.zul`). CI is green because it fails on *drift* (a new regression, or a
quarantined file that now passes and must leave the list), not on the absolute state. Every entry is an
unfixed schema false positive.

**Why this is worse than ordinary technical debt:** when the skill validates its own examples as broken,
the agent either wastes turns "fixing" correct code or learns to ignore validation failures. Both are
bad, and the second destroys the value of every rule in Tier 1.

Options, in order of preference:

1. **Generate the XSD from ZK's source of truth** — the `lang.xml` / addon component definitions inside
   the ZK jars — with the generator committed to the repo. Hand edits stop; regeneration is documented
   and repeatable. Keep the existing version stamp.
2. **One systematic pass instead of per-bug patches**, if generation is too costly now: add a shadow
   element group (`forEach`, `if`, `choose`, `apply`) reference to every container content model, and make
   trailing "required children" choices optional for every model-driven component (listbox, grid, tree,
   combobox…), since MVVM templates legally replace static children. Those two changes cover both classes
   found in review and both remaining quarantined assets.
3. Either way, the regression corpus in CI is what makes schema surgery safe — **do that first**, which is
   already the case.
