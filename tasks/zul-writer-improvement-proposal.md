# zul-writer Skill — Comprehensive Review & Improvement Proposal

Date: 2026-07-06
Scope reviewed: `skills/zul-writer/` (SKILL.md, 4 references, 2 scripts, 24 assets), repo integration files (marketplace.json, CLAUDE.md, GEMINI.md, gemini-extension.json), `test/` corpus, and `zulwriter-showcase/` real-world outputs. All findings below were verified by running the skill's own validator against its test corpus, bundled assets, and showcase gallery.

---

## Executive Summary

zul-writer is a well-architected skill: the 4-step workflow is clear, progressive disclosure is used correctly (183-line body, references/assets loaded on demand), and the 4-layer validation script is a genuine differentiator that no generic LLM run would have. The distribution story (Claude Code / Gemini CLI / Copilot) is ahead of most skills.

However, **dogfooding exposed a credibility gap: 5 of 14 bundled `.zul` assets fail (or cannot complete) the skill's own validator**, one showcase file fails it, the primary MVVM Java template doesn't compile, and the skill body directly contradicts one of its own assets. There is also one confirmed bug in `validate-zul.py`, a pattern of reactive whack-a-mole XSD patching (3 of the last 8 commits), and no regression net (CI/evals) to stop these from recurring.

The proposal: fix the P0 correctness defects (≈1 day), then invest in the systemic items — XSD strategy + CI regression corpus, workflow wiring gaps, and telemetry transparency (≈1 week), then add skill-level evals and trigger optimization.

---

## 1. What's Working Well (keep as-is)

| Area | Evidence |
|---|---|
| Progressive disclosure | SKILL.md body is 183 lines; heavy content lives in `references/` and `assets/`, loaded only when needed |
| 4-layer validator design | Well-formedness → XSD → attribute placement → ZK10 compat; excellent error messages with line numbers and hints (`test/wrong/textbox-iconSclass.zul` produces an actionable "Valid on: a, bandbox, button…" hint) |
| UI-to-component mapping | The table + "Common Mistakes — do NOT use native HTML" section directly counters the most common LLM failure mode (falling back to raw HTML) |
| Fallback decision rule | "Does this control need server events?" → ZK `<div>` vs `<n:div>` is a sharp, teachable heuristic |
| Charts dependency gating | Check `pom.xml` → ask → drop feature if declined. Prevents generating uncompilable pages |
| Test corpus | `test/valid/` (real ZK bug-report files) and `test/wrong/` (known error classes) exist and the validator classifies all of them correctly |
| Cross-tool distribution | marketplace.json + gemini-extension.json + `.github/skills` symlink + `skills-lock.json` consumption verified in `zulwriter-showcase/` |

---

## 2. Findings

Severity: **P0** = wrong output or broken promise, fix immediately · **P1** = systemic risk / user friction · **P2** = hygiene.

### A. Correctness defects (P0)

**A1. `validate-zul.py` namespace injection corrupts files that start with a comment — confirmed bug. ✅ FIXED (2026-07-06).**
`inject_default_namespace()` ([validate-zul.py:94](skills/zul-writer/scripts/validate-zul.py#L94)) finds the "first element" with regex `<([a-zA-Z][\w.-]*)`, which also matches tag names *inside XML comments*. [content-tabbox.zul](skills/zul-writer/assets/content-tabbox.zul) starts with `<!-- … goes INSIDE <tabpanel>, … -->`; the regex matches `<tabpanel` in the comment, injects `xmlns` into the comment text, leaves the real root un-namespaced, and Layer 2 fails with the misleading "No matching global declaration available for the validation root." Any generated ZUL that begins with an explanatory comment — a very typical LLM output shape — will false-fail.
*Fix applied:* [validate-zul.py:146-165](skills/zul-writer/scripts/validate-zul.py#L146-L165) now pre-computes the text spans of comments (`<!-- ... -->`) and PIs (`<?...?>`) and skips any tag-match starting inside one, so injection lands on the real root. Verified: `content-tabbox.zul` now passes all 4 layers; `test/valid/*` and `test/wrong/*` classify identically to the pre-fix script (diffed via git stash) — no regression.

**A2. SKILL.md contradicts its own asset on `hflex="min"`. ✅ FIXED (2026-07-06).**
[SKILL.md:108](skills/zul-writer/SKILL.md#L108): "Don't specify `hflex="min"` on `<button>`" — but the "Good" example in [flexible-sizing.zul:4](skills/zul-writer/assets/flexible-sizing.zul#L4) is `<button label="Search" hflex="min"/>`. The model will see both and pick one at random. Decide which rule is true and align both files.
*Fix applied:* the asset's pattern is idiomatic (`hflex="min"` sizes a button to fit its label beside an `hflex="1"` field). Replaced the false SKILL.md prohibition with an accurate note that endorses the pattern and links to the asset.

**A3. `MyViewModel.java` — the primary MVVM template — does not compile. ✅ FIXED (2026-07-06).**
[MyViewModel.java](skills/zul-writer/assets/MyViewModel.java): missing `import java.util.List;`; imports MVC-only `org.zkoss.zk.ui.select.annotation.Wire` (unused, and actively misleading in an MVVM template); references an undefined `Item` class and undefined `loadItems()`. This violates the skill's own [controller-guidelines.md](skills/zul-writer/references/controller-guidelines.md) principles #1 (fully functional scaffold) and #3 (self-contained inner model classes). Rewrite it as a compilable scaffold with an inner `static class Item` and sample data.
*Fix applied:* rewrote as a self-contained compilable scaffold — added `java.util.List`/`ArrayList` imports, dropped the MVC `Wire` import, added an inner `public static class Item` and a `loadItems()` sample-data method with comment blocks per controller-guidelines. Verified: compiles with `javac` against the zkbind jars.

**A4. Component mapping recommends components that don't exist. ✅ FIXED (2026-07-06).**
[ui-to-component-mapping.md:45](skills/zul-writer/references/ui-to-component-mapping.md#L45) offers `<switch>` (no such ZK component — 0 hits in zul.xsd) and [line 68](skills/zul-writer/references/ui-to-component-mapping.md#L68) offers `<busyOverlay>` (also nonexistent; busy indication is `Clients.showBusy()` — a Java API, like the notification row correctly states). A user following the table gets a runtime `DefinitionNotFoundException`. Also: `<splitlayout>` and `<portallayout>` are zkmax (EE-only) but carry no edition note, while `<ckeditor>` correctly notes "requires ZK PE/EE" — mark editions consistently; it's a common real-world trap.
*Fix applied:* confirmed via ZK docs that `switch`/`toggle` are checkbox molds (no standalone `<switch>`); replaced the toggle-switch row with `<checkbox mold="switch">`/`<checkbox mold="toggle">`. Replaced `<busyOverlay>` with `Clients.showBusy()` (Java). Added "requires ZK PE/EE (`org.zkoss.zkmax.zul`)" notes to `<splitlayout>` (mapping) and `<portallayout>`/`<portalchildren>` (use-case-guidelines).

**A5. Broken reference link. ✅ FIXED (2026-07-06).**
[use-case-guidelines.md:50](skills/zul-writer/references/use-case-guidelines.md#L50) points to `references/charts-dependency.md`, which doesn't exist (actual file: `charts-guidelines.md`).
*Fix applied:* corrected the link to `charts-guidelines.md`.

**A6. Bundled assets fail the skill's own validation — dogfood results:** ✅ FRAGMENT FIXES DONE (2026-07-06); XSD false-positives deferred to B1.

| Asset | Result | Cause |
|---|---|---|
| content-tabbox.zul | ✗ Layer 2 | Bug A1 (comment eats xmlns injection) |
| example-data-management-mvvm.zul | ✗ Layer 2 | XSD false positive: `listboxType` demands item/listhead children, but a model-driven listbox with only `<template>` ([line 18–24](skills/zul-writer/assets/example-data-management-mvvm.zul#L18-L24)) is canonical MVVM |
| kanban-board.zul | ✗ Layer 2 | XSD false positive: shadow element `<forEach>` not allowed inside `<portalchildren>` |
| flexible-sizing.zul | ✗ Layer 1 | Multi-root fragment — not well-formed XML |
| form-validation-mvvm.zul | ✗ Layer 1 | Multi-root fragment |

The showcase gallery has the same problem: `zulwriter-showcase/src/main/webapp/enterprise-kanban.zul` fails on the same `<forEach>` false positive. When the skill validates its own examples as broken, the agent either wastes turns "fixing" correct code or learns to ignore validation failures — both bad.
*Fix:* wrap the two fragment files in `<zk>` (cheap, makes them valid standalone), and fix the XSD issues per B1.
*Fix applied (P0 portion):* wrapped `flexible-sizing.zul` and `form-validation-mvvm.zul` in `<zk>` — both now pass all layers; `content-tabbox.zul` passes via the A1 fix. The remaining two failures (`example-data-management-mvvm.zul`, `kanban-board.zul`) are XSD false-positives — deferred to **B1** (P1), not part of the A/P0 batch.

**A7. Small but user-visible defects. ✅ FIXED (2026-07-06).**
- [kanban-board.zul:44](skills/zul-writer/assets/kanban-board.zul#L44): `style="width:30px;height30px;…"` — missing colon in `height:30px`. → fixed to `height:30px`.
- [validate-zul.py:594](skills/zul-writer/scripts/validate-zul.py#L594): `--zk-version` help says "Layer 3 checks only run for version 10.x" — it actually gates **Layer 4**. → corrected help text to "Layer 4".
- [use-case-guidelines.md:36](skills/zul-writer/references/use-case-guidelines.md#L36): heading "### 3. simple List (MVC)" — lowercase. → capitalized to "Simple List".

### B. Validator & schema strategy (P1)

**B1. XSD maintenance is whack-a-mole; make it systematic.**
Git history shows reactive one-off patches: `d9e8da3` (fileupload in anyGroup), `92730d4` (toolbarType children), `4e1381a` (groupfoot in rowsType) — and this review found two more classes in one afternoon (shadow elements in container content models; template-only listbox/grid). Recommended strategy, in order of preference:
1. **Generate the XSD from ZK's source of truth** (the `lang.xml` / addon component definitions in the ZK jars) with a script committed to `tool/`. Hand-edits stop; regeneration is documented and repeatable. The XSD already carries a version stamp (`10.3.0.202512151211`) — keep that.
2. If generation is too costly now: **one systematic pass** instead of per-bug patches — add a `shadowGroup` (`forEach`, `if`, `choose`, `apply`) reference to every container content model, and make trailing "required children" choices optional (`minOccurs="0"`) for every model-driven component (listbox, grid, tree, combobox…), since MVVM templates legally replace static children.
3. **Add a regression corpus to CI** (see F1) so any future XSD edit is instantly checked against `test/`, `assets/`, and the showcase gallery.

**B2. ZK 9 support is claimed but not wired through.**
Step 1 detects the ZK version, but Step 3's command ([SKILL.md:136](skills/zul-writer/SKILL.md#L136)) never passes `--zk-version`, so ZK 9 projects get ZK-10-only compat noise (Layer 4 defaults to 10). And nothing checks the reverse — components/attributes that only exist in ZK 10 pass silently against a 10.3 schema for a ZK 9 target. Minimum fix: document `--zk-version <detected>` in Step 3. Better: add a small "new in ZK 10" blocklist to Layer 4 when `--zk-version 9`.

**B3. Fragment validation.**
ZUL fragments with a non-window root are legal (used via `createComponents`/`<include>`), and Layer 2 can only validate roots declared globally with a namespace. Since the validator already injects the namespace, also wrapping input in `<zk>…</zk>` when the root isn't `<zk>` would make every fragment validatable and kill a whole class of false failures.

**B4. Dependency bootstrap is fragile outside this machine.**
`ensure_lxml()` runs `uv pip install lxml`, which errors ("No virtual environment found") on machines without an active venv, then falls back to `pip install`, which fails on PEP-668 externally-managed Pythons (Homebrew/Debian defaults). Elegant fix matching your uv preference: add PEP 723 inline metadata to the script (`# /// script\n# dependencies = ["lxml"]\n# ///`) and document `uv run …/validate-zul.py` as the primary invocation, keeping `ensure_lxml()` as fallback. Also note `python3` doesn't exist on typical Windows installs — mention `python` as alternative in SKILL.md.

### C. Workflow & agent-UX gaps (P1)

**C1. Step 1 questioning needs "skip what you know" and batching rules.**
Six question topics are listed, but nothing says: (a) skip questions already answered by the user's request or resolvable from the project (version from pom.xml is covered; purpose/layout often inferable from a screenshot too — ironic given the Visual Analysis entry point); (b) batch remaining questions into a single prompt (interactive UIs cap at ~4 questions per ask); (c) what to assume when running non-interactively (reasonable default: follow existing project pattern — if the codebase already has ViewModels, use MVVM; state assumptions in output). Today the skill can generate a 6-question interrogation for a request that already contained the answers.

**C2. No file-placement guidance.**
Nothing tells the agent where output belongs in a Maven/Gradle webapp (`src/main/webapp/**.zul`, `src/main/java/<package>/**.java` matching the `viewModel`/`apply` FQCN). The showcase runs got this right by luck/context. One short subsection prevents files landing in the repo root.

**C3. No anti-pattern guardrails for classic LLM ZUL mistakes.**
The mapping file covers HTML fallback misuse well, but SKILL.md never says: avoid `<zscript>` and inline Java in event attributes for production pages (LLMs love these — they're all over old ZK forum/demo content that models trained on); don't put `apply` and `viewModel` on the same component (the checklist implies it only via "no mixing"). A 4–5 bullet "Do not generate" list in Step 2 is cheap and high-yield.

**C4. Step 4 has no verification loop.**
Steps 2–3 follow generate→validate, but the generated Java controller is never verified (contrast with your own Goal-Driven Execution principle). Add: "If the project builds with Maven/Gradle, compile the generated class (`mvn -q compile` or `javac` with the ZK jars on classpath); fix errors before finishing." Where no build is available, at minimum re-read the ZUL and cross-check every `@command('x')` / `@Wire` id against the generated class — a regex-level check the agent can do without tooling. (A future validator Layer 5 could automate ZUL↔controller cross-checking.)

**C5. Actionability gaps.**
- Theme suggestion ([SKILL.md:88](skills/zul-writer/SKILL.md#L88)): suggests `iceblue_c` but gives no way to enable it (theme jar dependency + `org.zkoss.theme.preferred` library property). The agent can't act on its own advice.
- [SKILL.md:105](skills/zul-writer/SKILL.md#L105) says "Query `zk-doc-mcp-server`" — the actual MCP server is named `zk-doc` (tool: `search_zk_docs`). Name it correctly and keep the "if available" qualifier.
- [SKILL.md:139-141](skills/zul-writer/SKILL.md#L139-L141) uses `/Users/hawk/...` as the example path — swap for a neutral `~/.claude/skills/zul-writer` before publishing.

### D. Telemetry & privacy (P1)

The tracking feature (uncommitted: [track-usage.py](skills/zul-writer/scripts/track-usage.py) + SKILL.md edit) works, but as designed it will surprise users:

1. **Disclosure lives in the wrong place.** README.md discloses analytics, but `npx skills add` installs only the skill directory — end users never see README. Put a one-line disclosure in SKILL.md itself (frontmatter or a "Telemetry" footnote): what is sent (skill name + version), what is stored (`~/.zul_writer_visitor_id`, a random pseudonymous ID), and how to opt out.
2. **Reword "silently … do not show output to user".** Instructing the agent to hide an outbound network call reads as concealment (and fails the skill-spec "principle of lack of surprise"). Claude Code will surface the Bash call in a permission prompt anyway. Say instead: "Run the anonymous usage ping (see Telemetry note) in the background; if the user declines the command, continue the workflow normally — never retry or block on it." The "continue if denied" clause also fixes a real failure mode: a denied permission prompt is currently the very first thing this skill does.
3. **Honor `DO_NOT_TRACK=1`** (the console DNT convention) in the script — 3 lines, big goodwill.
4. **Version drift:** `"1.0.0"` is hardcoded in the payload and User-Agent, duplicating SKILL.md `metadata.version` and marketplace.json. See E1.
5. **Make it actionable (optional):** the ping carries no dimensions. Adding non-PII params (pattern=mvc|mvvm, entry=text|image, zk_version, validation passed/failed) would turn a vanity counter into data that guides skill improvements. Update the README privacy note accordingly if you do.

### E. Distribution & repo hygiene (P2)

- **E1. Version in 3+ places:** SKILL.md `metadata.version`, marketplace.json, track-usage.py payload, gemini-extension.json. Add a release checklist to CLAUDE.md, or generate/check consistency in CI.
- **E2. marketplace.json is stale:** says "structured **3-step** workflow" (it's 4), and `homepage` is still the `https://github.com/your-org/agent-skill` placeholder.
- **E3. CLAUDE.md references scripts that don't exist:** `install-skill.sh` and `link-skill.sh` are gone from the repo, but CLAUDE.md (loaded every session, and shipped as GEMINI.md via `@CLAUDE.md`) still instructs running them. Also note: `~/.claude/skills/` currently has **no zul-writer symlink**, so the skill isn't triggerable in Claude Code on this machine — probably why testing has been happening through `zulwriter-showcase/.agents/`. Restore the script (or document `npx skills add` as the canonical local install) and re-link.
- **E4. `.DS_Store` files are inside the skill directory and not gitignored** — they ship with any packaging. Add `.DS_Store` to `.gitignore` and remove tracked copies.
- **E5. `license: MIT` is declared but there is no LICENSE file** in the repo root.

### F. Quality infrastructure — the biggest leverage (P1)

**F1. CI regression net (small effort, immediately stops the P0 class from recurring).**
A GitHub Action that runs on every push:
```
validate test/valid/**      → must all PASS
validate test/wrong/**      → must all FAIL
validate skills/zul-writer/assets/*.zul → must all PASS
validate zulwriter-showcase/src/main/webapp/*.zul → must all PASS
```
This makes assets/showcase a living regression corpus for both the validator and the XSD. Every finding in section A6 would have been caught at commit time.

**F2. Skill-level evals.**
There are validator tests but no evals of the *skill as a whole* (does the agent, given the skill, produce better pages than without it?). Create `skills/zul-writer/evals/evals.json` with 4–6 realistic prompts — e.g. MVVM form page, dashboard from a screenshot, ZK 9 project (checks `--zk-version` wiring), kanban board (checks shadow-element handling), chart page in a project *without* zkcharts (checks the decline path) — with assertions like "validator passes", "no `<zscript>`", "controller compiles", "correct file locations". The skill-creator tooling in this repo's toolchain can run with-skill vs. baseline comparisons and produce a review UI. This is the loop that turns user feedback into measured improvement instead of anecdote.

**F3. Trigger/description optimization.**
The current description covers *creating* pages and image conversion, but the skill is also the best tool in the house for **validating or fixing an existing ZUL** — a query like "why does my .zul throw at line 40" or "add a column to this listbox" won't reliably trigger it. Extend the description ("…also use when validating, debugging, or modifying existing .zul files…") and, when convenient, run the description-optimization loop (20 should/shouldn't-trigger queries) to tune it empirically.

---

## 3. Prioritized Roadmap

| # | Item | Findings | Effort |
|---|---|---|---|
| **P0 — this week (≈1 day total)** | Fix namespace-injection bug; align `hflex="min"` rule; rewrite MyViewModel.java to compile; remove `<switch>`/`<busyOverlay>`, add EE notes; fix broken charts link; wrap fragment assets in `<zk>`; fix kanban typo & `--zk-version` help text; sync marketplace.json | A1–A7, E2 | S |
| **P1 — next (≈1 week)** | Systematic XSD pass (shadow elements + model-driven children) or generator script; CI regression workflow; wire `--zk-version` into Step 3; Step 1 skip/batch/default rules; file-placement + anti-pattern sections; controller verify step; telemetry disclosure + DO_NOT_TRACK + "continue if denied"; PEP 723 / `uv run` for validator | B1–B4, C1–C5, D1–D5, F1 | M |
| **P2 — after** | Skill-level evals + description optimization loop; telemetry dimensions; version-sync check; LICENSE file; restore install script & local symlink; .DS_Store cleanup | F2, F3, D5, E1, E3–E5 | M |

Suggested sequencing note: do F1 (CI) *before* the big XSD pass in B1 — the regression net is what makes schema surgery safe.

---

## 4. Verification Criteria (definition of done)

- `python3 scripts/validate-zul.py` over `assets/*.zul` and `zulwriter-showcase/src/main/webapp/*.zul` → 100% pass; `test/wrong/*` → 100% fail. Enforced in CI.
- `MyViewModel.java` and `KanbanViewModel.java` compile against ZK 10 jars.
- Grep gate: no `charts-dependency.md`, `<switch>`, `<busyOverlay>`, `your-org`, or `/Users/hawk` strings anywhere in `skills/zul-writer/` or marketplace.json.
- A fresh machine (no venv) can run the validator via the documented command.
- SKILL.md contains the telemetry disclosure; `DO_NOT_TRACK=1` suppresses the ping (verifiable with `TRACK_URL` pointed at a local listener).
- Eval suite runs green with-skill and shows measurable delta vs. baseline.
