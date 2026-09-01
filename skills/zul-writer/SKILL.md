---
name: zul-writer
description: >
  Generates ZK Framework ZUL pages (.zul) through a structured 5-step workflow: requirements clarification, ZUL generation, validation, controller generation, and a rendered-image self-review.
  Every step also stands alone, so use this skill for a single step too — validating an existing .zul, writing the Composer/ViewModel for a page that already exists, or just rendering a .zul to a preview PNG without touching it.
  Supports both MVC (Composer-based) and MVVM (ViewModel-based) patterns, ZK 9/10, and visual analysis for screenshot-to-ZUL conversion.
  Use when the user asks to create a ZUL page, build ZK UI components (forms, grids, dashboards, borderlayouts), convert an image/mockup to ZUL code, edit or extend an existing ZUL page, move a page's hard-coded data into a Composer/ViewModel, validate/fix a .zul that errors, preview/screenshot/see what a ZUL page looks like, or work out why a rendered page looks wrong — a blank icon, a clipped label, an element that is not there, a colour or width nobody asked for.
license: MIT
compatibility: >
  Designed for Claude Code, Gemini CLI, and GitHub Copilot/Cursor.
  Requires access to local skills/zul-writer/assets/ and skills/zul-writer/references/ directories.
metadata:
  author: hawk
  version: "2.0.0"
---
# ZUL Writer

## Workflow Overview

This skill creates well-structured zul pages through a 5-step process:

1. **Clarify Requirements** - Gather page purpose, pattern, and layout needs
2. **Generate ZUL** - Create the ZUL file based on requirements
3. **Validate ZUL** - Verify correctness of the generated ZUL
4. **Generate Controller Class** - Create the corresponding Java class (ViewModel or Composer)
5. **Preview & Self-Review** - Render the page to an image and check it against the requirements

**Alternative entry**: When user provides a UI image (screenshot/mockup), perform the **Visual Analysis** below first, then proceed to the 5-step process.

### Run only the steps the request needs

The five steps are entry points, not a chain. A page built from nothing needs all of them; most
other requests need one or two. Someone who hands you a finished `.zul` and asks what it looks like
wants Step 5 and nothing else — interviewing them about MVC vs MVVM, or "improving" their markup on
the way past, answers a question they did not ask and costs them a page they were happy with.

| What the user asks | Steps to run |
|---|---|
| "Build me a page that…", "turn this mockup into ZUL" | 1 → 5, the whole workflow |
| "Preview / screenshot / show me what `foo.zul` looks like" | 5 |
| "Why is this icon a blank box / this label clipped / this section missing?" | 5, then `--probe` the element |
| "Is this ZUL valid?", "why won't this page parse?" | 3 |
| "Write the ViewModel for this page" | 4 |
| "Move this page's data into a ViewModel/Composer" | the extraction pass in Step 2 → 4 → 5 with `--run-controllers` |
| "Add a column to this grid", "make the sidebar narrower" | 2 on the existing file → 3 → 5 if the change is visible |
| "Build a page for this ViewModel/Composer we already have" | 1 → 5, but there is nothing to extract — see *Model-driven pages* in Step 2 |

**A model-driven page runs Step 5 twice, and the second time is not a fix round.** The numbered
steps are the order for a page whose data is still in the markup; once Step 5 has settled the
layout, the extraction pass in Step 2 moves that data into the controller and one more
`--run-controllers` render checks it. So the shape is 1 → 5, then back to 2 → 4 → 5 once. That last
loop is easy to forget precisely because it runs backwards through the numbers.

**"Why does this look wrong?" is a diagnosis request, not a validation one.** The two rows sit
together because they are so easy to confuse: *why won't this page parse* and *why is this icon a
blank box* read alike, and Step 3 answers only the first. `<label sclass="z-icon-bell"/>` is valid
ZUL — the validator passes it and reports the page clean, which is precisely how a real defect
gets closed as "no problem found". A page that renders wrong while validating clean is the case
Step 3 cannot see. The markup is already written; the question is what the browser did to it, and
only a render can answer that. Go to Step 5 and probe the element, so the measurement names the
cause before you touch the markup — opening with a guess costs a round and can "fix" the wrong
line convincingly. Naming the cause is the whole answer to a "why"; the edit is a separate
question, and it is the user's to ask.

The steps you skip still feed the ones you run — Step 4 needs to know whether the page is MVC or
MVVM, Step 5 needs something to judge the render against. Read those out of the file and the user's
message rather than restarting Step 1: an existing `.zul` already states its pattern, its layout and
its ZK version far more reliably than an interview would. Ask only what you genuinely cannot infer.

**Called in for one step, report rather than rewrite.** Validating or rendering a page you did not
write surfaces things nobody asked you to change. Say what you found, then make only the edit that
was requested — or wait to be told to fix the rest. The exception is the defect that blocks the step
itself: a page that will not parse cannot be rendered, so name it and offer the fix.

---

## Visual Analysis (for Images/Mockups)

When a UI screenshot or mockup image is provided, perform this analysis **before** starting the 5-step workflow:

1. **Visual Breakdown**: Identify all UI elements (layout, inputs, buttons, tables, navigation).
2. **Component & Layout Strategy**: Plan the ZK component mapping (refer to [references/ui-to-component-mapping.md](references/ui-to-component-mapping.md)) and determine the overall layout (e.g., `<borderlayout>`, nested `<vlayout>`).
3. **Tab Content Scope**: If tabs are present, determine content boundaries. Items switching with tabs must go INSIDE `<tabpanel>`. See [assets/content-tabbox.zul](assets/content-tabbox.zul).
4. **Identify Custom Styling**: Mark areas that require fallback HTML elements or custom CSS.

**Transition**: Use these findings to inform **Step 1: Clarify User Requirements** and eventually **Step 2: Generate ZUL File**.


---

## Step 1: Clarify User Requirements

Ask targeted questions to understand needs. If starting from an image, use the results of the **Visual Analysis** to inform these questions.

Ask only what is still open. The request, the project and any existing file answer several of these
already — a version in `pom.xml`, a pattern visible in the markup you were pointed at, a layout
described in the prompt — and re-asking those reads as though you did not look.

### Questions to Ask

#### 1. ZK Version
Detect from user's project (check `pom.xml`, `ivy.xml`, or `build.gradle` for ZK dependency version). If not found, ask:
- 9 or before
- 10.x

#### 2. Page Purpose
- Data entry form
- Data list/grid display
- Dashboard with multiple sections
- Dialog/popup window
- Master-detail view
- Search and results page
- Other: [specify]

#### 3. MVC or MVVM Pattern
Present both options with equal weight — do NOT mark either as "(Recommended)":
- **MVVM**: ViewModel-based with `@bind`/`@command` data binding — testable, requires more ZK familiarity
- **MVC**: Composer-based with `apply` and wired components — straightforward, beginner-friendly

The line between them is exact, so there is never a page you cannot classify: **MVC applies a
Composer** (`apply="com.foo.MyComposer"`), **MVVM sets a ViewModel and uses binding syntax**
(`viewModel="@id('vm') @init('com.foo.MyVM')"` plus `@load`/`@bind`/`@command`). Either one is a
controller, and it governs the component it is set on **and every descendant of it**.

**Write one pattern per page.** ZK permits mixing them and some projects do, but a mixed page has no
single answer to "where does this value come from", which is the question both the extraction pass
and the Step 5 self-review depend on. If the user asks for both, ask which one the page's data
should follow.

#### 4. Static Data or Model-Driven

Ask this as its own question. It is independent of MVC/MVVM — that choice decides where *behaviour*
lives, this one decides where *data* lives — and it changes the order the work happens in:

- **Static data**: the text and rows are written in the ZUL — `<label value="Acme Corp"/>`, and rows
  spelled out as `<row>` in a grid, `<listitem>` in a listbox, `<treeitem>` in a tree. Right for a
  layout, a mockup, a demo, anything whose content is fixed.
- **Model-driven**: the controller supplies them — a Composer calling `setModel()` on a component it
  wired, or a ViewModel the page reads through `@load`/`@bind` and a bound `model`. Right for
  anything backed by real data.

**A component gets its rows from one of these, never both.** Setting a model discards the rows
written in the markup, silently, so literal rows left beside a model are markup that displays
nothing at all.

Either answer still gets a controller in Step 4. Model-driven pages are additionally built in two
passes — see *Model-driven pages* in Step 2.

#### 5. Layout Requirements
- Borderlayout (north/south/east/west/center)
- Vertical layout (vlayout)
- Horizontal layout (hlayout)
- Grid-based layout
- Tabbed layout (tabbox)
- Combined layouts

#### 6. ZK Charts (only when charts are needed)

If the ZUL page requires a `<charts>` component, follow [references/charts-guidelines.md](references/charts-guidelines.md) before generating any chart code.

#### 7. Theme and Data Density

If a page is designed to show a high density of data, suggest to the user to use another free theme called `iceblue_c`, a compact theme that has smaller padding, margin, and font-size.

---

## Step 2: Generate a ZUL File

### Generation Guidelines

When generating the ZUL file, follow these technical guidelines:

1. **Map UI Elements**: Consult [references/ui-to-component-mapping.md](references/ui-to-component-mapping.md) to choose the correct ZK components. 
   - Prioritize ZK components over native HTML.
   - Use layout components like `<borderlayout>`, `<vlayout>`, and `<hlayout>` effectively.
2. **Style through classes, not through `style` attributes**:
   - Put the page's CSS in one `<style>` element near the top of the file — **not** the `<?style ?>`
     processing instruction — and attach it with `sclass` on ZK components (`class` on native `n:`
     elements). Name each class for what the thing *is* (`sclass="stat-card"`), and give the page's
     classes a short prefix of their own so they cannot collide with ZK's `z-` classes or with
     another page's CSS.
   - **Why this is not just taste.** A `style` attribute is rendered onto the widget's own element,
     where it outranks every rule any stylesheet can write: the page stops being themeable, CSS
     written later silently loses to it, and no `:hover`, `:focus` or `@media` rule can ever reach
     it. Declarations pasted onto a dozen components also drift into a dozen near-identical values,
     where one class is edited once and every instance follows.
   - **When a class looks like it "doesn't work", the theme is out-specifying it** — `.z-button` is
     more specific than `.my-btn`, so the theme wins. Qualify the selector
     (`.my-page button.my-btn { … }`) rather than reaching for `style`; that reach is exactly how a
     page ends up inline-styled all the way down.
   - **Size and spacing belong to the component, not to the CSS.** `hflex`/`vflex`, `width`,
     `height`, `spacing` and `valign` are the component's own API and cooperate with ZK's layout
     engine; recreating them in CSS is how flex layouts break. Let the component own the box and the
     class own the appearance.
   - **One honest exception: a value that only exists at runtime.** A colour or width that comes from
     data (`style="@load('background-color:'.concat(tag.color))"`) cannot be a static class. Keep
     that one declaration inline and leave the rest in the class.
   - If fallback native HTML elements (e.g. `<n:div>`) are used, include the CSS they need in that
     same `<style>` block.
3. **ZK Documentation**:
   - Query `zk-doc-mcp-server` for detailed component info if available.
   - Use [ZK Javadoc](https://www.zkoss.org/javadoc/latest/zk/) for properties and event details.
4. **Best Practices**:
   - Prefer `hflex`/`vflex` over fixed pixel widths for responsive layouts. `hflex="min"` sizes a component to fit its content — useful for a `<button>` sitting beside an `hflex="1"` field (see [assets/flexible-sizing.zul](assets/flexible-sizing.zul)).
   - Use meaningful IDs and follow the [assets/template.zul](assets/template.zul) structure.
   - **Never put `--` inside an XML comment.** XML forbids it anywhere between `<!--` and `-->`, so
     the `<!-- ---------- Left column ---------- -->` separator that is perfectly good Java style is
     a hard parse error in a ZUL. Use `=`: `<!-- ===== Left column ===== -->`.


### Model-driven pages: write the data in, then take it out

A page whose values come from a controller cannot show you itself until that controller runs. Until
then `@load(vm.customer)` renders as dimmed expression text and a bound `model` renders as a couple
of placeholder rows — so column widths, wrapping, card heights and whether a row of stats fits are
all being judged against text that is not the text the page will hold. That is how a page passes
Step 5 and still comes out wrong the first time it is run for real.

**Which of the two paths you are on is a lookup, not a question.** Do not ask the user; the answer
is in front of you. A page you are writing from nothing needs a controller you have not written yet
— in ZK a Composer or ViewModel belongs to a page, not to a shared service layer, so a new page
means a new controller and the two-pass path below. Only an existing `.zul` can already name a class,
and then you open it: if it exists and compiles, there is nothing to extract — render with
`--run-controllers` from the start and judge the real data.

#### Pass 1 — literal data, real shape

Write the first version with literal values, shaped like the data that will replace them: a name of
realistic length, a price with its real digits, enough rows to fill the region. Rows go in as
markup — `<row>` in a grid, `<listitem>` in a listbox, `<treeitem>` in a tree. Literals render as
themselves, so the Step 5 screenshot is the page the user will actually get, and this pass is
*cleaner* than a bound one: with no `@load` anywhere there is not a placeholder on the page.

**The controller you write in Step 4 for this pass holds behaviour, not data** — the event handler,
the `@Command`, the wiring. Putting the data in it now cancels the whole point of the pass: Step 5
would render real rows through `--run-controllers` and you would be back to judging the layout
against text you never checked.

Iterate here until the layout and the styling are right.

#### Pass 2 — extraction, after Step 5 has settled the layout

This is the one action in the workflow that runs **after** Step 5 rather than before it, so it is
easy to skip. Its trigger is "the layout is settled", which is a Step 5 outcome. Four actions, in
order:

1. **Move each literal into the controller** as a field, getter or list.
2. **Point the ZUL at it.** MVVM replaces the value with the binding that reads it
   (`@load(vm.customer.name)`, `model="@load(vm.items)"`). MVC has no ZUL-side expression at all:
   the Composer wires the component by its `id` and calls `setModel(...)`, so the ZUL keeps the
   `id` and gains nothing else.
3. **Delete the literal rows.** They are not harmless leftovers. Setting a model — bound or through
   `setModel()`, full or empty — **discards the rows written in the markup**, silently and with no
   warning, so the page renders correctly while the markup keeps rows that display nothing. Nobody
   looking at the image can see this, which is why `literal-rows-discarded` in Step 5's `LAYOUT`
   block measures it for you.
4. **Change nothing else** — same components, same `sclass`, same `hflex`. Extraction moves values,
   not structure, so if the page shifts afterwards the extraction is what to look at.

Then re-render once with `--run-controllers` to confirm it did not. That render checks the
extraction, not the layout, so it sits outside Step 5's two-round budget.

### Layout & Component Patterns

#### XML & Pattern Structures
- **Base Template**: [assets/template.zul](assets/template.zul)
- **MVC Structure**: [assets/mvc-sample.zul](assets/mvc-sample.zul)
- **MVVM Structure**: [assets/mvvm-pattern-structure.zul](assets/mvvm-pattern-structure.zul)

#### Sizing & Layouts
- **Flexible Sizing (hflex/vflex)**: [assets/flexible-sizing.zul](assets/flexible-sizing.zul)
- **Borderlayout Example**: [assets/borderlayout-example.zul](assets/borderlayout-example.zul)

#### Common MVVM Patterns
- [Form with Validation](assets/form-validation-mvvm.zul)
- [Data Grid with Selection](assets/data-grid-selection-mvvm.zul)
- [Master-Detail Pattern](assets/master-detail-mvvm.zul)
- [Dialog/Popup](assets/dialog-popup-mvvm.zul)

---

## Step 3: Validate Generated ZUL

Run validation using the script from this skill's base directory (provided as "Base directory for this skill:" in the skill context header). Pass the ZK version detected in Step 1 via `--zk-version` so Layer 4 checks match the target:

```bash
uv run <skill-base-dir>/scripts/validate-zul.py --zk-version <detected-version> <path-to-zul-file>
```

Example: if the skill base directory is `~/.claude/skills/zul-writer` and the project targets ZK 10.3.0, run:
```bash
uv run ~/.claude/skills/zul-writer/scripts/validate-zul.py --zk-version 10.3.0 path/to/file.zul
```
- Layer 1: XML well-formedness (no dependencies). Multi-root fragments are auto-wrapped in `<zk>` before validating.
- Layer 2: XSD schema validation (requires `lxml`)
- Layer 3: Attribute placement check (requires `lxml`) - catches misplaced attributes (e.g. `iconSclass` on `textbox`)
- Layer 5: inline-style advisory — lists static `style="..."` attributes that belong in a `<style>`
  class attached with `sclass`. It reports and never fails the run, so treat each line as a defect
  to fix rather than noise to pass over; a data-driven `style="@load(...)"` is skipped on purpose.
- Layer 4: version compatibility checks for the target ZK version — removed/deprecated API for all targets, plus ZK-10-only API (e.g. dropped `<fragment>`, or new `accept`/`responsive` attributes) gated by `--zk-version`. Defaults to `10` if omitted.

### Prerequisites
Layer 2 and 3 require `lxml`. **`uv run` handles this automatically** via the script's PEP 723 inline metadata — it provisions `lxml` in an ephemeral environment, so no manual setup is needed. If `uv` is unavailable, run with a plain interpreter instead and the script self-installs `lxml` as a fallback:

```bash
python3 <skill-base-dir>/scripts/validate-zul.py --zk-version <detected-version> <path-to-zul-file>
```
(On Windows, use `python` instead of `python3`.)

### Usage Tracking
Running this script also fires an anonymous, aggregate usage ping (skill name + version only, no identifier) on a background thread — it never delays or blocks validation. Opt out with `DO_NOT_TRACK=1` or `TRACK_URL=""`, or per-run with `--dev` — which is what runs made while developing or testing the skill itself should pass, so they are not counted as usage.

### Asked only to validate

Report the layers that failed, quote the lines the script names, and say what each one means — then
stop. A validation request is a request to be told what is wrong; edit the file when the user asks
for the fix, or when fixing it is the task you were already on.

### Post-Validation Checklist

#### Pattern Consistency
- **MVC**: Uses `apply` attribute, no MVVM binding expressions
- **MVVM**: Uses `viewModel` attribute, proper binding syntax
- One pattern for the whole page, not one per component
- No component carries both a `model` and literal rows — see *Model-driven pages* in Step 2

#### Best Practices
- IDs are unique within each ID space owner (`<window>`, `<idspace>`)
- Appearance lives in `<style>` classes attached with `sclass`; the only `style` attribute left is
  one whose value comes from data. Layer 5 lists any others it found
- Prefer `hflex`/`vflex` over fixed dimensions
- Include meaningful labels and tooltips for accessibility


## Step 4: Generate Controller Class

Generate the corresponding Java controller class (ViewModel or Composer) for the ZUL page. 

**Generate it for a static-data page too.** The values may be fixed, but the page will still have to
*do* something, and what a developer needs from you is the shape of that attachment: how a Composer
wires a component and listens for its event, how a ViewModel declares a `@Command` and what the ZUL
writes to invoke it. Leaving it out withholds the one part that is ZK-specific and hard to guess. So
include at least one working handler on something the page really has — the Save button, the row
selection, the search box — acting on the values already in the markup.

**Behaviour now, data later.** Whether the page is static or model-driven, what you write here is
the page's *behaviour*. On a model-driven page the data is still in the markup at this point and
belongs there until the layout is settled — so no `setModel()`, no getter backing a bound `model`,
not yet. Both arrive in the extraction pass (see *Model-driven pages* in Step 2), and this step runs
a second time to receive them. Writing the data in now is the single easiest way to lose the literal
pass without noticing: Step 5 would render real rows and the layout would never be judged against
anything you checked.

### Controller Generation Guidelines

1. **Pattern Consistency**: 
   - Use **ViewModel** for MVVM patterns.
   - Use **Composer** for MVC patterns.
2. **Implementation Details**: Follow the technical requirements in [references/controller-guidelines.md](references/controller-guidelines.md).

#### MVC Pattern - Composer Class
[assets/MyComposer.java](assets/MyComposer.java)

#### MVVM Pattern - ViewModel Class
[assets/MyViewModel.java](assets/MyViewModel.java)

### Complete Examples & Patterns

For complex UI patterns like Kanban Boards or Dashboards, and for complete template examples, refer to [references/use-case-guidelines.md](references/use-case-guidelines.md).

---

## Step 5: Preview & Self-Review

Render the finished page to an image, **look at it**, and check it against the requirements gathered in Step 1. Steps 2–4 only ever see markup; this is the only step that sees what the page actually looks like.

**Asked only for a preview**, there are no Step 1 answers to judge against — so judge the render
against the page's own markup and whatever the user said they expected, describe what you see, and
report the image path. The *What to fix* list below still tells you what counts as a defect worth
mentioning; it does not license editing a file the user asked you to look at rather than change.

Run the preview script from this skill's base directory (same convention as Step 3):

```bash
uv run <skill-base-dir>/scripts/preview-zul.py <path-to-zul-file>
```

Example: if the skill base directory is `~/.claude/skills/zul-writer/` and the page lives in a Maven webapp, run:
```bash
uv run ~/.claude/skills/zul-writer/scripts/preview-zul.py src/main/webapp/index.zul
```

**Where the image goes: the current working directory.** With no `--out`, the PNG is written to the
directory you are working in, named after the page — `index.zul` gives `./index-preview.png` — and
the `SCREENSHOT:` line reports the exact path. Leave it there. This image is not a scratch file: it
is the one visual artifact of the whole workflow, the thing the user opens to see whether the page
matches what they asked for, so it belongs beside their work where they can click it, keep it, or
delete it. Sending it to a temp or scratchpad directory instead hides it behind a path they would
have to be told about and cannot find again later. Re-renders overwrite the same file, so the path
stays valid across fix rounds and is still the right one to report at the end. Pass `--out` only
when the user names a destination, or when a corpus/CI job needs the images collected somewhere.

If this session wrote the page's controller, append `--run-controllers` (read the next paragraph
before you do — it executes project code):
```bash
uv run ~/.claude/skills/zul-writer/scripts/preview-zul.py --run-controllers src/main/webapp/index.zul
```

**When to pass `--run-controllers`.** Pass it when this session wrote the page's controller
(Step 4's composer or ViewModel): the sample data in it is yours, running it is what turns a
skeleton screenshot into a judgeable one, and the flag makes bound values, model-bound rows and
composer-filled labels real. It is also the render that checks an *extraction*: after moving a
page's literals into its controller (Step 2), this is what shows the page still looks like the one
you approved. Do **not** pass it for a page whose controller you did not write —
the flag **executes arbitrary project code** from the project's classpath (constructors, service
calls, whatever `doAfterCompose` does), so it is opt-in per render and never a default. If the
controller has not been compiled yet, build first (`mvn compile` / `gradle classes`); the script
warns when no compiled classes are on the classpath. Add `--controller-timeout <seconds>` only if
a legitimately slow page keeps degrading (the default budget is 10 s for the whole render).

**Viewport: `--width`, `--height`, `--full-page`.** The default viewport is 1280x900; the `SIZE:`
line in the output always says which viewport the render actually used.

- **Match the mockup's width.** When the user supplied a screenshot or mockup, pass `--width` at
  approximately that image's pixel width, so the two images compare like for like — a 1600 px
  mockup means `--width 1600`. Rendering the 1280 default against a wider mockup adds differences
  that are yours, not the page's, and you will spend fix rounds on them. Match the *layout* width,
  not the file's pixel count: halve a high-DPI export, and do not follow a thumbnail far below 1024
  unless you mean to test a narrow viewport — a very narrow render manufactures `clipped-text`
  findings that the same markup does not produce at desktop width.
- **`--full-page` when the page flows past the fold** — long forms, stacked reports, anything meant
  to scroll. It stitches the whole scrollable page into the PNG.
- **`--height` when the page is a vertical flex shell.** A page whose root region is `vflex` is
  exactly viewport-tall by construction, so `--full-page` cannot show more of it: raise `--height`
  instead. `hflex` is a width and does not do this — an `hflex` page flows past the fold like any
  other, and there `--full-page` is the right flag. A `--full-page` capture that comes back exactly
  as tall as the `SIZE:` viewport is telling you the page is flex-sized, not truncated.

```bash
uv run ~/.claude/skills/zul-writer/scripts/preview-zul.py --width 1600 --full-page --run-controllers src/main/webapp/index.zul
```

The script resolves the project's ZK jars (Maven, Gradle, or stock ZK when the file belongs to no project), renders the page through ZK's own engine, and writes a PNG. **Requires Java 17+ and Google Chrome or Microsoft Edge.** On first use it downloads the render helper (`zk-preview-launcher.jar`, ~500 KB), verifies its SHA-256, and caches it under `~/.cache/zul-writer/`; later runs need no network.

Then **read the PNG** with your image-reading tool and compare it against the Step 1 answers. If the user started from a screenshot or mockup, re-read that image too and compare the two side by side.

### When there is no preview

The script exits **2** and prints one line beginning `PREVIEW_SKIPPED:` — no ZK jars resolvable, no Java 17+, no browser, or the helper could not be downloaded. **This is not a defect in the ZUL.** Report it in one line — *"Skipped the rendered preview: &lt;reason&gt;"* — and finish the task normally.

Never describe a screenshot you did not see, and never let a skipped preview stand in for a passed one.

The `NEXT:` line says what would enable a preview. If that looks fixable from here, spend **one** retry on it — appending `--debug` prints the resolved classpath, every helper command line and the renderer's own output to stderr (stdout is unchanged), which is usually enough to see why. Then stop and report the skip either way.

### Read the `CONTROLLERS:` line first

It is one line in the output, and the judging rules below **invert** on it:

| Line | What the image is | How to read it |
|---|---|---|
| `CONTROLLERS: executed` | controllers ran: real bound values, real model rows, real composer output | *What you cannot judge* shrinks — a blank bound field **is** a defect |
| `CONTROLLERS: skipped (isolated)` | the default: no Composer, no ViewModel | dimmed expression text and placeholder rows are correct behaviour |
| `CONTROLLERS: failed → isolated` | you asked for controllers; they failed and the isolated render was served instead | read it under the isolated rules, and see the new *What to fix* bullet below |

### Read the `LAYOUT:` block first

A browser *measured* these, so they are facts, not opinions — read them before you open the PNG.
Each line is `rule | locator | measurement`:

```
LAYOUT: 3 findings
  - zero-size         | a[label="Settings"] | 0x0 with text but no box
  - clipped-text      | a[label="Documents"] | text needs 77px, box is 48px
  - viewport-overflow | grid.gp-wide | page scrollWidth 2005 > viewport 1280; widest offender 2000px
```

The locator is the ZUL id when the component has one (`label#breadcrumbCurrent`), otherwise the
component plus a distinguishing attribute (`a[label="Settings"]`) or its style class
(`grid.gp-wide`). It never names a generated id, so it is always something you can find in your own
markup.

| Rule | What it means | What fixes it |
|---|---|---|
| `clipped-text` | the text does not fit the box that clips it, so part of it is cut off | widen the box (`width`/`hflex`), let it wrap, or shorten the text |
| `zero-size` | the component occupies no space at all, and its content is invisible | a missing `height`/`vflex` on it or an ancestor, or a `width: 0` style rule |
| `escapes-parent` | visible content sticks out of an ancestor that clips, so the overhang is cut | give the parent room, or stop the child overflowing it |
| `viewport-overflow` | the page is wider than the viewport, so it needs a horizontal scrollbar; the line names the widest offender | remove the fixed width on the named element, or make it `hflex`/percentage |
| `icon-not-rendered` | a font icon will draw as an empty box: its glyph is there, but the font stack the browser resolved for it cannot supply that glyph | put the icon class on a carrier that keeps the icon font — `iconSclass`, or a plain container — rather than on one whose own `font-family` outranks it |
| `literal-rows-discarded` | rows spelled out in the markup are not on the page, because setting a model discards them. Usually an extraction that moved the data but left the old rows behind | delete the literal `<listitem>`/`<row>`/`<treeitem>` elements. The model is the page's only source of rows now |

`literal-rows-discarded` is the one rule you cannot check against the PNG, because it is about
something the page does *not* contain. **The page renders correctly** — the model's rows are all
there — while the markup keeps rows that display nothing at all, and the next person to edit one of
those rows will change nothing and not know why. It fires two ways: from the markup alone when a
`model` attribute sits beside literal rows, and from the render when a Composer's `setModel()`
(which lives in Java, invisible to any ZUL check) has replaced them. Paging, a collapsed tree node
and an unselected tab all keep rows off the page legitimately, and the rule is measured against
each of those, so a finding here is not one of them.

Three things to know before you act on the block:

- **It is omitted entirely when there is nothing to report.** No `LAYOUT:` line means the audit ran
  and found nothing.
- **It never changes the exit code in this loop.** Findings are reported, not enforced; `STATUS: ok`
  still means the page rendered. Only CI's `--fail-on-layout` turns findings into exit 4, and even
  then `STATUS: ok` prints first.
- **It covers the whole document, not just the captured image** — including everything below the
  fold, with or without `--full-page`. So a finding may name something the screenshot does not show.
  Trust the measurement, and re-render with `--full-page` if you want to see it.

Under `CONTROLLERS: skipped (isolated)`, a `clipped-text` finding on placeholder text (`prod.price`
in a narrow column) is measured against the placeholder, not against your real data — check it
against a `--run-controllers` render before widening a column for it.

### `WARNINGS:` — console and client errors

Three entry shapes in the `WARNINGS:` block come from the browser rather than from the launcher:

| Entry | What it means |
|---|---|
| `console error: <text>` | the page's own JavaScript called `console.error` — a `<zscript>`, an `n:script`, or a widget's client code |
| `console warning: <text>` | the same for `console.warn`. ZK's client engine does emit a few real ones (an unloaded locale, an unexpectedly large AU batch) |
| `ZK client error: <text>` | ZK's **client engine** complained — an unknown widget, a failed mount, a missing mold. The server was happy: `STATUS: ok`, exit 0 |

A `ZK client error:` entry is the one to take seriously. It is the only signal that the page the
server rendered did not actually come up in the browser, and it is invisible in the exit code.

Three limits worth knowing:

- **It covers first paint only** — everything up to just after the screenshot. A complaint raised by
  a later AU round-trip is never seen, so an empty block is not proof of a clean session.
- **ZK's client complaints come from its on-page error box**, which the script reads out of the DOM
  because ZK does not put them on the console. That box is a real element appended to the page — a
  pale red panel headed `N Errors`, top-centre, with a reload and a close icon — so it usually
  appears **in the PNG**. An unexplained red panel in the image is this same finding, not markup of
  yours to fix. Its own `N` counts every raised message, while the `WARNINGS` entries are deduped,
  so the two numbers legitimately differ when one complaint repeats.
- **Browser `Failed to load resource:` lines are deliberately not reported here.** Every page emits
  one for its missing favicon, and that line carries no URL, so keeping them would put a finding on
  every clean page. Anything that really failed gets its own `WARNINGS` entry naming the URL —
  `ZK resource not served` for a `~./` classpath miss, `page asset not found` for a file the docroot
  does not have.

`--debug` prints every console level to stderr, including the levels this block filters out — reach
for it when a page misbehaves and the block is empty.

### If you are scripting this, not reading it

`--report json[:<path>]` writes this same run as one JSON object — by default beside the PNG, with a
`.json` suffix — so a CI or corpus job can diff structured runs instead of parsing these lines.
stdout gains only `REPORT: <path>`; every block above is unchanged. The full schema, and which keys
are populated per exit code, is in `references/preview-guidelines.md`.

**Doing Step 5 by hand, do not pass it.** You already have this stdout in the same tool call that
ran the script, so the file is an extra round trip for identical information.

### What to fix

Judge **structure**, not pixels and not data. Fix only these:

- **An error page instead of the page** (the script exits 1 and prints `PHASE`, `MESSAGE` and `LOCATION`). A real ZUL bug — fix it at the reported location.
- **"Unknown component `<x>`"** — the jar defining that component is not on the classpath. Either the tag is a typo, or an add-on dependency is missing; ask the user rather than deleting the component.
- **Missing or extra sections** compared with what Step 1 asked for.
- **Wrong region placement** — a sidebar rendered under the content, a missing header, tab content sitting outside its `<tabpanel>`.
- **Wrong component choice** — a data table rendered as a plain stack of labels, a form field that isn't the input type requested.
- **Broken layout** — content clipped or overflowing, a horizontal scrollbar on a page meant to fit, a region collapsed to zero height, widgets overlapping, an `hflex`/`vflex` that visibly did not take. The `LAYOUT:` block names all of these precisely, with the component and the measurement — fix those first, before anything you are judging by eye.
- **Raw unstyled HTML** where a ZK component was intended.
- **An asset the page asked for and did not get.** The preview server serves the docroot, so a
  `WARNINGS` line naming a missing image, stylesheet or script means the file is not there at that
  path — a real miss, worth fixing, not a preview limitation. Check the path first and the
  `DOCROOT:` line second, since a guessed docroot makes correct paths look wrong. A `~./` URL is the
  other shape: that one means a jar is missing from the classpath, so ask the user about the
  dependency rather than editing the markup.
- **A font icon rendered as an empty box** — reported as `icon-not-rendered` in `LAYOUT:`, naming the
  glyph and the font stack that could not supply it. The class is on a carrier that overrides the
  icon font; *Icons* in [references/ui-to-component-mapping.md](references/ui-to-component-mapping.md)
  says which carrier to move it to. This is a one-word markup fix, and it was misdiagnosed three
  separate ways in an evaluation before it was measured — trust the finding over a theory about
  webfonts.
- **A `ZK client error:` entry naming an unknown widget or a failed mount** — the add-on jar's
  CLIENT-side JS package is absent even though the server-side class resolved, which is why the page
  parsed and then came up wrong. Check the `WARNINGS` 404 entries and the classpath, and ask the user
  about the dependency — never rewrite working markup for it.
- **`literal-rows-discarded` in `LAYOUT:`** — delete the literal rows it names. This is the one
  finding you will not be able to confirm by looking at the image, because the page in the image is
  correct; the defect is markup that renders nothing. Almost always an extraction that moved the
  data and left the old rows behind, so check that the controller really does supply them before
  deleting.
- **`CONTROLLERS: failed → isolated`** — read the `WARNINGS` entry: it names the failing class and
  the first cause line. A controller exception, a missing class or a blown budget is a defect in the
  **controller** (or a missing build), not in the ZUL. Fix it there and re-render, or report it —
  never work around it by hard-coding values into the markup. The exit code is still 0 and the
  screenshot is still valid; it just shows the isolated render.

### When the image shows a defect but not its cause

An empty box where an icon belongs. A component you cannot find. A colour nobody asked for. A
width that is not the one you set. In each case the PNG proves something is wrong and says nothing
about why — and re-rendering produces the same PNG.

**Probe the element instead of re-rendering.** `--probe '<css-selector>'` reports every match as
the browser actually built it: its opening tag, its measured box, and the computed styles these
defects turn on. It reads the render you already have, so it costs no extra round.

```bash
uv run --with playwright preview-zul.py page.zul --probe '[class*="z-icon-"]'
```

The `LAYOUT:` findings already name their elements with a CSS locator — paste that locator straight
into `--probe` to see why the measurement came out the way it did. When you do not yet know what to
ask for, `--dump-dom` writes the whole post-mount DOM to a file you can grep; it is a file and not a
block because a data-heavy page runs to hundreds of KB.

This matters because the DOM is the only place a ZK page exists as markup. The served response is a
`zkmx([...])` bootstrap that merely restates your `.zul` back to you — every class name, font and
box is built afterwards, in the browser.

### What you cannot judge from this image

The preview renders the **first paint only**. With `CONTROLLERS: skipped (isolated)` or
`failed → isolated` it also runs **no ViewModel and no Composer**, and everything below is the
renderer behaving correctly. Do **not** "fix" it, do not report it as a flaw, and do not let it
drive a re-render:

- **Bound values shown as dimmed expression text** (e.g. a literal `vm.customer` inside a textbox) — the ViewModel never runs. This is the renderer being correct, and it is also why a new model-driven page is written with literal data first (Step 2): you cannot measure a layout against text that is not the text it will hold.
- **Placeholder rows** in a `<grid>`/`<listbox>`/`<tree>` whose `model` is bound (e.g. rows reading `each.product`) — dimmed sample rows keep the component's real geometry.
- **A whole section missing where an `<include>` has a bound `src`** — this one is *not* placeholdered. A constant literal (`src="@load('~./page.zul')"`) is included for real; anything the ViewModel supplies (`src="@load(vm.page)"`) leaves `src` unset, so the include contributes **nothing** and you see a silent gap, not dimmed text. Adding a hard-coded `src` to "fix" the gap breaks the real page.
- **Anything a Composer or ViewModel would populate** — default values, initial selections, computed labels, i18n text. `apply="..."` composers are no-ops here.
- **Anything requiring a server round-trip** — button clicks, paging, sorting, tree expansion, selection highlighting, a `<window>` or popup opened by an event. Only the first-paint state exists. Client-side `w:` handlers *do* run, and so does `<zscript>`.
- **Theme-dependent colours and spacing** when the theme jar isn't a project dependency.
- **Exact spacing, font rendering, sub-pixel alignment, or a colour that is merely close** to the mockup.
- **Data content from the mockup** — sample data will differ. Compare the *shape* of the UI, not the values in it.
- **How tall a `--full-page` image is.** `--full-page` never resizes the browsing context — Playwright stitches a taller PNG afterwards — so the `LAYOUT:` findings and every `hflex`/`vflex` measurement refer to the `SIZE:` viewport, not to the image height. See *Viewport* in [references/preview-guidelines.md](references/preview-guidelines.md).

**Under `CONTROLLERS: executed`, the first four bullets above no longer apply** — dimmed expression
text, placeholder rows, the missing bound-`src` section and "anything a Composer or ViewModel would
populate" are all real output now. There, a bound field rendered blank, a data table with no rows,
or a section still missing **is a defect** — in the controller if it never supplied the value, in
the ZUL if the binding names the wrong property. Everything from *"Anything requiring a server
round-trip"* down still holds in both modes.

### How many rounds

- **At most two fix rounds.** A round is: render, read, list defects from *What to fix*, fix them,
  re-run Step 3 validation. Two of those, then stop.
- **The budget counts edits, not renders.** Rendering again to work out *why* something is wrong —
  which element, which measurement, which of two possible causes — is not a fix round and is not
  capped, and neither is a `--probe` or `--dump-dom` run. Nothing has been changed yet, so there is
  nothing to have got wrong twice; what the cap exists to stop is editing on a guess and then
  editing again on the next guess. Stopping at the cap with the cause still unknown is how a real
  defect gets shipped, or gets blamed on the preview. Diagnosis has a different stopping rule and it
  is not a number: **stop when the next render would not tell you anything the last one did not.**
  One evaluation run spent six renders isolating a chart animation that was clipping every
  screenshot, and that was the right call — a cap that made it feel like a transgression was
  measuring the wrong thing.
- **Fix only whole defects from that list.** If your list is empty, or everything left on it is in *What you cannot judge*, the page is good enough — say so in one line and stop. "Good enough" means every requirement from Step 1 is visibly present, in the right region, in the right kind of component, and nothing is clipped or overlapping.
- **A model-driven page spends its rounds on the literal version.** Settle the layout while the data
  is still in the markup, then extract and re-render once with `--run-controllers`. That render sits
  outside the two-round budget because it checks the extraction, not the layout — and if the page
  looks different afterwards, the extraction is what changed it.
- **Never edit the ZUL for a cosmetic difference alone.** Chasing pixels against a mockup costs rounds and regresses working markup.
- If a defect survives both rounds, **stop and tell the user** what it is and what you tried. Do not keep rendering.
- Report the final image path so the user can look at it themselves.

For classpath resolution details, the docroot rules, and what each `PREVIEW_SKIPPED` reason means, see [references/preview-guidelines.md](references/preview-guidelines.md).