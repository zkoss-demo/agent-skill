# Measured ZK, browser and launcher behaviour

Facts established by running something, not by reading docs or source. Each was expensive to obtain
and none of them is recoverable from this repository's code. Where a fact caused a rule, the rule is
named.

Environment for everything below unless stated: ZK 10.2.1 / 10.3.0.1 with the Iceblue theme,
`zk-preview-launcher` 1.0.2–1.0.3, Chromium via Playwright, JDK 17+.

---

## Component and markup behaviour

### 1. `z-icon-*` on a `<label>` never draws; three other carriers do

| Carrier | `::before` content | resolved `::before` font-family | box |
|---|---|---|---|
| `<label sclass="z-icon-bell"/>` → `span.z-label` | `""` | `"Helvetica Neue", Helvetica, Arial, sans-serif` | **8×18** |
| `<span sclass="z-icon-bell"/>` | `""` | `ZK85Icons, FontAwesome` | 14×16 |
| `<div sclass="z-icon-bell"/>` | `""` | `ZK85Icons, FontAwesome` | 14×16 |
| `<button iconSclass="z-icon-bell"/>` → `<i>` | `""` | `ZK85Icons, FontAwesome` | 14×16 |

Cause: `.z-label` sets an explicit `font-family` that outranks the icon rule
(`font-awesome.css.dsp` and `norm.css.dsp` both match at specificity (0,1,0), so the later `.z-label`
rule wins on source order). The `::before` then asks for glyph `\f0f3` in a text font and the browser
draws tofu. Font loading is entirely healthy — `ZK85Icons.woff/.ttf/.eot/.svg` and FontAwesome ship
inside the `zul` jar under `web/zul/less/font/`.

**All four request the identical glyph.** That is why a markup-only dump proves nothing and why
`--probe` reports computed styles. Rule: `icon-not-rendered` (`LAYOUT:`), plus the *Icons* section in
`ui-to-component-mapping.md`.

Cost of not knowing this: hit in 3 of 6 evaluation runs and **misdiagnosed all three times, three
different ways** — one run shipped a page whose every icon was an empty box.

### 2. A bound `model` silently discards literal children — including an empty model

Four configurations, one render each. All four: `STATUS: ok`, zero warnings.

| Configuration | Result |
|---|---|
| MVVM listbox: `model="@load(vm.items)"` + literal `<listitem>` | literals **gone**, 10 model rows shown |
| MVC listbox: literal `<listitem>` + `setModel(10 items)` | literals **gone** |
| MVC listbox: literal `<listitem>` + `setModel(empty list)` | literals **gone**, list entirely blank |
| MVVM grid: `model="@load(vm.items)"` + literal `<row>` | literals **gone** |

An earlier note recorded this as "unsafe", which reads like it throws. It does not — **it is silent
and looks correct.** The page renders perfectly, so a screenshot review cannot structurally catch it;
the ZUL keeps a line claiming to show a row it has never once shown, and the next person to edit that
line finds nothing responds. Same class as the icon defect: a defect invisible in the render.

Rule: `literal-rows-discarded`, two detectors — (A) ZUL-only, `model=` beside literal children,
fires even in isolated mode because the defect is in the source; (B) component present in the DOM but
not one of its literal strings arrived, which is the only way to see a `setModel()` written in Java.
Detector B requires the component to have an `id`, because `setModel()` reaches it through `@Wire`,
which is the ZUL id — no id, nothing to look up, and the rule stays silent rather than guessing.

### 3. Without a model there is no render-on-demand

The most-feared false positive turned out to be zero risk. Measured, all literals declared vs. present
in the DOM:

| Situation | declared | in DOM | false-positive source? |
|---|---|---|---|
| **60 literal rows in a 120px-high listbox (scrolls)** | 60 | **60, all of them** | **no** — scrolling is plain CSS overflow |
| listbox `mold="paging" pageSize="3"`, 9 literals | 9 | 3 (rows 1–3) | yes |
| grid `mold="paging" pageSize="3"`, 9 literals | 9 | 3 (rows 1–3) | yes |
| children under a collapsed `<treeitem>` | 1 | 0 (the collapsed parent row itself renders) | yes |
| `visible="false"` label | 1 | 1 (rendered, merely hidden) | no |
| listbox inside an unselected `<tabpanel>` | 2 | **0, and the whole listbox is absent** | yes |

An unselected tabpanel is an empty stub — `<div id="lDXF9" style="display:none"></div>` — with the
child component not in the DOM at all.

Two guards clear all three real sources: **the component must be in the DOM** (otherwise skip: cannot
judge, so do not judge), and **any surviving literal string means skip** (paging can only hide beyond
page one; a collapsed tree node cannot hide its own row). Residual risk, accepted: every literal of a
component falls under a collapsed container that itself carries no literal text. Hard to construct in
practice.

### 4. Four collapsible components mark themselves four inconsistent ways

Measured on `preview-fixtures/collapsible-state.zul`, ZK 10.3:

| Component | DOM marking |
|---|---|
| `groupbox` | `z-groupbox-collapsed` on the root when **collapsed**; nothing when open |
| `nav` | `z-nav-open` when **open**; nothing when collapsed |
| `detail` | `z-detail-open` when **open**, on `.z-detail-outer` — which is not the widget root |
| `treeitem` | `z-tree-open` / `z-tree-close` on the **toggle icon**, not on the item |

Two markings mean collapsed, two mean open, and one is not on the element itself. Reading DOM classes
means maintaining four conventions with two mutually inverted defaults — misread any one and the state
reports backwards. `STATE:` therefore reads widget properties (`_open` / `isOpen()`): one property
replaces four conventions, and a theme can change a class but not a property name.

Two `treeitem` traps, both found by measurement:

1. **A `Treeitem` has no DOM node of its own.** It shares a `<tr>` with its `Treerow`, and
   `zk.Widget.$(tr)` returns the *inner* `Treerow`. Scanning by widget root finds **no treeitems at
   all** — the first implementation reported six of eight components. Take `parent` from the row.
2. **There is no `getTreechildren()`** (measured: `undefined`). The signal for "can collapse" is
   whether the last child widget is a `Treechildren`; a leaf's last child widget is its own `Treerow`.

Also: ZK does not render the children of a collapsed branch at all, so state inside a collapsed node
cannot be listed. Not a defect — the block describes the page as it is, which is what the user sees.

### 4b. A bound `src` is deliberately not placeholdered

Every other binding renders as dimmed expression text under isolation, but `PlaceholderInjector` leaves a
non-literal bound `src` **unset** rather than writing its expression text. So an
`<include src="@load(vm.page)"/>` contributes **nothing** to the image — the whole section is simply
absent.

**This is documented behaviour, not a defect. The agent must not "fix" the missing section.**

### 5. The ZK 10 theme owns the mesh header

A grid's column titles go invisible / a listbox header becomes a solid primary-blue bar with white
text. Both are the same ZK 10.3 Iceblue default, `--zk-mesh-title-background-color`. The modern fix is
a **scoped CSS custom-property override**; one evaluation run tried to out-specify it with
`!important` and only half-won. Confirmed identical on a real Jetty, so it is not a preview artifact.
Found only via the zk-doc MCP; `ui-to-component-mapping.md` still contains no occurrence of "mesh".

### 6. `<charts>` rejects `sclass`; `<togglebutton>` does not exist in ZK 10

`<charts>` takes `className` / `zclass`. Both facts came from an agent reading the shipped
`assets/zul.xsd` before writing an unfamiliar component — a move the skill never suggests and that
therefore happened in 2 of 6 runs. See [knowledge-roadmap.md](knowledge-roadmap.md) §Tier 2.

### 7. A ZK `label` renders as an inline span, so `width=` does nothing

`width="80px"` on caption `<label>`s does not line values up. Wrap the captions in fixed-width
`<div>`s instead.

### 8. Excess flex space is painted flat grey — ZK product behaviour

Any ZK container given more flexible height than its content needs paints the remainder
`rgb(224,225,227)` rather than inheriting the page background. Sampled on both `<tree>` and `<grid>`,
and **identical on a real servlet container**. Workaround: do not hand a component surplus flexible
height; to push content to the bottom, use a separate spacer element.

### 9. `hflex="min"` under-measures, and the gap grows with item count

| `hflex="min"` `<hlayout>` | measured box | content actually needs |
|---|---|---|
| 2 items | 136px | 140px (4px over) |
| 6 items | 439px | 463px (24px over) |

Identical through the launcher and through a real Jetty with three extra seconds of settling, so the
"measurement happened before CSS applied" theory is **false** — it is ZK product behaviour. Observed
up to 128px short on dense text. Workaround: a CSS `min-width` floor on text-dense horizontal groups.
Note the `LAYOUT:` audit correctly reports the consequence as `clipped-text` — that is the audit
working, not a false positive.

The documented answer exists but is unreachable in practice: it sits at the bottom of
`font_awesome.md` — *"using `hflex="min"` with iconSclass may not get the desired result… add
`z-icon-fw`"*. A run framed its problem as layout, the answer lives under fonts, and it shipped a CSS
`min-width` hack it itself called "a blunt instrument, not a diagnosis".

### 10. A constant `escapes-parent` overflow is `height:100%` plus padding

Three status bars in parents differing only in height (34 / 52 / 64px) all reported **exactly 16px**
overflow. Cause is not the inline-block baseline theory that was first suspected: it is `height: 100%`
plus vertical padding under `box-sizing: content-box`, so the child's box is always *parent + padding*
and the overflow is constant. The one move the message invited — give the parent more room — can never
change it.

Judged a **measurement artefact**. `escapes-parent` now requires *ink* in the strip that gets cut (the
element's own background or border, its own text, or a painting descendant). A box edge crossing a
clipping boundary with nothing rendered behind it costs the reader nothing.

### 11. `clipped-text` must intersect *all* clipping ancestors

The false negative was not "no clipping ancestor" — there was one, it was returned, and it was the
wrong one. A roomy `overflow:hidden` box nested inside a narrow one made plainly cut text measure as
fitting. The nearest clipping ancestor is not what a text run is visible inside; **the intersection of
all of them is**, per axis.

Non-defect worth recording: a `<button>` whose label is wider than its width does not clip in Chrome —
the text overflows the border box and stays readable, so silence there is correct.

---

## Toolchain and harness behaviour

### 12. `wait_for_function` runs on the page's main thread

On a chart page the pipeline silently skipped its ZK-ready wait and reported *"zk client engine:
absent"*. The first diagnosis ("zkcharts is big, so `window.zk` is slow") was wrong: `zk.wpd` finished
at **499 ms** and `window.zk` existed at **2,507 ms**, both long before the `load` event at 6,321 ms.

A 20 ms probe showed the main thread blocked solid:

```
main-thread stalls over 250ms (chart-animation)
  at    609 ms  blocked for 2,578 ms
  at  3,187 ms  blocked for   930 ms
  at  4,569 ms  blocked for 1,965 ms
  at  6,534 ms  blocked for 4,575 ms   <-- the pipeline starts asking at 6,376 ms
```

The check could not observe a condition that had been true for four seconds. `ZK_READY` resolved
**34 ms** after `window.zk` once the thread freed. Fix: stop asking a question that needs the main
thread — whether a page carries a ZK client engine is read from the **HTTP response**, since every ZK
page fetches its engine from under `/zkau/` and the launcher's error page does not. The old code was
already burning 5.03 s on a check that then failed, so the corrected gate costs **+0.67 s**, not the
+3.5 s an earlier note claimed. Pinned by contract test A18, which asserts both halves.

### 13. Playwright's `animations="disabled"` does not cover JS animation

It handles CSS animations and transitions only. Highcharts (and therefore zkcharts) animates through
`requestAnimationFrame` onto SVG attributes, and per-series entry animation is **not** suppressed by
chart-level `setAnimation(false)`. Nothing in the wait sequence waits for JS animation:
`networkidle` watches the network, `fonts.ready` watches fonts, `ZK_READY` watches ZK mount.

zkcharts defers chart construction to `onSize` when either flex is set (`Charts.src.js:141-144`), so a
responsively-sized chart starts animating *after* ZK's sizing pass — after every wait the pipeline
knows about. A `width`/`height` chart settles before capture and shows nothing.

**Status: the symptom never reproduced locally.** 12 captures across 3 page shapes, byte-identical and
complete every time, both before and after the mitigation (`ANIMATION_OFF_JS` + a `_settle()` gate,
measured 260–350 ms, inside the 500 ms allowance). The mechanism is not in question; what R5 had that a
minimal fixture does not, still is. See [open-items](README.md#open-items).

### 14. The launcher renders pixel-identically to a real servlet container

Same `.zul`, same browser, same 1600×900 viewport, one path through
`preview-zul.py` + launcher 1.0.2, the other through `mvn jetty:run` with deliberately generous
waits. On a page combining `grid`, `tree`, `hlayout`, flexible sizing and theme defaults:
**0 differing pixels out of 1,440,000**, both files 35,921 bytes.

Direct evidence of render fidelity, and the reason two visual phenomena (§8, §9) could be attributed to
ZK rather than to the preview.

### 15. Launcher ≤1.0.2 served no docroot static file at all

Not images, not stylesheets, not scripts — only `.zul` pages and ZK classpath resources under
`/zkau/web/`. Five static files sitting inside the very directory passed as `--webapp`, at exactly the
requested paths, all returned 404. The failure was not path resolution; no handler existed.

Consequences while that was true: every image on every page was blank in the screenshot, so "an image
did not draw" carried no signal — a real broken path and a correct one looked identical. The skill
compensated with a blanket instruction to ignore missing assets, and **that instruction was then quoted
to close a genuine one-word markup bug as unfixable**, and a page shipped with every icon an empty box.

`1.0.3` implements static serving. **A blank asset is a real signal only from 1.0.3 up**, which is why
the `LAUNCHER:` line matters and must not claim an unverified version. Also fixed in 1.0.3: a `GET` for
a nonexistent `.zul` returned `200` with a zero-byte body, so a caller could not distinguish "page
missing" from "page rendered to nothing"; it now returns 404 and names the docroot in the body,
separating the two causes without a second request.

### 16. `zk.error()` never reaches the browser console

The obvious design — subscribe to `page.on("console")` and collect errors — cannot see ZK's own client
error reporting. `zk.error()` routes a complaint to `zk.debugLog` (console **only** under `zk.debugJS`,
which is off), optionally to the server, and then to an **error box appended to the page**.

So there are **two collectors**, not one: the console subscription for genuine
`console.error`/`console.warn`, plus a DOM read of that error box. Browser network-failure console
reports are filtered out deliberately.

A related trap in how this gets tested: a ZUL naming an unknown component fails at **server parse**, so
no client engine ever boots and there is no client-side complaint to surface. The case that actually
exercises this path is a page the server renders happily whose client engine complains anyway.

### 17. `vflex` and `--full-page` do not interact the way they appear to

Measured 2026-08-23 with a purpose-built probe. Three findings, each contradicting a plausible belief:

- **"A `vflex="1"` region legitimately ends at viewport height in a full-page capture" describes a
  situation that cannot occur.** For the document to be taller than the viewport, something must sit
  *below* the flex widget — and the moment it does, the flex widget resolves to **0**, not to viewport
  height. A root `<borderlayout vflex="1">` with a 1400px sibling measured **1590×0**, and the layout
  audit correctly reported `zero-size | borderlayout#flexed | 1590x0 with 1 children`. **That is a real
  markup defect, identical on a real server**, and must not be excused as something the image cannot
  judge — doing so teaches the agent to ignore a true finding.
- **`--full-page` cannot reveal more of a `vflex` page.** It never resizes the browsing context
  (`innerHeight` stayed 900 while the PNG stitched to 1404), and a `vflex`-rooted page is exactly
  viewport-tall, so the full-page capture is the same size as the default. **`--height` is the lever** —
  the same page at `--height 1400` measured 1400 with nothing clipped.
- **`hflex` is a width and does none of this.** An `hflex`-only root page flows past the fold like any
  other and stitches to 1600×1400. Pairing the two flags in one caveat is what produced a false claim in
  the first draft of the shipped documentation.

### 18. Forwarding `Accept-Encoding` to `/zkau/web/*` breaks the page completely

The launcher forwards the browser's request headers into its mock servlet request, because ZK resolves
device type and browser server-side from `User-Agent`. **The resource dispatch path is excluded from
that, permanently.**

Measured: with the browser's real `Accept-Encoding` present, ZK's extendlets return gzip,
`ResourceResult` carries no `Content-Encoding`, and gzip is served labelled `text/javascript` —
`Invalid or unexpected token`, then `zk is not defined`, nothing paints, `WARNINGS: 5` against a
baseline of 1.

> **Do not "complete" this change symmetrically.** Render dispatch only.

Also measured on the same work: the headers **cannot** be a thread-local, because with
`--run-controllers` the render happens on a one-shot executor thread created inside `renderZul`.

### 19. Layout-rule conditions that are wrong as anyone would first write them

Five rules in the original specification were corrected by measurement, because the browser disagreed
with the spec and the browser is the fact. Each correction is a trap a future rule will re-encounter:

1. **`clipped-text` cannot use `scrollWidth > clientWidth` on the text element.** ZK renders `<label>`
   and `<a>` as `display: inline`, where both are 0 by CSS definition. Measure the text run with a
   `Range` against the nearest clipping box instead.
2. **`zero-size` cannot use `clientWidth === 0 || clientHeight === 0`** — same inline-box fact: a plainly
   visible 14.9×20 icon link reports 0×0. Use rects.
3. **`zero-size`'s `childElementCount > 0` excludes the very defect it was written for.** A collapsed
   `<a label="Settings"/>` has no element children. The condition is text **or** children.
4. **`overflow: hidden` clips at the *padding* box, not the content box.** Against the content box the
   audit produced confirmed false positives on a stock asset whose headers render in full. Position
   matters as much as size.
5. **A widget root whose subtree still has a box has not vanished.** The literal rule produced four false
   `zero-size` findings on one borderlayout page.

Also narrowed deliberately: *"computed `overflow-{x,y}` is not `visible`"* became `hidden`/`clip` only,
because ZK's Grid, Listbox and Tree bodies are `overflow: auto` and the literal rule fires on **every row
of every data table**.

### 20. ZK 10.3 bundles Font Awesome 6.4.2

Several Font Awesome 4 names a model would reach for from memory are gone. The icon class names live in
`web/zul/font/font-awesome.css.dsp` inside the `zul` jar, alongside the base rule
`[class*="z-icon"] { font-family: ZK85Icons, FontAwesome }`.

This matters because **`iconSclass="z-icon-file-pdf-o"` with a typo renders *nothing* and stays silent
through every validation layer.** Two greps against the jar remove that whole class of defect — and this
is a "does the name exist" question, which is the only kind where reading the jar is the right move (see
[product-rationale.md](product-rationale.md) §6).

### 21. Passing validation does not mean the page renders

- `<combobox selectedIndex="0">` passes all five validator layers and dies at render with
  `Out of bound: 0 while size=0`. Mechanically detectable in source — but **not** as "a selection
  index on a component with no model", which is how this entry first recorded it and how Layer 6
  was first built. See §21b: the model is irrelevant, and so are the items.
- `@Wire` with a mismatched field type (an `<a>` wired to a `Label` field) compiles, passes validation,
  renders fine, and throws `ClassCastException` at runtime only when the field is used.

### 21b. A literal `selectedIndex` is applied before the children *and* before the model

Rendered one page per component, each with its literal items present (ZK 10.3.0.1):

| Component | literal items in markup | bound model | outcome |
|---|---|---|---|
| `combobox` | 2 `<comboitem>` | `@load(list)` | **throws both ways** |
| `listbox` | 2 `<listitem>` | `@load(list)` | **throws both ways** |
| `radiogroup` | 2 `<radio>` | (no model form) | **throws** |
| `tabbox` | 2 `<tab>` | (no model form) | **throws** |
| `selectbox` | (no literal form) | `@load(list)` | renders |
| `cardlayout` | 2 child `<div>` | (no model form) | renders |
| any of them | — | — | `selectedIndex="-1"` renders |

Exceptions raised: `Out of bound: 0 while size=0` (combobox, listbox), `0 out of 0..-1`
(radiogroup), `No tab at all` (tabbox).

So for the first four, **neither the literal items nor a model rescues the index** — it is applied
while the element itself is being built, before its children are attached and long before a binder
sets a model. Counting the literal items was the wrong model of the timing, and it was the wrong
model *in the direction that hides the defect*: Layer 6 reported
`<combobox selectedIndex="0">` with three comboitems right there in the markup as clean, and the
render died. The same page also showed the second half: `<listbox model="@load(vm.items)"
selectedIndex="0">` throws identically, so the "a model silences it" exemption was a false
negative rather than the deliberate under-report it was documented as.

Found by writing exactly that combobox into a showcase page, so it is the shape an author reaches
for naturally — a sort dropdown that should open on its first option.

Rule: Layer 6 now flags a literal non-negative `selectedIndex` on `combobox`, `listbox`,
`radiogroup` and `tabbox` unconditionally, names the per-component remedy
(`value="..."` / `selected="true"` / select after `setModel`), and keeps the counting rule only for
the two components measured to tolerate an index. Pinned by
`test/wrong/selectedindex-with-literal-items.zul` (must fail on Layer 6 alone),
`test/valid/selectedindex-tolerated.zul` (must pass), and six `L6:` checks in
`test/run-schema-query-tests.py` — two of which previously asserted the refuted behaviour.

### 22. XML forbids `--` inside a comment, and it bites anyone documenting a `--flag`

Four independent occurrences, one of them *after* the fix landed — while writing a comment about a flag
whose name starts with two hyphens, in the fixture built to test icons. The root cause was the skill's
own doing: `controller-guidelines.md` item 4 recommends `// --- Wired components ---` separators, legal
in Java, a hard error in ZUL, with no reference file noting the difference. Fixed at source in
`3d485f2` by adding the contrast (not by deleting the Java advice) and by repeating the rule in
`SKILL.md` Step 2, because an agent writing a static page never opens the controller guidelines.
`validate-zul.py` also names the rule in its `ParseError` path — expat only says
`not well-formed (invalid token)`.

### 23. `mvn -o compile` will not rebuild after a real source edit

Reports "Nothing to compile". `touch` does not help; only deleting the `.class` forces a rebuild. This
sits directly inside the skill's edit → compile → `--run-controllers` loop, and matters most for
`<charts>`, where **a stale `.class` and "the chart never drew at all" look identical** — read the
`CONTROLLERS:` line first.

---

## Model, template and controller behaviour

### 24. `setModel()` copies the model's own `multiple` flag onto the component

`ListModelList` defaults to single selection, and `Listbox.setModel()` applies the model's flag to
the listbox — so `setModel(new ListModelList<>(rows))` **silently overrules `multiple="true"` in the
ZUL**. On a `<listbox checkmark="true">` the visible symptom is that the checkbox column comes back
as **radio buttons**, which is the only reason it gets noticed at all.

Nothing static sees it: the ZUL is correct, the Java compiles, all seven validator layers pass, and
the page renders. It surfaced on the extraction pass of a page whose Pass-1 render had square
checkboxes and whose Pass-2 render had round ones — i.e. only because the same page was rendered
before and after the data moved, which is the argument for that second render existing.

Fix is on the model, not the component:

```java
ListModelList<Transaction> model = new ListModelList<>(TRANSACTIONS);
model.setMultiple(true);
txList.setModel(model);
```

Recorded in `references/controller-guidelines.md` §3.

### 25. A template's variable differs between the binder and plain EL, and fails silently

Inside `<template name="model">`:

| Page | Expression that works | The variable |
|---|---|---|
| MVVM (binder) | `@load(node.data.name)` | `var="node"` **is** honoured |
| MVC (plain EL) | `${each.data.name}` | always `each`; a custom `var` is **ignored** |

And what the variable holds depends on the component: for a **grid or listbox** template `each` is
the item (`${each.action}`); for a **tree** it is the `TreeNode`, so the data is one hop further in
(`${each.data.action}`).

**The failure mode is the expensive part.** An unresolvable variable renders as empty text, not as
an error. An MVC tree written `${node.data.name}` produced a tree with correct structure,
indentation, open/closed state and selection — and every label blank, every `sclass` unset, so the
node divs measured `0x0` and the only clue was that the `LAYOUT` locator said `div.z-div` where it
had said `div.tc-node` before extraction. Two edits were spent on it before it was probed.

The probe that settled it is worth copying: put all four candidate expressions in one cell and
render once. `${each.name}` throws `Property 'name' not found on type org.zkoss.zul.DefaultTreeNode`
— which names the variable's real type *and* the missing hop in a single message, while the three
silent forms prove themselves wrong by rendering nothing.

Recorded in `SKILL.md` Step 2 (extraction, action 2) and `references/controller-guidelines.md` §5.
