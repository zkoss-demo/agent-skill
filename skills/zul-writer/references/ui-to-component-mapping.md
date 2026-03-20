# UI Element to ZK Component Mapping

Map visual UI elements from screenshots/mockups to ZK components. Use ZK components first; fall back to `<div>` + CSS only when no suitable ZK component exists.

## Layout Components

| UI Pattern | ZK Component | Notes |
|---|---|---|
| Vertical stack | `<vlayout>` | **Priority.** Use first for most layouts. For alignment, use CSS `text-align` in `style`. |
| Horizontal row | `<hlayout>` | **Priority.** Use first for most layouts. For vertical alignment, use `z-valign-top`, `z-valign-middle`, or `z-valign-bottom`. |
| Header / sidebar / content regions | `<borderlayout>` with `<north>`, `<west>`, `<center>` | Use for full-page or complex structural layouts |
| Navigation tabs (tabs that switch visible content) | `<tabbox>` with `<tabs>` + `<tabpanels>` | All content below the tab strip belongs INSIDE `<tabpanel>` — never place it as siblings outside `<tabbox>` |
| Accordion | `<tabbox mold="accordion">` | |
| Splitter panels | `<splitlayout>`  | |
| Card / panel | `<groupbox>` or `<panel>` | `<groupbox>` for titled sections |
| Column-based alignment | `<hbox>` or `<vbox>` | **Avoid.** Planned for deprecation. Use `<hlayout>`/`<vlayout>` with CSS instead. |
| Grid-aligned form | `<grid>` with `<columns>` + `<rows>` | Label + input pairs requiring strict tabular alignment |

## Data Display

| UI Pattern | ZK Component | Notes |
|---|---|---|
| Data table with selectable items | `<listbox>` with `<listhead>` + `<listitem>` | Use `mold="paging"` for pagination |
| Data table (no selection) | `<grid>` | Use `mold="paging"` for pagination |
| Editable data table | `<grid>` with inline inputs | Or `<listbox>` with custom template |
| Tree view | `<tree>` with `<treecols>` + `<treechildren>` | |
| Paginated list | `<listbox mold="paging" pageSize="N">` | |
| Detail view | `<grid>` or `<vlayout>` with label/value pairs | |

## Form Inputs

| UI Pattern | ZK Component | Notes |
|---|---|---|
| Text field | `<textbox>` | |
| Password field | `<textbox type="password">` | |
| Multi-line text | `<textbox multiline="true" rows="N">` | |
| Dropdown / select | `<combobox>` or `<selectbox>` | `<combobox>` supports autocomplete |
| Checkbox | `<checkbox>` | |
| Radio buttons | `<radiogroup>` with `<radio>` | |
| Date picker | `<datebox>` | |
| Time picker | `<timebox>` | |
| Number input | `<intbox>`, `<decimalbox>`, `<doublebox>`, `<spinner>` | Choose by data type |
| Slider | `<slider>` | |
| File upload | `<button upload="true">` | |
| Toggle switch | `<checkbox>` with `mold="toggle"` (ZK 10) or `<switch>` | Check ZK version |
| Rich text editor | `<ckeditor>` (requires ZK PE/EE) | |

## Actions & Navigation

| UI Pattern | ZK Component | Notes |
|---|---|---|
| Button | `<button>` | Use `iconSclass` for icon buttons |
| Icon button | `<button iconSclass="z-icon-xxx">` | Font Awesome icons |
| Toolbar | `<toolbar>` with `<toolbarbutton>` | |
| Menu bar | `<menubar>` with `<menu>` + `<menupopup>` | |
| Context menu | `<menupopup>` attached via `context` attribute | |
| Breadcrumb | No direct component | Use `<hlayout>` with `<a>` + separators |
| Pagination | `<paging>` standalone or `mold="paging"` on listbox | |

## Feedback & Overlays

| UI Pattern | ZK Component | Notes |
|---|---|---|
| Modal dialog | `<window mode="modal">` | |
| Alert / notification | `Clients.showNotification()` (Java) | Not a ZUL element |
| Tooltip | `tooltip` attribute or `<popup>` | |
| Progress bar | `<progressmeter>` | |
| Loading spinner | `<busyOverlay>` or custom CSS | |
| Badge / tag | No direct component | Use `<label sclass="...">` + CSS |
| Popover | `<popup>` | |

## Common Mistakes — Do NOT Use Native HTML For These

- **Tab-like navigation** → Use `<tabbox>`, not `<n:button class="tab">`
- **Dropdown menus** → Use `<combobox>` or `<menubar>`, not `<n:select>`
- **Data tables** → Use `<listbox>` or `<grid>`, not `<n:table>`
- **Modal dialogs** → Use `<window mode="modal">`, not `<n:div class="modal">`
- **Layout alignment** → Use `<vlayout>` with CSS `text-align` or `<hlayout>` with `z-valign-*`, not `<vbox>`/`<hbox>` or complex `<grid>` tables.

## Fallback Strategy: HTML + CSS

When a UI control cannot be mapped to an existing ZK component, you can construct it by combining HTML elements with custom CSS.

However, there is a crucial consideration: **whether this UI control needs to send events to the server.**

1. **Requires server events:** Use ZK's own `<div>` or `<span>`.
2. **No server events needed:** Use native HTML elements( e.g. `<n:div>` and `<n:span>` with the native namespace).

```xml
<!-- Example 1: No events needed, using native HTML -->
<n:div class="custom-card" xmlns:n="native">
    <n:div class="card-header">Title</n:div>
    <n:div class="card-body">
        <!-- ZK components inside native divs work fine -->
        <textbox hflex="1"/>
    </n:div>
</n:div>

<!-- Example 2: Click event needed, using ZK components -->
<div sclass="custom-clickable-card" onClick="@command('handleCardClick')">
    <div sclass="card-header">Interactive Title</div>
</div>
```

Common fallback scenarios:
- **Breadcrumbs**: `<n:nav>` with `<a>` links
- **Badges/tags**: `<n:span class="badge">` or `<label>` with sclass
- **Cards with custom layouts**: `<n:div class="card">`
- **Hero/banner sections**: `<n:section>` with CSS
- **Custom grid layouts**: `<n:div style="display: grid; ...">` when `<hlayout>`/`<vlayout>` insufficient
- **Progress steps / wizard indicators**: `<n:ol class="steps">`

Always include the companion CSS with `<style>` element when using fallback components. Do not use `<?style ?>` processing instruction.