# Use Case Guidelines

This document provides patterns for complex UI scenarios in ZK. Use these as a reference when composing multiple components to solve specific business requirements.

## Pattern 1: Kanban Board

A Kanban board typically uses a horizontal layout of columns, where each column contains a list of tasks.

### Recommended Components
*   **Container**: [`<portallayout>`](https://www.zkoss.org/javadoc/latest/zk/org/zkoss/zkmax/zul/Portallayout.html) or `<hlayout>` with `hflex="1"`.
*   **Columns**: [`<portalchildren>`](https://www.zkoss.org/javadoc/latest/zk/org/zkoss/zkmax/zul/Portalchildren.html) or `<vlayout>`.
*   **Task Cards**: `<panel>` or `<groupbox>` with custom styling.
`<panel>` is draggable in a `<portallayout>`.

### Examples
*   [Kanban Board ZUL](../assets/kanban-board.zul)
*   [Kanban ViewModel](../assets/KanbanViewModel.java)

If `<portallayout>` approach doesn't fit your needs or is not available, then you can use `<div>` instead, make sure to specify `draggable="true"` on each card `<div>` and `drop="true"` on each column `<div>`.
---

## General Use Cases & Reference Assets

Use these complete examples as templates for common page types.

### 1. Simple Form (MVVM)
Focuses on data entry, validation, and layout using `<grid>`.
*   [Template](../assets/example-simple-form-mvvm.zul)
*   [Validation Guide](../assets/form-validation-mvvm.zul)

### 2. Data Management (MVVM)
A comprehensive page with search, results grid, and CRUD actions.
*   [Template](../assets/example-data-management-mvvm.zul)
*   [Grid Selection patterns](../assets/data-grid-selection-mvvm.zul)

### 3. simple List (MVC)
A straightforward listing page using the MVC pattern with a Composer.
*   [Template](../assets/example-simple-list-mvc.zul)
*   [MVC structure](../assets/mvc-sample.zul)

---

## Pattern 2: Dashboards

Dashboards often require flexible, tile-based layouts.

### Recommendations
*   Use `Portallayout` if users should be able to drag-and-drop tiles.
*   Use nested `<vlayout>` and `<hlayout>` with `hflex`/`vflex` for fixed dashboards.
*   Consult [references/charts-dependency.md](charts-dependency.md) if adding data visualizations.
