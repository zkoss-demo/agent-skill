# Showcase gallery: generate ZULs for the remaining mockups

## Context

`zulwriter-showcase/ui-screenshots/` holds 9 mockups. Two already have pages:

| Mockup | Page | Pattern | Data |
|---|---|---|---|
| AppTracker.png | `app-tracker.zul` | MVC | literal |
| enterprise kanban board.png | `kanban-board.zul` | MVVM | literal |

The remaining 7 are to be generated: half MVC, half MVVM, **all model-driven**.

## Step 1 answers (shared across all 7 pages)

| Question | Answer | Source |
|---|---|---|
| 1. ZK version | **10.3.0.1-Eval** | `zulwriter-showcase/pom.xml` `<zk.version>` |
| 2. Page purpose | per page, read from the mockup | the images |
| 3. MVC / MVVM | **user-specified: half and half** | user's message (overrides `detect-pattern.py`, which reported `mixed (MVC 7, MVVM 4)` → `USE: mvc`) |
| 4. Static or model-driven | **model-driven, all 7** | user's message |
| 5. Layout | per page, derived from the mockup | the images |
| 6. ZK Charts | **available** — `org.zkoss.chart:zkcharts:12.2.0.0-Eval` is already a dependency | `pom.xml` |
| 7. Theme / density | **keep the project theme** (no `iceblue_c` switch) | switching repaints every existing page |

No defaults from the *"when there is no one to ask"* table were needed: every question was
answered by the user, the build file, or the mockup.

## Pattern assignment

Balanced across the whole gallery (9 pages → MVC 4, MVVM 5).

| # | Mockup | New page | Pattern | Model-driven via |
|---|---|---|---|---|
| 1 | Task Master.png | `task-master.zul` | MVVM | `<tree model>` + `<forEach items="@load(vm.tasks)">` cards |
| 2 | Feedback Dashboard.png | `feedback-dashboard.zul` | MVVM | `<charts model>` ×2 + bound progress/labels |
| 3 | Data Comparison Modal.png | `data-comparison-modal.zul` | MVVM | `<grid model>` + `<template name="model">` |
| 4 | Data Analytics Dashboard.png | `data-analytics-dashboard.zul` | MVVM | `<forEach>` KPI cards + `<charts model>` ×2 + `<grid model>` |
| 5 | Bank Reconciliation Dashboard.png | `bank-reconciliation.zul` | MVC | Composer `setModel()` on a wired `<listbox>` |
| 6 | Test Case Management.png | `test-case-management.zul` | MVC | Composer `setModel()` on a wired `<tree>` + `<grid>` |
| 7 | Application Review.png | `application-review.zul` | MVC | Composer sets the wired detail labels |

## Verified before writing any markup

- `<forEach items="@load(vm.x)" var="y">` repeats a ViewModel collection — probed with a throwaway
  page + ViewModel, rendered `CONTROLLERS: executed`, 3 cards laid out across an `hlayout`.
  Probe files deleted afterwards.
- `<forEach>` schema: accepts `begin, end, items, step, var, varStatus`.
- `<charts>` takes `className`/`zclass`, **not** `sclass`; takes `model`; no `width` needed (100% by default).
- zkcharts models present in the jar: `DefaultCategoryModel`, `DefaultXYModel`, `DefaultPieModel`.
- Icon classes go on `<span>`/`<div>` carriers or `iconSclass` — never on `<label>`.
- Toolchain: `withjdk.sh 17 mvn -o compile`, then `withjdk.sh 17 uv run .../preview-zul.py`.
  Default `java` on this machine is 11, which the preview rejects.

## Per-page procedure

For each page, in order:

1. Visual analysis of the mockup → component/layout plan.
2. **Pass 1** — write the ZUL with literal data, shaped like the real data.
3. Validate: `validate-zul.py --zk-version 10.3.0.1-Eval --dev <page>`.
4. Write the controller — **behaviour only**, no data.
5. Render at the mockup's width (`--width 1600`, `--width 1280` for Feedback Dashboard, whose PNG is
   a 2× export) and self-review. Fix rounds until the layout is settled (budget: 4).
6. **Pass 2** — extract the literals into the controller, point the ZUL at them, delete the literal
   rows.
7. Validate with `--controller` (Layer 7), then re-render with `--run-controllers` once.

## Checklist

- [x] Toolchain + schema + `<forEach>` probe
- [x] `task-master.zul` + `TaskMasterViewModel` (MVVM)
- [x] `feedback-dashboard.zul` + `FeedbackDashboardViewModel` (MVVM)
- [x] `data-comparison-modal.zul` + `DataComparisonViewModel` (MVVM)
- [x] `data-analytics-dashboard.zul` + `DataAnalyticsViewModel` (MVVM)
- [x] `bank-reconciliation.zul` + `BankReconciliationComposer` (MVC)
- [x] `test-case-management.zul` + `TestCaseManagementComposer` (MVC)
- [x] `application-review.zul` + `ApplicationReviewComposer` (MVC)

## Open question for the user

The two pre-existing pages (`app-tracker.zul`, `kanban-board.zul`) hold their data as literal
markup, not model-driven. Converting them was not asked for and is not in this scope — see the
report's decision section.

## Review

All seven pages built, both passes each. Every page passes validator layers 1-7 (with
`--controller`), and `mvn clean compile` is green.

| Page | Pattern | Pass 1 fix rounds | Pass 2 fix rounds |
|---|---|---|---|
| `task-master.zul` | MVVM | 1 (tree indentation + duplicate carets) | 0 |
| `feedback-dashboard.zul` | MVVM | 0 | 0 |
| `data-comparison-modal.zul` | MVVM | 2 (middle-column tint; 1st aimed at the wrong selector) | 0 |
| `data-analytics-dashboard.zul` | MVVM | 0 | 0 |
| `bank-reconciliation.zul` | MVC | 1 (DATE column wrapped, doubling row height) | 1 (model reset multi-select; % truncation) |
| `test-case-management.zul` | MVC | 2 (3 folders open vs design; column clipping) | 2 (tree template EL; `--` in an XML comment) |
| `application-review.zul` | MVC | 1 (page background did not fill the viewport) | 0 |

No page reached the four-round backstop in either pass.

### Things measured along the way, worth keeping

1. **A grid's data cells are `td.z-row-inner`, not `.z-cell`.** Two rules aimed at `.z-cell`
   painted nothing at all; the DOM dump settled it. `.z-cell` is what an explicit `cell`
   component renders.
2. **A tree template's EL variable is always `each`, and it is the `TreeNode`.** A custom
   `var="..."` is silently ignored on the plain-EL (MVC) path, so expressions through it render
   empty instead of failing — which is why this cost two rounds before being probed. The MVVM
   binder *does* honour `var`. So: MVC writes `${each.data.x}`, MVVM writes `@load(node.data.x)`.
3. **`selectedIndex="0"` on a `<combobox>` throws even when the markup has `<comboitem>`
   children** — the attribute is applied before the children exist. Layer 6 only fires when there
   are no items in the markup at all, so it passed this page and the render caught it. Use
   `value="..."` on a readonly combobox instead.
4. **`Listbox.setModel()` copies the model's own `multiple` flag onto the listbox**, and
   `ListModelList` defaults to single selection — silently overruling `multiple="true"` in the
   ZUL and turning a `checkmark` column into radio buttons. Call `model.setMultiple(true)`.
5. **The bundled XSD rejects a model-driven `<tree>` whose only child is a `<template>`** —
   `treeType` requires a `treecols` or `treechildren` once the tree has any child. An empty
   `<treechildren/>` satisfies it and the model still fills the tree.
6. **ZK Charts chrome must come from the controller, not from ZUL text.** `legend="false"` throws
   `ClassCastException` (it wants a `Legend` object); `colors="#3b82f6"` finds no setter. Bind
   `Legend` / `Credits` / `Exporting` / `List<Color>` / `PlotOptions` from the controller instead.
   `yAxis` is *not* usable: Layer 3 rejects it on `<charts>`, so axis chrome stays ZK-default.
7. **`<forEach items="@load(vm.x)" var="y">`** repeats a ViewModel collection and is the way to
   build a wrapping card grid from a model — no model-bearing component required.
8. **`<checkbox mold="switch">`** is a real ZK 10 mold (confirmed in `zul.jar`'s `lang.xml`), and
   renders the design's toggle without any custom CSS.
