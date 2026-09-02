# Decision log

Settled decisions and deliberate non-goals, each with the alternative that was rejected and why.
Recorded so that a future change to any of them is a conscious reopening rather than an accident.

Numbering (`D…`) is the original numbering from the working documents; gaps are decisions that were
only ever recorded in passing.

---

## Skill behaviour

### D16 — A one-sided project convention may override the pattern default · **decided: B**

When Step 1 cannot ask whether a page should be MVC or MVVM, the default is MVC. All six evaluation
runs independently invented a third path — copy the project's existing pages — which the skill never
sanctioned, and which fails the moment the project is inconsistent (this repo is: 12 MVC, 11 MVVM).

Chosen: count the project's own signal and follow it **only when it is one-sided**, otherwise fall
back to MVC and say so. Implemented as `scripts/detect-pattern.py`, used at question 3 only.

- **Rejected (A): the default is absolute, never look at the project.** Cheaper — no script — but an
  all-MVVM project gets one MVC page added to it.
- "One-sided" is defined as **zero on the other side**, not as a percentage threshold. Any percentage
  is an invented number, and a mixed project falls back to MVC either way; the only difference is
  whether the report says "this project is MVC" or "this project is mixed, so I used the default".
  The second is the true one. 6-to-2 is still `mixed`.
- The script reads **the ZUL side only**. Java-side signals lie: a ViewModel is a plain POJO and
  `@Init` is optional (this repo has ViewModels with none), so counting `@Init` under-counts; counting
  `Composer` subclasses over-counts, pulling in base and utility classes never applied to a page.
- One special case: `apply="org.zkoss.bind.BindComposer"` counts as **MVVM**. It is MVVM's own binder,
  and reading it as MVC inverts the conclusion. `test/valid/zk-5696.zul` uses exactly this form.
- The script prints filenames, not just counts, deliberately: **the script supplies facts, the agent
  still draws the conclusion**, and the user can check it.

### D17 — `<charts>` is exempt from the literal first pass · **decided: A**

A chart has no literal form in markup, so "write the data in, then take it out" cannot have a first
pass for it. Chosen: the chart block goes straight into the controller and is judged with
`--run-controllers` from the first render; the rest of the page still takes the literal pass.

- **Rejected (B): a same-size placeholder box first.** If the placeholder's height differs from the
  real chart, the layout has to be judged twice.
- Stated cost: that page's first render now depends on the controller compiling. Combined with §18 of
  [zk-measured-behaviour.md](zk-measured-behaviour.md) — a stale `.class` and "the chart never drew"
  look identical — so read `CONTROLLERS:` before diagnosing a missing chart.

### D18 — Literal-beside-model detection lives in `preview-zul.py` · **decided: C**

- **Rejected (A): prose only.** Abandons the one mechanism that can catch it.
- **Rejected (B): a `validate-zul.py` Layer 3 rule.** Catches the ZUL side (`model=` beside literal
  children) but is structurally blind to MVC, where `setModel()` is in Java and the ZUL shows nothing
  but literal children.
- Chosen (C): `--run-controllers` holds both the ZUL source and the rendered DOM, so the signal
  *"the ZUL declares a literal but the DOM does not contain that text"* does not care where
  `setModel()` was written and covers both patterns.
- C was the only option requiring an experiment first, and the experiment changed the design: paging,
  collapsed tree nodes and unselected tabpanels are genuine false-positive sources; virtual scrolling
  is not. Two guards clear all three. Measurements in
  [zk-measured-behaviour.md](zk-measured-behaviour.md) §2–3.
- Contract test A25 deliberately runs the same fixture **twice**, because the defect exists in only one
  of the two modes: in isolated mode the composer never ran and the literals did render, so reporting
  then would be a lie. **A rule that fires in both modes is reading markup while claiming to measure.**

### D21 — The fix-round cap becomes a three-layer rule · **decided: A**

The old rule — "at most two fix rounds, three renders total" — was a policy number no measurement ever
supported. Renders per run were 4, 3, 3, 3, **10**, 5, and **every overrun was the agent deciding the
extra round was worth it**, not the agent miscounting. A cap that most complex pages break is not a
cap; it is a number the agent has to decide whether to ignore.

The root problem is that one total cannot distinguish two opposite causes:

- **(a) the page genuinely has many independent defects.** Each round closes some; the list keeps
  shrinking. Blocking it ships a defective page.
- **(b) one defect the agent does not understand, re-guessed each round.** Each round edits the markup
  and the defect survives. This is the "blind, endless fixing" the cap was meant to stop — and every
  extra round only raises the chance of breaking markup that was already correct.

Chosen three layers, each blocking a different failure:

1. **At most two edits to the same defect.** Two consecutive ineffective edits mean the causal model is
   wrong; a third edit changes the markup, not the defect. Go and diagnose instead — diagnosis costs no
   rounds — and returning with a measurement does not count as a third guess.
2. **A round is worth running only if the last one closed at least one defect and added none.** The
   mechanically detectable half is checked against `LAYOUT: N findings`, printed on every render, not
   against memory. Same shape as the diagnosis stopping rule: *if the next render will not tell you
   anything the last one did not, stop.*
3. **A hard cap per pass, as a backstop rather than a target** (see D22).

Plus three things the skill had never said: **revert** a round that broke the page and stop; **report**
how many rounds were used and what is left open; and Pass 1 (literal layout) and Pass 2 (extraction)
each get their own budget, because their defect causes differ.

- **Rejected (B): per-defect cap only, no page-level number.** Closest to blocking (b) without blocking
  (a), but pages whose defects interact could run forever — close one, create one, repeat.
- **Rejected (C): keep one number, change 2 to 4.** A one-line change that also doubles the budget for
  blind re-guessing, and does not address the fact that one number cannot tell (a) from (b).

Also confirmed effective and kept: **a defect that survives two rounds stops the agent, which reports
rather than continuing**. One run refused to ship a speculative fix it could not verify by render, and
said why, under the pressure of having already spent its rounds.

### D22 — The hard cap is 4 rounds per pass · **decided: A**

Covers every observation (max ~3 after diagnosis is excluded) with one round of headroom, so a normal
page never reaches it and reaching it is itself a finding worth reporting.

- **Rejected (B): 5 per pass** — two rounds beyond any observation, so effectively never fires.
- **Rejected (C): 3 per pass** — zero headroom; exactly the pages that were observed at ~3 would catch
  on it, reproducing "the agent must ignore this number".

### Deliberately not built: a render counter in the script

The script could hash the input file, count renders in its cache and print
`RENDER: 3rd of this file (2 since last edit)`, turning "how many rounds have I spent" from the agent's
memory into a fact.

**Not doing it, for now.** There is no evidence any agent ever miscounted — every overrun was
"I judged this worth it". The cost is real: cross-invocation state and cache writes. The half of layer 2
that needs a fact already has one, printed on every render (`LAYOUT: N findings`). Applying the
facts-from-scripts principle here would be applying it for its own sake. Revisit if a genuine miscount
is observed.

---

## Tooling and release

### D19 — `detect-pattern.py` sends no usage ping · **decided: A**

`validate-zul.py` and `preview-zul.py` each send one anonymous ping. The new script does not.

This is not a code question (~10 lines) but a **metric-definition** one: one skill run currently emits
two events. A third emitter makes the same run emit three, and **the trend line breaks at the version
boundary in a way that looks like 50% growth**.

- Chosen (A): do not send. This script runs inside a skill run that two other scripts already reported.
  Cost: inconsistent with the "every script pings" convention, so a future maintainer may read it as an
  omission — the reason is written into the script's docstring.
- **Rejected (B): follow the convention.** Would require deciding what happens to the existing data —
  accept the discontinuity, or add a source field to the event.

### D20 — The skill version stays at 2.0.0 until the branch converges · **live constraint**

Several changes have landed (a `LAYOUT` rule, a new script, a whole Step 1 section) with the version
still 2.0.0. That is deliberate: remaining work touches the same files, so the version bumps once, at
convergence.

**Until then, do not touch either of the two places in isolation.** `SKILL.md` `metadata.version` and
`marketplace.json` must move together; changing one is drift. `gemini-extension.json` is a separate
version line and is not expected to follow — a mismatch there is not drift.

There were three places when this was written, because each script carried its own `SKILL_VERSION`
literal. They do not any more — see D21.

### D21 — `SKILL.md` is the version, and the scripts read it · **decided: B + D**

Four sites held `"2.0.0"`: `SKILL.md`, `marketplace.json`, and a literal in each of `validate-zul.py`
and `preview-zul.py`. The docs called it three by counting the scripts as one, which understated the
edit a release actually takes. The failure mode was silent: nothing errors when one is missed, the
usage endpoint simply receives a version that was never released.

- Chosen (B): `scripts/_skill_meta.py` reads `metadata.version` out of `SKILL.md`'s frontmatter, and
  both scripts import `SKILL_VERSION` from it. Four sites become two, and the file that declares what
  the skill is now also declares its version. Cost: the reported version depends on a documentation
  file being present and parseable beside the scripts, so the reader falls back to `"unknown"` rather
  than raising — reporting a version is never the job the user asked for, and a broken install showing
  up as its own bucket beats it vanishing from the counts.
- Chosen alongside (D): `test/run-version-consistency.py`, run first in CI. `marketplace.json`
  **structurally cannot** participate in B — it sits at the repo root, and `npx skills add`, a
  directory symlink and `.github/skills/` all ship `skills/zul-writer/` without it, so a script
  reading it would find nothing on every real install. The check is the only thing holding it in step,
  and it also fails if a `SKILL_VERSION` literal is ever written back into a script. The workflow's
  path filter gained `SKILL.md` and `marketplace.json`, without which the one job that catches version
  drift would never run on the commit that causes it.
- **Rejected (C): read from `marketplace.json`.** Same reason it cannot participate above.
- **Rejected (A alone): a shared module holding the literal.** Two lines, but it leaves the version
  duplicated against `SKILL.md` — three sites instead of four, and the file declaring the skill still
  not the one declaring its version.

The `sys.path.insert` before each import is not decoration: `PYTHONSAFEPATH=1` (and `python -P`) drops
the script's own directory from `sys.path`, and without the line the import fails there and takes the
whole run with it. Measured, not assumed.

### D15 — the `LAUNCHER:` line must not claim an unverified version

How the asset-404 warnings should be read depends on which launcher build ran (see
[zk-measured-behaviour.md](zk-measured-behaviour.md) §15: static serving only exists from 1.0.3). The
line therefore reports a version only when it has been proven, never an assumed one.

### D9 — the DOM-probe branch was merged rather than choosing one half

Two branches attacked the same two passages of prose from opposite directions. The merge kept both
halves instead of picking one: the corrected attribution of the Step 5 disclaimer (the cause was the
preview server having no static-file handler, not a guessed docroot) *and* the manual discrimination
method plus the new *Icons* section in `ui-to-component-mapping.md`. Running the merged suite then
found two real defects that only the combined tests could reach.

### `--dump-dom` takes no value

Specified as `--dump-dom [<path>]`; the contract tests showed what that costs. `--dump-dom page.zul` —
which is how anyone would type it — makes argparse take the `.zul` as the flag's value, leaving the
positional empty and killing the run at exit 3. **An optional value reads well in a help text and is a
trap on a command line whose last token is a path.** The path is now always the PNG's, with a
`.dom.html` suffix; `--out` places the pair.

### The `--probe` style set is fixed, not configurable

Nine properties plus `::before` `content` and `font-family`, chosen from the defects the evaluation
actually produced. Configurability is one more thing to get wrong, and the fixed set covered every
observed defect. Also rejected: the full DOM to stdout (231 KB on a data grid), and a launcher endpoint
returning HTML (the launcher has no browser; its HTML is the `.zul` restated).

### The `::before` glyph is printed escaped

The first working version printed `content ""`. An icon codepoint is private-use, so raw it is
invisible in a terminal — turning the one line that proves *the glyph was requested* into apparent
proof that it was not. It now reads `""`.

### Fixtures are named for the phenomenon, not the tool

`icon-carrier.zul`, not `icon-probe.zul`; matching `layout-clipping`, `client-error-box`.

---

## Preview-pipeline defect triage

Four defects were raised against the preview pipeline from the six-run evaluation. Three were fixed in
`preview-zul.py`; the fourth was closed without a code change.

| # | Defect | Outcome |
|---|---|---|
| D1 | `clipped-text` false negative | **Fixed** — intersect all clipping ancestors, per axis ([measured §11](zk-measured-behaviour.md)) |
| D2 | screenshot taken mid JS animation | **Mitigated, never reproduced locally** ([measured §13](zk-measured-behaviour.md)) |
| D3 | `escapes-parent` reporting a constant, unactionable value | **Fixed** — judged a measurement artefact; the rule now requires ink in the clipped strip ([measured §10](zk-measured-behaviour.md)) |
| D4 | grey flex fill + `hflex="min"` under-measurement | **Closed: ZK product behaviour.** Neither the launcher nor the script needed a change ([measured §8, §9, §14](zk-measured-behaviour.md)) |

D3's judgement was the interesting one, because both answers were defensible: *(a) it is a real
overflow, so the message must name an actionable direction*, or *(b) it is a measurement artefact, so
the rule must stop reporting it*. (b) was chosen and written into the code, with a genuinely
overflowing companion fixture asserting the other half — **that is the difference between correcting a
rule and switching it off.**

Global constraints that survive all four and must hold for any future rule:

1. The `LAYOUT:` audit runs **after** the screenshot and must not mutate the page, so it can never
   alter the image it describes. Text is measured with `Range` precisely to avoid inserting nodes or
   writing styles.
2. The audit stays wrapped in `try/except`: **a bug in the audit must never fail a good render.**
3. The stdout block order is a contract — automation parses these lines. `LAYOUT` sits between
   `CONTROLLERS` and `WARNINGS`.
4. **Never truncate silently.** Print caps limit what is shown; `total` is always honest.
5. Every rule needs a regression fixture that fails before the fix and passes after.

---

## The preview capability set (P0–P3), and its non-goals

A requirements specification derived from one live `zul-writer` run drove seven changes across both
repositories. All of P0–P2 shipped; only `--watch` (P3) remains unbuilt. What is worth keeping is the
decisions, the product owner's rulings, and the non-goals.

**Product owner rulings, recorded verbatim in intent:**

| Question | Ruling |
|---|---|
| Should `--run-controllers` default on when the skill generated the controller in-session? | **Yes** — the script default stays off; `SKILL.md` passes the flag explicitly, so non-skill callers are unaffected |
| Should `LAYOUT` findings fail the corpus CI job, or only report? | **Report in normal runs, fail in CI** via `--fail-on-layout` |
| Ship `overlap` detection behind `--strict-layout`, or drop it? | **Drop it** for v1 — the one rule likely to produce false positives on ZK's absolutely positioned widgets (popups, tooltips) |
| Does `zk-preview-launcher` version independently of the IntelliJ plugin? | **No — both use the same version** |

**Fail soft is mandatory, not advisory.** With `--run-controllers`, a controller that throws, hangs or
cannot be loaded must not destroy the preview: retry once with isolation on, emit
`CONTROLLERS: failed → isolated` plus a warning naming the class and first cause, and **still deliver
the screenshot with exit 0**. The causes to degrade on rather than crash are all ordinary:
`ClassNotFoundException` (project not compiled), `NoClassDefFoundError` (Spring/JPA absent), an NPE from
a missing session or servlet context, and any controller exceeding the wall-clock budget.

**Always report which mode ran.** This is the requirement the run that motivated the spec cared about
most, because **Step 5's judging rules invert depending on the answer**: with controllers off, an empty
field is expected; with them on, an empty field is a real defect. Before this, three signals disagreed —
`CLASSPATH:` said the output roots *were* passed, a commit was titled "pass the project's compiled
classes to the renderer", and `SKILL.md` said composers are no-ops — and none of them was ground truth.

**Layout findings are findings, not errors.** Exit code stays 0. The audit must not mutate the DOM
before the screenshot, must run at the viewport the `SIZE:` line reports, and must stay under ~500 ms on
a typical page. Locator quality is a requirement in itself: `div#zk_comp_37` is useless to an agent, so
each node resolves through the client engine (`zk.Widget.$(node)`) to its ZUL id and widget class, giving
`label#fullName`, `a[label="Settings"]`.

**Closed, not deferred:**

- **`--widths 1280,768`** (render two viewports in one browser session) was **ruled out**. It needs a
  second `SCREENSHOT:`/`SIZE:` pair against a frozen block order; a second run with a different
  `--width` covers the need today.
- **`--user-agent`** was not built. Playwright already sends a real UA (observed in the rendered page as
  `HeadlessChrome/151.0.0.0`), nothing is blocked without it, and a new flag is a new surface on a frozen
  text-output contract.

### Non-goals for the whole preview capability

1. **No pixel or perceptual diff against the mockup.** It directly contradicts Step 5's own rule —
   *"judge structure, not pixels… never edit the ZUL for a cosmetic difference alone"* — and would flag
   sample-data differences as defects. A diff score would pull the agent into exactly the pixel-chasing
   the skill spends a paragraph forbidding. Structural findings deliver the safety without the trap.
2. **Not a real servlet container.** No session persistence across requests, no AU round-trips, no click
   simulation. **First paint is the contract.**
3. **No change to the IntelliJ plugin's defaults.** Every new capability is opt-in at the CLI.
4. **No new required network dependency at render time** beyond the one-off launcher download.

### A note on how that spec aged

The specification's own detection tables, JSON sketch and viewport guidance were each later annotated
*"read the code, not this table"* — five layout conditions, the console-capture premise, four JSON keys
and the whole `vflex` caveat were corrected by measurement, because the browser disagreed with the spec
and **the browser is the fact**. The corrections are preserved in
[zk-measured-behaviour.md](zk-measured-behaviour.md) §16–19; the authoritative descriptions live in
`references/preview-guidelines.md`.

Two acceptance criteria in that spec were also **not verifiable by execution**, and saying so is part of
the record: *"a run started from a 1600px mockup renders at ~1600px without being told to"* is a claim
about a future agent session, judged on the wording's imperativeness; and the console-capture criterion
about an unknown component cannot fire, because such a page fails at server parse and no client engine
ever boots.

---

## `zk-preview-launcher` static asset serving (1.0.3)

Requirements were specified against launcher 1.0.2 and implemented and verified in 1.0.3. The
component lives in the `zkidea` repository; only the decisions are recorded here.

**Why it mattered enough to specify:** see [zk-measured-behaviour.md](zk-measured-behaviour.md) §15 —
without it, a blank image carried no signal at all, and the blanket "ignore missing assets"
instruction that compensated for it was quoted to close a real bug.

**Security properties are requirements, not advice.** On 1.0.2 path traversal was impossible *by
construction*, because nothing read the filesystem for an arbitrary path. A static handler ends that
accidental safety. Hence: percent-decode **before** validating (so `%2e%2e%2f` is rejected on the same
code path as `../`); compare confinement on path *components*, not string prefixes (a docroot of
`/home/u/app` must not admit `/home/u/app-secrets/x`); `WEB-INF` / `META-INF` never served, case
insensitively, at any depth; no dotfiles; loopback bind only; and never a directory listing, which
would disclose a developer's working tree to anything that can reach the port.

**Never cache — and no `ETag` or `If-Modified-Since` either.** The caller re-renders the same URL while
editing files; a `304` produces exactly the stale-image failure the no-cache headers exist to prevent.

### Deliberate non-goal: symbolic links are followed

A symlink inside the docroot serves its target even when the target is outside the docroot. Measured on
1.0.3: a link to `/etc/passwd` returned 200 with all 9,196 bytes, and a link to the `/etc` **directory**
exposed the whole tree beneath it.

**Accepted, as a decision rather than an oversight.** The exposure requires someone to have placed an
escaping link inside the developer's own project directory, and the listener is bound to loopback, so
nothing off the machine can reach it. Asserted by a *characterisation* test so the boundary is pinned
rather than assumed.

> Implementers: this is the known and intended boundary of path confinement. **Do not add link
> resolution to "fix" a report of it without reopening this decision**, and do not quietly rely on the
> absence of links for any stronger claim.

Also out of scope, each for a stated reason: range requests (the consumer screenshots a first paint),
compression (everything is local), and rendering `.zhtml` as a page — it returns 404 today, and the one
firm requirement is that the static handler must never start returning it as *source text*. Either keep
it 404 or render it, but decide deliberately.
