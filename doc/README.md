# Project documentation

Condensed from the working documents that used to live in `tasks/`. Those files were planning logs,
implementation diaries and runbooks; what survived the condensation is the part a reader of the code
cannot reconstruct — **motivation, decisions, and facts that cost a measurement to establish.**

| Document | What it holds |
|---|---|
| [product-rationale.md](product-rationale.md) | Why the preview exists at all (the agent-eyes axis), the governing "facts from scripts, judgement to the AI" principle, the origin of the static-vs-model-driven policy, design reasons behind the preview pipeline, and deferred product/content ideas |
| [decisions.md](decisions.md) | Settled decisions and deliberate non-goals, each with the rejected alternative and its cost. Includes the preview-pipeline defect triage and the launcher static-asset decisions |
| [zk-measured-behaviour.md](zk-measured-behaviour.md) | 27 ZK / browser / launcher / model behaviours established by running something. The most expensive content here to re-obtain |
| [evaluation.md](evaluation.md) | The six-run end-to-end evaluation: reusable methodology, the nine repeated findings and their status, the method's own blind spots, and why it could not converge |
| [knowledge-roadmap.md](knowledge-roadmap.md) | Where ZK knowledge should live (check / pre-write lookup / example / prose), the retrieval-precision bug, the corpus version trap, and the unresolved XSD maintenance problem |
| [effectiveness-measurement.md](effectiveness-measurement.md) | Whether the pre-write lookup and Layers 6/7 give right answers — recall against the recorded failures, precision against 558 external ZUL files, and the two defects that sweep found |
| [dev-environment.md](dev-environment.md) | Iterating on the skill in its plugin form, the two prerequisites that silently degrade every preview, and why testing the skill *inside this repository* measures recall rather than generation |

Not documentation, but referenced from these files:

- `tasks/eval-private/` — the evaluation answer key (briefs, checklist, negative control, results).
  Deliberately gitignored: the examinee can read this repository, so the answer key must not be in it.

---

## Open items

Nothing here has an owner. Grouped by where the work would land.

### Knowledge and prevention — the highest-leverage group

- [x] **Turn `assets/zul.xsd` into a pre-write lookup** — done: `validate-zul.py --describe
      <component> [--attr <name>]`, with the instruction in Step 2 guideline 3 and a routing-table row
      so a bare "does ZK 10 have X?" reaches it. → [knowledge-roadmap.md §Tier 2](knowledge-roadmap.md)
- [x] **The last two Tier-1 rules** — done: Layer 6 (a literal `selectedIndex` pointing past the items
      that exist) and Layer 7 (`@Wire` type and id cross-check, opt-in via `--controller`).
- [x] **Does Layer 6's `selectedIndex` rule need a ZK 9 gate?** — no (D3). The rule had only ever been
      measured on 10.3.0.1, and it fires on markup that is all over older forum and demo content, so a
      ZK 9 difference would have made it a false-positive machine for exactly the users least able to
      argue with it. Re-measured case by case on **ZK 9.6.6**: identical outcomes on every case, so
      one rule serves both targets and `--zk-version` stays out of this layer. The same pass refuted
      two of the rule's own boundaries — `-1` is not universally legal, and `selectbox` was being
      accused wrongly. → [zk-measured-behaviour.md §21b](zk-measured-behaviour.md)
- [x] **The lookup's own wrong answers** — done (D25): `xs:simpleContent` is now traversed (it was the
      root cause of the `test/valid/zk-5793.zul` quarantine, which has been removed from the list), an
      element whose own type declares `xs:anyAttribute` is reported as taking arbitrary names, and
      `<apply>` / `<include>` are named as pass-through elements. Measured 70 → 33 wrong answers over
      967 external pairs, −61% file-weighted, with the default output changing on exactly one file.
      → [effectiveness-measurement.md §6](effectiveness-measurement.md)
- [x] **Layer 7 vs. `@Wire` inside a nested component class** — done (D26): both halves skip fields not
      declared in the outermost class body. Re-measured at 0 findings over 192 external pairs and 140
      `@Wire` fields. The same section records why the runtime NPE cannot replace the check: when the
      field is used only in an event handler, the render reports `STATUS: ok` and never sees it.
      → [effectiveness-measurement.md §4](effectiveness-measurement.md)
- [ ] **One cell of the `selectedIndex` table is still open: `cardlayout` on ZK 9 EE** (D5, deferred).
      Every other cell was measured on both 9.6.6 and 10.3.0.1. `cardlayout` is a zkmax component, ZK 9
      CE does not ship it, and no 9.6.x EE stack is cached locally — closing the cell means downloading
      a whole second `-Eval` stack for three renders. Layer 6 therefore *extrapolates* one rule to
      ZK 9 EE: that `<cardlayout selectedIndex="-1">` throws. The extrapolation is a reasonable one —
      the rejection comes from a bounds check against children that are already attached, which is the
      kind of thing that does not move between versions — and the limit is stated where the table lives,
      so no reader is misled. Cost of being wrong: one false positive for ZK 9 EE users.
      → [zk-measured-behaviour.md §21b](zk-measured-behaviour.md)
- [ ] **Fix the zk-doc retrieval precision bug** before growing any corpus. A combobox
      default-selection query returns `treeitem` first — and `treeitem`'s answer is exactly the wrong
      spelling an evaluation run tried first.
- [ ] **Resolve the XSD maintenance strategy.** Five files are quarantined in
      `test/known-failures.txt` as unfixed schema false positives, two of them the skill's own bundled
      assets. Two further instances, measured 2026-09-01, are deliberately *not* quarantined because
      each has a one-element workaround that the showcase pages use and `SKILL.md` Step 2 documents:
      a model-driven `<tree>` whose only child is a `<template>` needs an empty `<treechildren/>`, and
      a `<listbox>` with literal `<listitem>`s needs a `<listhead>`.
      **Decided (D4): keep the workarounds, leave the schema alone for now** — the documented
      workaround costs nothing and the schema is a 43KB document to operate on. What the second
      instance changes is the *size* of the problem, not the decision: a listbox with literal items is
      not model-driven at all, so §7's "model-driven components" framing is too narrow — the
      over-strict "required children" choices bite plainly static markup too.
      → [knowledge-roadmap.md §7](knowledge-roadmap.md)
- [ ] **Findings 7 and 9 from the evaluation** remain on the knowledge track: the ZK 10 theme owning the
      mesh header (`ui-to-component-mapping.md` contains no occurrence of "mesh"), and the
      read-the-schema-first habit.

### The evaluation

- [ ] **Add Q14 and Q15 to the checklist before reusing it.** Without them it inherits two known blind
      spots: arrangement *within* a section, and a broken icon.
- [ ] **The human spot-check (phase 3) was never run.** By design it cannot be delegated. Two pairs, R6
      and R4. If a reading disagrees with the blind verdict, every remaining blind verdict is void.
- [ ] **A third batch is no longer blocked on material.** This item used to read *"all three remaining
      mockups are disqualified"* — true only while the generation happens *in* this repository.
      `test/cleanroom/make-sandbox.sh` moves it out, which puts **8 of the 9 mockups back in play**
      (only *enterprise kanban board* stays out, its answer shipping inside the skill's own `assets/`).
      What is still open is whether to spend the runs. → [effectiveness-measurement.md §7](effectiveness-measurement.md)
- [ ] **D32: a second clean-room run.** One page cannot separate *"the skill does this"* from *"that page
      did this"*, and every pilot-01 finding is dashboard-shaped. Prefer a non-dashboard layout — *Data
      Comparison Modal* or *Test Case Management*. Worth doing now rather than earlier: the icon false
      negative is fixed, so a second run's icon results are trustworthy in a way pilot-01's were not.
- [ ] **Probe iteration 2**: drop the falsifying contrast from prompt 1, which currently measures the
      wrong thing; and reword *"let the measurement pick the edit"* → *"…name the cause"*, then re-run
      prompt 2 to see whether the report-don't-rewrite behaviour returns.
- [ ] Eight single-occurrence anecdotes remain on the watch list.
      → [evaluation.md §4](evaluation.md)

### Tooling and content

- [ ] **D2 (screenshot mid-animation) never reproduced locally** — 12 captures across 3 page shapes, all
      byte-identical and complete. The mitigation shipped; the acceptance criterion (fails before, passes
      after) is unmet. Open question: what a real dashboard chart has that a minimal fixture does not.
      → [zk-measured-behaviour.md §13](zk-measured-behaviour.md)
- [x] **`skills/zul-writer/assets/master-detail-mvvm.zul` — both defects fixed, now verified.** This
      item was **stale from birth**: `d8d6499` fixed the asset and created this list in the same
      commit, and its own message says so. The item was carried over from the `tasks/` documents
      being condensed and never reconciled against the change beside it.
      What was missing was evidence, since the asset had only been re-validated, and neither defect is
      visible to validation *or* to a first-paint render — both live in the **selected** state. Both
      versions were pasted as a page and rendered in both states:

      | Markup | nothing selected | a row selected |
      |---|---|---|
      | before `d8d6499` | master list **1265px** | master list **422px**, `CONTROLLERS: failed → isolated`, `PropertyNotFoundException: Property 'description' not found` |
      | the asset today | master list **422px** | master list **422px**, controllers executed |

      So the "snap to a third" was a 3× width jump on the first click, and the property defect did not
      render blank — it took the whole controller down. The lesson that outlives the fix is in
      `SKILL.md` Step 5, *A page with an empty state has two first paints*.
- [ ] **Decide `.zhtml`**: it returns 404 from the launcher today. Either keep that or render it — but
      the static handler must never start returning it as *source text*.
      → [decisions.md](decisions.md)
- [ ] **Skill-level evals** (`skills/zul-writer/evals/`) do not exist. Validator tests exist; nothing
      measures the skill as a whole against a no-skill baseline.
- [ ] **`make-sandbox.sh` does not stamp the skill version it copied.** Pilot-01's copy was three commits
      stale when the run was about to start — it would have measured a skill nobody ships, and nothing in
      the sandbox would have said so. Caught by hand once; print the copied skill's `git describe` into
      `MANIFEST.md` at build time.
- [ ] **`--dev` does not say which side of the line a clean-room pilot is on.** The flag is documented as
      "runs made while developing or testing the skill itself"; `MANIFEST.md` calls the sandbox "the skill
      under test", but the examinee is doing a genuine page build. Pilot-01 judged it real and left the
      flag off, so ~15 validator runs counted as ordinary usage. One sentence settles it either way.
- [ ] **`--watch` mode** (re-render on change, JVM and browser kept warm) is the one item from the
      preview specification never built. Lowest priority; it mainly helps people developing the skill
      itself, where the render is the slow part of every iteration.
- [ ] **The `zk.xml` error-page risk was never confirmed.** The showcase forwards every `Throwable` to
      `/error.zul`, which does not exist, so Step 5's error path may be reading a 404 instead of ZK's
      real error page. One cheap experiment settles it.
      → [dev-environment.md §2](dev-environment.md)
- [x] **The clean-room comparison was run** (pilot-01, `test/cleanroom/make-sandbox.sh`). Same mockup as
      evaluation run R5, generated outside this repository with no answer on disk: **7 renders, 2 of them
      fix rounds**, against R5's 10. It cannot separate the clean-room effect from the skill's changes
      since R5, but it yielded four defects the in-repo runs never surfaced — one of them a false negative
      in `icon-not-rendered`. → [effectiveness-measurement.md §7](effectiveness-measurement.md)
      A second run is **D32**, filed with the evaluation items above.

### Repo hygiene, still open from the 2026-07 review

- [ ] `CLAUDE.md` instructs running `./install-skill.sh` and updating `link-skill.sh`. **Neither file
      exists.** Restore them, or make `npx skills add` the documented local install.
- [ ] `marketplace.json` `homepage` is still the `https://github.com/your-org/agent-skill` placeholder.
- [ ] `license: MIT` is declared in `marketplace.json` but there is **no LICENSE file**.
- [ ] `.DS_Store` is not gitignored and copies sit **inside `skills/zul-writer/`**, so they ship with any
      packaging.
- [x] `SKILL.md` said *"Query `zk-doc-mcp-server`"*, a server that does not exist — corrected to
      `zk-doc` (tool: `search_zk_docs`).
- [ ] **No "do not generate" list in Step 2.** `<zscript>` and inline Java in event attributes are
      classic LLM ZUL mistakes — they are all over the old forum and demo content models trained on —
      and `SKILL.md` mentions `<zscript>` only in terms of what the *preview* does with it, never as
      something not to write. Four or five bullets, cheap and high-yield.
- [ ] **No file-placement guidance.** Nothing states where output belongs in a Maven/Gradle webapp
      (`src/main/webapp/**.zul`, `src/main/java/<package>/**.java` matching the `viewModel`/`apply`
      FQCN); the example commands imply it and nothing more. One short subsection prevents files landing
      in a repo root.
- [ ] **Theme advice is not actionable.** Step 1 can suggest `iceblue_c` but nothing says how to enable
      it (the theme jar dependency plus the `org.zkoss.theme.preferred` library property), so the agent
      cannot act on its own recommendation.

### Live constraint, not a task

- **The two version places move together, or not at all**: `SKILL.md` `metadata.version` and
  `marketplace.json`. Changing one alone is drift. `gemini-extension.json` is a separate line and is
  not expected to follow. → [decisions.md §D20](decisions.md)
- **There were three, and the scripts are no longer one of them.** `validate-zul.py` and
  `preview-zul.py` used to carry their own `SKILL_VERSION` literal; they now read `SKILL.md`'s
  frontmatter through `scripts/_skill_meta.py`, so a bump does not touch them at all.
  `marketplace.json` cannot join them — it sits outside the skill directory and no install ships it —
  so `test/run-version-consistency.py` holds it in step, and CI runs it first.
  → [decisions.md §D21](decisions.md)
- The condition the earlier wording waited on has happened. This entry used to read *"the version stays
  at 2.0.0 until the branch converges"*; the work converged into `main` and **2.0.0 is tagged
  `v2.0.0`**, so the number is a released point rather than a held one. The next change to either of
  the two places is a version bump, and it moves both.
- **"The next change" means the next *release*, not the next commit.** Read the other way once, on
  `fix/icon-not-rendered-weight`, and the bump was reverted: an unreleased branch must not carry a
  version number no tag corresponds to. The version stays at 2.0.0 until someone cuts a release, and
  that is when both places move together.
