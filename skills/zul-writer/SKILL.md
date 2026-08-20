---
name: zul-writer
description: >
  Generates ZK Framework ZUL pages (.zul) through a structured 5-step workflow: requirements clarification, ZUL generation, validation, controller generation, and a rendered-image self-review.
  Supports both MVC (Composer-based) and MVVM (ViewModel-based) patterns, ZK 9/10, visual analysis for screenshot-to-ZUL conversion, and rendering an existing .zul to a preview PNG.
  Use when the user asks to create a ZUL page, build ZK UI components (forms, grids, dashboards, borderlayouts), convert an image/mockup to ZUL code, or preview/screenshot/see what a ZUL page looks like.
license: MIT
compatibility: >
  Designed for Claude Code, Gemini CLI, and GitHub Copilot/Cursor.
  Requires access to local skills/zul-writer/assets/ and skills/zul-writer/references/ directories.
metadata:
  author: hawk
  version: "1.1.0"
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

---

## Visual Analysis (for Images/Mockups)

When a UI screenshot or mockup image is provided, perform this analysis **before** starting the 4-step workflow:

1. **Visual Breakdown**: Identify all UI elements (layout, inputs, buttons, tables, navigation).
2. **Component & Layout Strategy**: Plan the ZK component mapping (refer to [references/ui-to-component-mapping.md](references/ui-to-component-mapping.md)) and determine the overall layout (e.g., `<borderlayout>`, nested `<vlayout>`).
3. **Tab Content Scope**: If tabs are present, determine content boundaries. Items switching with tabs must go INSIDE `<tabpanel>`. See [assets/content-tabbox.zul](assets/content-tabbox.zul).
4. **Identify Custom Styling**: Mark areas that require fallback HTML elements or custom CSS.

**Transition**: Use these findings to inform **Step 1: Clarify User Requirements** and eventually **Step 2: Generate ZUL File**.


---

## Step 1: Clarify User Requirements

Ask targeted questions to understand needs. If starting from an image, use the results of the **Visual Analysis** to inform these questions.

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

#### 4. Layout Requirements
- Borderlayout (north/south/east/west/center)
- Vertical layout (vlayout)
- Horizontal layout (hlayout)
- Grid-based layout
- Tabbed layout (tabbox)
- Combined layouts

#### 5. ZK Charts (only when charts are needed)

If the ZUL page requires a `<charts>` component, follow [references/charts-guidelines.md](references/charts-guidelines.md) before generating any chart code.

#### 6. Theme and Data Density

If a page is designed to show a high density of data, suggest to the user to use another free theme called `iceblue_c`, a compact theme that has smaller padding, margin, and font-size.

---

## Step 2: Generate a ZUL File

### Generation Guidelines

When generating the ZUL file, follow these technical guidelines:

1. **Map UI Elements**: Consult [references/ui-to-component-mapping.md](references/ui-to-component-mapping.md) to choose the correct ZK components. 
   - Prioritize ZK components over native HTML.
   - Use layout components like `<borderlayout>`, `<vlayout>`, and `<hlayout>` effectively.
2. **Handle CSS Inclusion**: 
   - If fallback native HTML elements (e.g. `<n:div>`) are used, identify and include the necessary CSS.
   - Use the `<style>` element for inline CSS; **do not** use the `<?style ?>` processing instruction.
3. **ZK Documentation**:
   - Query `zk-doc-mcp-server` for detailed component info if available.
   - Use [ZK Javadoc](https://www.zkoss.org/javadoc/latest/zk/) for properties and event details.
4. **Best Practices**:
   - Prefer `hflex`/`vflex` over fixed pixel widths for responsive layouts. `hflex="min"` sizes a component to fit its content — useful for a `<button>` sitting beside an `hflex="1"` field (see [assets/flexible-sizing.zul](assets/flexible-sizing.zul)).
   - Use meaningful IDs and follow the [assets/template.zul](assets/template.zul) structure.


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
- Layer 4: version compatibility checks for the target ZK version — removed/deprecated API for all targets, plus ZK-10-only API (e.g. dropped `<fragment>`, or new `accept`/`responsive` attributes) gated by `--zk-version`. Defaults to `10` if omitted.

### Prerequisites
Layer 2 and 3 require `lxml`. **`uv run` handles this automatically** via the script's PEP 723 inline metadata — it provisions `lxml` in an ephemeral environment, so no manual setup is needed. If `uv` is unavailable, run with a plain interpreter instead and the script self-installs `lxml` as a fallback:

```bash
python3 <skill-base-dir>/scripts/validate-zul.py --zk-version <detected-version> <path-to-zul-file>
```
(On Windows, use `python` instead of `python3`.)

### Usage Tracking
Running this script also fires an anonymous, aggregate usage ping (skill name + version only, no identifier) on a background thread — it never delays or blocks validation. Opt out with `DO_NOT_TRACK=1` or `TRACK_URL=""`.

### Post-Validation Checklist

#### Pattern Consistency
- **MVC**: Uses `apply` attribute, no MVVM binding expressions
- **MVVM**: Uses `viewModel` attribute, proper binding syntax
- No mixing of patterns on same component

#### Best Practices
- IDs are unique within each ID space owner (`<window>`, `<idspace>`)
- Prefer `sclass` over inline styles
- Prefer `hflex`/`vflex` over fixed dimensions
- Include meaningful labels and tooltips for accessibility


## Step 4: Generate Controller Class

Generate the corresponding Java controller class (ViewModel or Composer) for the ZUL page. 

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

Run the preview script from this skill's base directory (same convention as Step 3):

```bash
uv run <skill-base-dir>/scripts/preview-zul.py --out <path-to-png> <path-to-zul-file>
```

Example: if the skill base directory is `~/.claude/skills/zul-writer/` and the page lives in a Maven webapp, run:
```bash
uv run ~/.claude/skills/zul-writer/scripts/preview-zul.py --out /tmp/zul-preview.png src/main/webapp/index.zul
```

If this session wrote the page's controller, append `--run-controllers` (read the next paragraph
before you do — it executes project code):
```bash
uv run ~/.claude/skills/zul-writer/scripts/preview-zul.py --run-controllers --out /tmp/zul-preview.png src/main/webapp/index.zul
```

**When to pass `--run-controllers`.** Pass it when this session wrote the page's controller
(Step 4's composer or ViewModel): the sample data in it is yours, running it is what turns a
skeleton screenshot into a judgeable one, and the flag makes bound values, model-bound rows and
composer-filled labels real. Do **not** pass it for a page whose controller you did not write —
the flag **executes arbitrary project code** from the project's classpath (constructors, service
calls, whatever `doAfterCompose` does), so it is opt-in per render and never a default. If the
controller has not been compiled yet, build first (`mvn compile` / `gradle classes`); the script
warns when no compiled classes are on the classpath. Add `--controller-timeout <seconds>` only if
a legitimately slow page keeps degrading (the default budget is 10 s for the whole render).

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

### What to fix

Judge **structure**, not pixels and not data. Fix only these:

- **An error page instead of the page** (the script exits 1 and prints `PHASE`, `MESSAGE` and `LOCATION`). A real ZUL bug — fix it at the reported location.
- **"Unknown component `<x>`"** — the jar defining that component is not on the classpath. Either the tag is a typo, or an add-on dependency is missing; ask the user rather than deleting the component.
- **Missing or extra sections** compared with what Step 1 asked for.
- **Wrong region placement** — a sidebar rendered under the content, a missing header, tab content sitting outside its `<tabpanel>`.
- **Wrong component choice** — a data table rendered as a plain stack of labels, a form field that isn't the input type requested.
- **Broken layout** — content clipped or overflowing, a horizontal scrollbar on a page meant to fit, a region collapsed to zero height, widgets overlapping, an `hflex`/`vflex` that visibly did not take.
- **Raw unstyled HTML** where a ZK component was intended.
- **`CONTROLLERS: failed → isolated`** — read the `WARNINGS` entry: it names the failing class and
  the first cause line. A controller exception, a missing class or a blown budget is a defect in the
  **controller** (or a missing build), not in the ZUL. Fix it there and re-render, or report it —
  never work around it by hard-coding values into the markup. The exit code is still 0 and the
  screenshot is still valid; it just shows the isolated render.

### What you cannot judge from this image

The preview renders the **first paint only**. With `CONTROLLERS: skipped (isolated)` or
`failed → isolated` it also runs **no ViewModel and no Composer**, and everything below is the
renderer behaving correctly. Do **not** "fix" it, do not report it as a flaw, and do not let it
drive a re-render:

- **Bound values shown as dimmed expression text** (e.g. a literal `vm.customer` inside a textbox) — the ViewModel never runs.
- **Placeholder rows** in a `<grid>`/`<listbox>`/`<tree>` whose `model` is bound (e.g. rows reading `each.product`) — dimmed sample rows keep the component's real geometry.
- **A whole section missing where an `<include>` has a bound `src`** — this one is *not* placeholdered. A constant literal (`src="@load('~./page.zul')"`) is included for real; anything the ViewModel supplies (`src="@load(vm.page)"`) leaves `src` unset, so the include contributes **nothing** and you see a silent gap, not dimmed text. Adding a hard-coded `src` to "fix" the gap breaks the real page.
- **Anything a Composer or ViewModel would populate** — default values, initial selections, computed labels, i18n text. `apply="..."` composers are no-ops here.
- **Anything requiring a server round-trip** — button clicks, paging, sorting, tree expansion, selection highlighting, a `<window>` or popup opened by an event. Only the first-paint state exists. Client-side `w:` handlers *do* run, and so does `<zscript>`.
- **Missing images, fonts or `~./` resources** — the docroot is inferred, so assets outside it 404 in the preview but load fine on a real server.
- **Theme-dependent colours and spacing** when the theme jar isn't a project dependency.
- **Exact spacing, font rendering, sub-pixel alignment, or a colour that is merely close** to the mockup.
- **Data content from the mockup** — sample data will differ. Compare the *shape* of the UI, not the values in it.

**Under `CONTROLLERS: executed`, the first four bullets above no longer apply** — dimmed expression
text, placeholder rows, the missing bound-`src` section and "anything a Composer or ViewModel would
populate" are all real output now. There, a bound field rendered blank, a data table with no rows,
or a section still missing **is a defect** — in the controller if it never supplied the value, in
the ZUL if the binding names the wrong property. Everything from *"Anything requiring a server
round-trip"* down still holds in both modes.

### How many rounds

- **At most two fix rounds — three renders total.** Round 1: render, read, list defects from *What to fix*. Fix them, re-run Step 3 validation, re-render. Round 2: same. Then stop.
- **Fix only whole defects from that list.** If your list is empty, or everything left on it is in *What you cannot judge*, the page is good enough — say so in one line and stop. "Good enough" means every requirement from Step 1 is visibly present, in the right region, in the right kind of component, and nothing is clipped or overlapping.
- **Never edit the ZUL for a cosmetic difference alone.** Chasing pixels against a mockup costs rounds and regresses working markup.
- If a defect survives both rounds, **stop and tell the user** what it is and what you tried. Do not keep rendering.
- Report the final image path so the user can look at it themselves.

For classpath resolution details, the docroot rules, and what each `PREVIEW_SKIPPED` reason means, see [references/preview-guidelines.md](references/preview-guidelines.md).