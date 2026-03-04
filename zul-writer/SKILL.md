---
name: zul-writer
description: Generate ZK Framework ZUL pages through a structured workflow. Use when users want to create ZUL files, convert UI designs/screenshots/mockups into ZUL code, build forms/grids/dashboards with ZK components, or need help with ZK layout and data binding (MVC or MVVM). Triggers on requests involving ZUL, ZK pages, or UI-to-ZUL conversion from images.
---
# ZUL Writer

## Workflow Overview

This skill creates well-structured ZUL pages through a 3-step process:

1. **Clarify Requirements** - Gather page purpose, pattern, and layout needs
2. **Generate ZUL** - Create the ZUL file based on requirements
3. **Validate** - Verify correctness and suggest companion Java classes

**Alternative entry**: When user provides a UI image (screenshot/mockup), skip to the image-to-ZUL workflow below.

---

## Step 1: Clarify User Requirements

Ask targeted questions to understand needs before generating code.

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

If the ZUL page requires a `<charts>` component, read [references/charts-dependency.md](references/charts-dependency.md) and follow the dependency-check steps before generating any chart code.

---

## Image-to-ZUL Workflow

When user provides a UI screenshot or mockup image:

1. **Analyze the image** - Identify all visible UI elements: layout structure, input fields, buttons, data tables, navigation, labels, icons
2. **Map to ZK components** - Consult [references/ui-to-component-mapping.md](references/ui-to-component-mapping.md) for element-to-component mapping. Prioritize ZK components; fall back to `<n:div>` + CSS only when no suitable ZK component exists
3. **Identify tab content scope** - When tabs are present, determine what content belongs inside each `<tabpanel>`:
   - **Content tabs** (tabs that switch visible content below): all content below the tab strip up to the next major layout boundary belongs INSIDE `<tabpanel>`, not as siblings outside `<tabbox>`. See [assets/content-tabbox.zul](assets/content-tabbox.zul)
   - **Navigation-only tabs** (top menu bars, routing tabs): use empty `<tabpanel/>` elements
4. **Infer layout** - Determine the overall layout structure (borderlayout, vlayout/hlayout nesting, grid)
5. **Ask clarifications** - Confirm ZK version and MVC/MVVM preference if not already known. Ask about any ambiguous UI elements
6. **Generate ZUL** - Proceed to Step 2 with the analyzed requirements
7. **Include CSS** - When fallback `n:div` elements are used, include companion CSS via `<style>` element (not `<?style ?>` processing instruction)

---

## Step 2: Generate ZUL File

### Generation Guidelines
Find proper components for UI requirements:
* If users have installed zk-doc-mcp-server, query it for component information
* Find components and properties from javadoc at https://www.zkoss.org/javadoc/latest/zk/
* Don't specify `hflex="min"` on `<button>` — it's `display: inline-block` by default
* Use `<style>` element for inline CSS, not `<?style ?>` processing instruction

#### XML Structure
Always start with proper XML declaration and ZK namespaces: [assets/template.zul](assets/template.zul)

#### MVC Pattern Structure
[assets/mvc-sample.zul](assets/mvc-sample.zul)

#### MVVM Pattern Structure
[assets/mvvm-pattern-structure.zul](assets/mvvm-pattern-structure.zul)

### Layout Best Practices

#### Use Flexible Sizing
[assets/flexible-sizing.zul](assets/flexible-sizing.zul)

#### Borderlayout Example
[assets/borderlayout-example.zul](assets/borderlayout-example.zul)

### Component Usage Examples - MVVM Pattern

* [Form with Validation](assets/form-validation-mvvm.zul)
* [Data Grid with Selection](assets/data-grid-selection-mvvm.zul)
* [Master-Detail Pattern](assets/master-detail-mvvm.zul)
* [Dialog/Popup](assets/dialog-popup-mvvm.zul)

---

## Step 3: Validate Generated ZUL

Run validation: `scripts/validate-zul.py`
- Layer 1: XML well-formedness (no dependencies)
- Layer 2: XSD schema validation (requires `lxml`)
- Layer 3: Attribute placement check (requires `lxml`) - catches misplaced attributes (e.g. `iconSclass` on `textbox`)
- Layer 4: ZK 10 compatibility checks (only if target ZK version is 10)

### Prerequisites
Layer 2 and 3 require `lxml`. If missing:

1. Check for `uv`: `which uv`
2. If `uv` available: `uv pip install lxml`, run script via `uv run`
3. If `uv` not available: ask user to install `uv` (https://docs.astral.sh/uv/getting-started/installation/)
4. If user declines `uv`: fall back to `pip install lxml`

Do NOT skip Layer 2 silently. Always inform the user and guide through installation.

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

### Controller Java Class Suggestions

#### MVC Pattern - Composer Class
[assets/MyComposer.java](assets/MyComposer.java)

#### MVVM Pattern - ViewModel Class
[assets/MyViewModel.java](assets/MyViewModel.java)

---

## Complete Examples

* [Simple Form - MVVM](assets/example-simple-form-mvvm.zul)
* [Data Management Page - MVVM](assets/example-data-management-mvvm.zul)
* [Simple List Page - MVC](assets/example-simple-list-mvc.zul)
