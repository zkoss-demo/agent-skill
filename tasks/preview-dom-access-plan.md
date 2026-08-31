# Plan: give the AI the rendered DOM during preview

**Status:** implemented on `feat/preview-dom-probe`. See §8 for what changed on contact with reality.
**Motivates:** [zul-writer-dom-access-gap.md](zul-writer-dom-access-gap.md), findings 3/4/6 and three
anecdotes in [zul-writer-eval-findings.zh-TW.md](zul-writer-eval-findings.zh-TW.md).

---

## 1. Prior-art search: nothing exists for the AI path

| Searched | Result |
|---|---|
| `skills/zul-writer/**` (SKILL.md + 5 references + both scripts) | no `--dump-*`, no `outerHTML`, no mention that a rendered DOM is inspectable |
| `agent-skill/tasks/**`, `zulwriter-showcase/*.md` | nothing; `git log -S "outerHTML" --all` and `-S "Rendered HTML"` are both empty |
| `zkidea/doc/**`, `zkidea/tasks/**` | **FR-23 "View Rendered HTML"** — shipped, but IDE-only: a right-click item that opens a read-only editor tab for a human |
| `zkidea/tasks/zul-preview-agent-skill-plan.md` (the plan that produced `preview-zul.py`) | zero matches for `FR-23`, `rendered html`, `context menu`, `devtools` — the port was never considered |
| `zk-preview-launcher/README.md` + `src/**` | serves `GET /<path>.zul → 200 text/html`; no diagnostic endpoint, no DOM concept (the launcher has no browser) |

So: **the capability was built for the human and never for the agent.** This plan is the port.

---

## 2. What was measured before designing anything

Prototyped by patching a scratch copy of `preview-zul.py` (`page.content()` + a computed-style
`evaluate` after the screenshot) and running it against real pages.

### 2a. Size — the constraint that shapes the whole design

| Page | `.zul` | Served HTML (launcher) | **Post-mount DOM** |
|---|---|---|---|
| `healthy-page.zul` | 2.2 KB | 2.3 KB | **2.4 KB** |
| icon probe (4 widgets) | 0.3 KB | 1.6 KB | **1.7 KB** |
| `app-tracker.zul` — real dashboard, controllers executed | 14.5 KB | 18.8 KB | **24.4 KB** (~6k tokens) |
| grid, 200 rows × 6 cols | 39 KB | 81 KB | **231 KB** (~58k tokens) |

A typical generated UI page is ~24 KB of DOM — affordable. A data table is **10× that**, and data
tables are exactly what this skill generates. **Conclusion: the full dump must go to a file, never to
stdout.** A flag that is safe on four pages and blows the context window on the fifth is worse than
no flag.

### 2b. Markup alone does not answer the question — computed styles do

The single most expensive defect in the eval (finding 4: `z-icon-*` on `<label>`, hit in 3/6 runs,
**misdiagnosed in all three, three different ways**) was reproduced and probed:

```
<label sclass="z-icon-bell"/>  →  <span class="z-icon-bell z-label">
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif    ← WRONG
    ::before content: "\f0f3"      ::before font-family: "Helvetica Neue", …
    rect: 8 × 18

<span sclass="z-icon-bell"/>   →  <span class="z-icon-bell z-span">
    font-family: ZK85Icons, FontAwesome                            ← right
    ::before content: "\f0f3"      ::before font-family: ZK85Icons, FontAwesome
    rect: 14 × 16

<div sclass=…> and <button iconSclass=…>  →  identical to <span>
```

Root cause, settled in **one** render: `.z-label` sets an explicit `font-family` that outranks the
icon rule, so `::before` asks for glyph `\f0f3` in a text font and the browser draws tofu.

Two consequences for the design:

- **`content` is identical on all four carriers.** A markup-only dump would have shown four elements
  each carrying `z-icon-bell` and proved nothing. **The probe must carry computed styles.** This is
  measured, not assumed — and it is why "just give me the HTML" is not sufficient as specified.
- The failing element is `8px` wide against `14px` for the working ones. Machine-comparable.

### 2c. The launcher's own HTML is nearly worthless for this

The user's framing was "get the HTML from the Preview Launcher". Measured, that channel is not the
one that pays. The served response for the icon probe contains **zero** occurrences of the class
`z-icon-bell` as an HTML class; its entire widget payload is:

```js
zkmx([… ['zul.wgt.Label','rVvH1',{sclass:'z-icon-bell'},{},[]],
        ['zul.wgt.Span', 'rVvH2',{sclass:'z-icon-bell'},{},[]], …])
```

That is **the .zul restated as JavaScript** — the agent already has the .zul. It answers exactly one
question the DOM answers less directly (*did the server create this component at all, with these
properties* — useful when a Composer builds children conditionally or `if=` evaluated false), and
nothing about why anything looks wrong. Everything of diagnostic value is created client-side.

**So the artifact to expose is the post-mount DOM from the browser phase, which `preview-zul.py`
already holds and currently throws away** — it runs `page.evaluate()` against that very DOM twice
already ([preview-zul.py:1871](../skills/zul-writer/scripts/preview-zul.py#L1871) layout audit,
[:1888](../skills/zul-writer/scripts/preview-zul.py#L1888) ZK error box). No launcher change is
needed, and none is proposed.

---

## 3. Design

Two flags. Neither changes a single byte of stdout on a run that does not pass them — that property
is what keeps the existing contract, Layer A's 20 cases, and every downstream reader intact.

### 3.1 `--probe <css-selector>` — the primary channel

Bounded, targeted, stdout. Pairs with the locators `LAYOUT:` already prints, so a finding and the
means to inspect it arrive in the same idiom.

```
PROBE: 4 matches for [class*="z-icon-bell"]
  - <span id="rVvH1" class="z-icon-bell z-label"> | 8x18 @ (20,20)
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif | display: inline-block
    ::before content: "\f0f3" | ::before font-family: "Helvetica Neue", Helvetica, Arial, sans-serif
```

- **Style set (fixed, not configurable):** `display`, `font-family`, `color`, `background-color`,
  `overflow`, `width`, `height`, `flex`, `position`, plus `::before` `content` and `font-family`.
  Chosen from the defects the eval actually produced: icon tofu (font-family/::before), the flat-grey
  leftover flex space R6 sampled with an eyedropper (background-color), `hflex="min"` under-measuring
  (width/flex), clipped text (overflow/width).
- **Caps:** 10 matches, `outerHTML` truncated to 200 chars, `… and N more` tail — the same
  truncation idiom `LAYOUT:` and `WARNINGS:` already use.
- **Repeatable:** accept `--probe` more than once.
- Runs **after** the screenshot and inside the same `contextlib.suppress` discipline as the audit: a
  bad selector must never fail a good render. An unmatched selector prints `PROBE: 0 matches for …`,
  which is itself an answer ("your component is not in the DOM at all").

### 3.2 `--dump-dom [path]` — the escape hatch

`document.documentElement.outerHTML` to a **file**. Default path mirrors `--report json`: beside the
PNG with `.dom.html`. stdout gains exactly one line, `DOM: <path>`, right after `SCREENSHOT:` (both
are artifact paths). The agent greps the file; it never reads it whole. §2a is the reason this is a
file and not a block.

### 3.3 Where the code goes

All of it inside `capture()`, after the screenshot is on disk, beside the two existing
`page.evaluate()` calls — so nothing evaluated can alter the image it explains. `--report json`
gains `probe` and `domDump` keys under the same "adds no information the text lacks" rule. Exit codes
are untouched: neither flag can fail a render.

### 3.4 Rejected

| Option | Why not |
|---|---|
| Full DOM to stdout | 231 KB on a data table (§2a) |
| A launcher endpoint returning HTML | the launcher has no browser; its HTML is the ZUL restated (§2c) |
| Selector-configurable style list | one more thing to get wrong; the fixed set covers every defect the eval produced |
| Re-render to probe | the DOM is already in hand; a second render is the waste this whole plan exists to remove |

---

## 4. The skill change, which is not optional

The eval's plainest lesson is that **agents do not use what they are not told about** — six runs each
independently invented "copy the project convention" because the skill never sanctioned it, and three
runs guessed at the icon cause rather than looking. Shipping the flags without the prose reproduces
that failure.

Add to SKILL.md Step 5, and to `references/preview-guidelines.md`:

> **When the image shows something is wrong but not why, probe — do not re-render.** An empty box, a
> component you cannot find, a colour you did not ask for, a width that is not what you set:
> `--probe '<selector>'` answers all four from the render you already have. Re-rendering to look
> harder at the same PNG is the wrong move.

And narrow Step 5's "What you cannot judge from this image" disclaimer, which currently absorbs real
defects (eval finding 4: R2 quoted it to classify a one-word fix as an unfixable preview artifact):

> An empty box where an icon should be is **not** a missing-resource artifact. Probe it: if
> `::before content` is set but `font-family` is not the icon font, the carrier element is wrong —
> `z-icon-*` belongs on `iconSclass` or a plain container, never on `<label>`.

---

## 5. Test plan (Layer A, `test/run-preview-tests.py`)

| # | Case | Assert |
|---|---|---|
| 1 | no flags | stdout **byte-identical** to today — the whole safety argument |
| 2 | `--probe` matching | `PROBE:` block, match count, the style keys present |
| 3 | `--probe` matching nothing | `PROBE: 0 matches`, exit 0 |
| 4 | `--probe 'a b ((('` (malformed) | exit 0, render unaffected |
| 5 | `--dump-dom` | file exists, non-empty, `DOM:` line names it, PNG unchanged |
| 6 | `--dump-dom` on the error page (exit 1) | no dump, or an explicitly-labelled one — never silently the launcher's own error markup |
| 7 | icon fixture + `--probe` | the `z-label` font-family differs from `z-span` — pins §2b as a regression |

Case 7 needs `icon-probe.zul` promoted into `preview-fixtures/` as a permanent fixture.

---

## 6. Scope

**In:** `preview-zul.py`, SKILL.md Step 5, `preview-guidelines.md`, Layer A cases, one fixture.
**Out:** the launcher (no change needed), the IntelliJ plugin, `validate-zul.py`, the JSON report
schema beyond two additive keys.

**Effort:** ~150 lines of Python, ~30 lines of prose, 7 test cases. The prototype that produced every
number in §2 was ~20 lines, so the mechanism is proven; the work is the contract, caps and tests.

---

## 7. Decisions needed before implementation

1. **Both flags, or `--probe` only first?** `--probe` carries the measured value; `--dump-dom` is
   insurance for "I do not know what selector to ask for". Shipping only `--probe` is defensible.
2. **`DOM:` after `SCREENSHOT:`, or last before `REPORT:`?** Both are additive-only; this is a
   readability call.
3. **Does this land in the skill's next release, or wait for a launcher release?** It needs no
   launcher change, so it can ship independently — worth confirming, since the two have been
   versioned together so far.


---

## 8. Implementation notes

Built on `feat/preview-dom-probe`, in a `git worktree` parallel to the session working on
`feat/zul-preview-agent-skill` — the two branches touch the same four files, so they cannot share a
working tree.

**Four deviations from §3, each forced by something the plan could not know.**

1. **`--dump-dom` takes no value.** §3.2 specified `--dump-dom [<path>]`. Layer A caught what that
   costs: `--dump-dom page.zul` — how anyone would type it — makes argparse hand the `.zul` to the
   flag as its path, leaving the positional empty and killing the run at exit 3. An optional value
   reads well in a help text and is a trap on a command line whose last token is a path. The path is
   now always the PNG's with a `.dom.html` suffix; `--out` places the pair.
2. **The `::before` glyph is escaped.** The first working version printed `content ""`: an icon's
   codepoint is private-use, so raw it is invisible in a terminal — turning the one line that proves
   *the glyph was requested* into apparent proof that it was not. It now reads `"\uf0f3"`.
3. **The fixture is `icon-carrier.zul`, not `icon-probe.zul`.** Every other fixture is named for the
   phenomenon it pins (`layout-clipping`, `client-error-box`), not for the tool that reads it.
4. **The skill `description` gained a trigger clause** — "work out why a rendered page looks wrong".
   §4 argued the prose is not optional because agents do not use what they are not told about; the
   same argument reaches the frontmatter, which is what decides whether the skill is consulted at
   all. This widens triggering, so it is the one change here worth a second opinion.

**Verified, not assumed.**

| Claim | How |
|---|---|
| stdout byte-identical without the flags | `git show HEAD:…preview-zul.py` run against the modified one over `healthy-page`, `layout-clipping`, `render-error`; stdout diffed, exit codes compared |
| the whole CLI contract still holds | Layer A, 26 checks (23 existing + A18/A18b/A19) |
| the icon rule is real and load-bearing | A18b asserts the two carriers request the **same** glyph and only one gets the icon font — a probe reporting markup alone would show four elements carrying `z-icon-bell` and prove nothing |
| error page, malformed selector, JSON report | exercised individually and folded into A18/A19 |

**Not done, and deliberately:** no launcher change (§2c — its HTML is the `.zul` restated), and no
`--probe` style-set configurability (§3.4).
