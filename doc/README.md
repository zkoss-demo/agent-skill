# Project documentation

Condensed from the working documents that used to live in `tasks/`. Those files were planning logs,
implementation diaries and runbooks; what survived the condensation is the part a reader of the code
cannot reconstruct — **motivation, decisions, and facts that cost a measurement to establish.**

| Document | What it holds |
|---|---|
| [product-rationale.md](product-rationale.md) | Why the preview exists at all (the agent-eyes axis), the governing "facts from scripts, judgement to the AI" principle, the origin of the static-vs-model-driven policy, design reasons behind the preview pipeline, and deferred product/content ideas |
| [decisions.md](decisions.md) | Settled decisions and deliberate non-goals, each with the rejected alternative and its cost. Includes the preview-pipeline defect triage and the launcher static-asset decisions |
| [zk-measured-behaviour.md](zk-measured-behaviour.md) | 18 ZK / browser / launcher behaviours established by running something. The most expensive content here to re-obtain |
| [evaluation.md](evaluation.md) | The six-run end-to-end evaluation: reusable methodology, the nine repeated findings and their status, the method's own blind spots, and why it could not converge |
| [knowledge-roadmap.md](knowledge-roadmap.md) | Where ZK knowledge should live (check / pre-write lookup / example / prose), the retrieval-precision bug, the corpus version trap, and the unresolved XSD maintenance problem |
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
- [ ] **Fix the zk-doc retrieval precision bug** before growing any corpus. A combobox
      default-selection query returns `treeitem` first — and `treeitem`'s answer is exactly the wrong
      spelling an evaluation run tried first.
- [ ] **Resolve the XSD maintenance strategy.** Six files are quarantined in
      `test/known-failures.txt` as unfixed schema false positives, two of them the skill's own bundled
      assets. → [knowledge-roadmap.md §7](knowledge-roadmap.md)
- [ ] **Findings 7 and 9 from the evaluation** remain on the knowledge track: the ZK 10 theme owning the
      mesh header (`ui-to-component-mapping.md` contains no occurrence of "mesh"), and the
      read-the-schema-first habit.

### The evaluation

- [ ] **Add Q14 and Q15 to the checklist before reusing it.** Without them it inherits two known blind
      spots: arrangement *within* a section, and a broken icon.
- [ ] **The human spot-check (phase 3) was never run.** By design it cannot be delegated. Two pairs, R6
      and R4. If a reading disagrees with the blind verdict, every remaining blind verdict is void.
- [ ] **A third batch is blocked on material**, not on effort: all three remaining mockups are
      disqualified. Needs new mockups with no counterpart in this repo, or a decision to converge here.
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
- [ ] **`skills/zul-writer/assets/master-detail-mvvm.zul` still carries both defects** that appeared the
      moment it was pasted as a page: `vm.selectedItem.description` names a property no model has, and
      `visible="@load(not empty vm.selectedItem)"` hides the whole detail pane, so the page snaps from
      full width to a third on the first click. Reasonable in a generic snippet, defects in a page.
- [ ] **Decide `.zhtml`**: it returns 404 from the launcher today. Either keep that or render it — but
      the static handler must never start returning it as *source text*.
      → [decisions.md](decisions.md)
- [ ] **Skill-level evals** (`skills/zul-writer/evals/`) do not exist. Validator tests exist; nothing
      measures the skill as a whole against a no-skill baseline.
- [ ] **`--watch` mode** (re-render on change, JVM and browser kept warm) is the one item from the
      preview specification never built. Lowest priority; it mainly helps people developing the skill
      itself, where the render is the slow part of every iteration.
- [ ] **The `zk.xml` error-page risk was never confirmed.** The showcase forwards every `Throwable` to
      `/error.zul`, which does not exist, so Step 5's error path may be reading a 404 instead of ZK's
      real error page. One cheap experiment settles it.
      → [dev-environment.md §2](dev-environment.md)
- [ ] **The clean-room comparison was never run.** The rig is designed and the reasoning is recorded, but
      no screenshot has been put through both a scratch project and the showcase to measure the repo's
      influence — which is the only way to know whether `SKILL.md` or the showcase examples are carrying
      the output. → [dev-environment.md §4–5](dev-environment.md)

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

- **The skill version stays at 2.0.0 until the branch converges.** When it moves, all three places move
  together: `SKILL.md` `metadata.version`, `marketplace.json`, and the `SKILL_VERSION` constant in each
  script. Changing one alone is drift. `gemini-extension.json` is a separate line and is not expected to
  follow. → [decisions.md §D20](decisions.md)
