---
name: zul-writer
description: Helps users write ZUL pages of ZK Framework through a structured workflow
context: fork
---
# ZUL Writer


## Workflow Overview

This skill guides users through a 3-step process to create well-structured ZUL pages:

1. **Clarify Requirements** - Gather information about the page purpose and technical needs
2. **Generate ZUL** - Create the ZUL file based on gathered requirements
3. **Validate** - Verify correctness and suggest companion Java classes.

---

## Step 1: Clarify User Requirements

### Purpose
Ask targeted questions to understand user needs before generating any code. This ensures the generated ZUL matches the user's exact requirements.

### Questions to Ask

#### 1. ZK Version
Try to detect it from user's project, if not found, ask user
```
Which ZK version are you using?
- 9 or before
- 10.x
```
**Why it matters**: Different versions have different components and features available.


#### 2. Page Purpose
```
What is the purpose of this page?
- Data entry form
- Data list/grid display
- Dashboard with multiple sections
- Dialog/popup window
- Master-detail view
- Search and results page
- Other: [specify]
```

#### 3. Layout Requirements
```
What layout structure do you need?
- Borderlayout (north/south/east/west/center)
- Vertical layout (vlayout)
- Horizontal layout (hlayout)
- Grid-based layout
- Tabbed layout (tabbox)
- Combined layouts
```

---

## Step 2: Generate ZUL File

### Generation Guidelines
find proper component for UI requirements:
* if users have installed zk-doc-mcp-server, ask it for component information when needed
* Find component and their property from javadoc at https://www.zkoss.org/javadoc/latest/zk/
* don't specify `hflex="min"` on button for it's `display: inline-block`

#### XML Structure
Always start with proper XML declaration and ZK namespaces like assets/template.zul


#### MVC Pattern Structure
See assets/mvc-sample.zul

#### MVVM Pattern Structure
assets/mvvm-pattern-structure.zul

### Layout Best Practices

#### Use Flexible Sizing
assets/flexible-sizing.zul

#### Borderlayout Example
assets/borderlayout-example.zul

### Component Usage Example - MVVM Pattern

* [Form with Validation](assets/form-validation-mvvm.zul)
* [Data Grid with Selection](assets/data-grid-selection-mvvm.zul)
* [Master-Detail Pattern](assets/master-detail-mvvm.zul)
* [Dialog/Popup](assets/dialog-popup-mvvm.zul)

---

## Step 3: Validate Generated ZUL
validate generated ZUL file with scripts/validate-zul.py
- Layer 1: XML well-formatted (no dependencies)
- Layer 2: XSD schema validation (requires `lxml`)
- Layer 3: ZK 10 compatibility checks (ONLY required if target ZK version is 10)

### Prerequisites
Layer 2 (XSD schema validation) requires the `lxml` Python library. If the validation script reports that `lxml` is not installed, follow this sequence:

1. **Check for `uv`**: Run `which uv` to detect if `uv` is available.
2. **If `uv` is available**: Install with `uv pip install lxml` and run the validation script via `uv run`.
3. **If `uv` is NOT available**: Ask the user if they'd like to install `uv` first (see https://docs.astral.sh/uv/getting-started/installation/).
4. **If the user declines `uv`**: Fall back to `pip install lxml` (or `pip3 install lxml`).

Do NOT skip Layer 2 silently. Always inform the user that schema validation was skipped due to the missing dependency and guide them through installation so full validation can run.

### Validation Checklist

#### ZK Namespace Declarations
- [ ] Additional namespaces as needed:
  - Native HTML: `xmlns:n="native"`
  - Client-side: `xmlns:w="client"`
  - Annotation: `xmlns:a="client/attribute"`

#### Pattern Consistency
- [ ] **MVC**: Uses `apply` attribute, no MVVM binding expressions
- [ ] **MVVM**: Uses `viewModel` attribute, proper binding syntax
- [ ] No mixing of patterns (e.g., don't use `apply` and `viewModel` on same component)

#### Attribute Validation
- [ ] `hflex`/`vflex` values are valid (`1`, `min`, `2`, etc.)
- [ ] `constraint` syntax is correct
- [ ] Event handlers use correct prefixes (`onClick`, `onChange`, etc.)
- [ ] MVVM commands use `@command('methodName')` syntax
- [ ] Data binding uses correct annotations (`@load`, `@save`, `@bind`)

#### Best Practices
- [ ] IDs are unique within one ID space owner : `<window>`, `<idspace>`
- [ ] Avoid inline styles where possible (use `sclass`)
- [ ] Use `hflex`/`vflex` instead of fixed dimensions
- [ ] Include meaningful labels and tooltips for accessibility

### Companion Java Class Suggestions

#### For MVC Pattern - Composer Class example
See assets/MyComposer.java

#### For MVVM Pattern - ViewModel Class
See assets/MyViewModel.java
---

## Complete Examples

### Example 1: Simple Form (MVVM)
assets/example-simple-form-mvvm.zul

### Example 2: Data Management Page (MVVM)
assets/example-data-management-mvvm.zul

### Example 3: Simple List Page (MVC)
assets/example-simple-list-mvc.zul

---

## Quick Reference

### MVVM Binding Annotations
| Annotation | Usage | Example |
|------------|-------|---------|
| `@load` | One-way (VM to View) | `value="@load(vm.name)"` |
| `@save` | One-way (View to VM) | `value="@save(vm.name)"` |
| `@bind` | Two-way binding | `value="@bind(vm.name)"` |
| `@command` | Method invocation | `onClick="@command('save')"` |
| `@global-command` | Global command | `onClick="@global-command('refresh')"` |

### Common Constraints
| Constraint | Description |
|------------|-------------|
| `no empty` | Cannot be empty |
| `no negative` | No negative numbers |
| `no zero` | No zero value |
| `no positive` | No positive numbers |
| `/regex/` | Must match regex |
| `min X` | Minimum value X |
| `max X` | Maximum value X |

### Sizing Attributes
| Attribute | Description | Example |
|-----------|-------------|---------|
| `hflex` | Horizontal flexibility | `hflex="1"`, `hflex="min"` |
| `vflex` | Vertical flexibility | `vflex="1"`, `vflex="min"` |
| `width` | Fixed width | `width="200px"`, `width="50%"` |
| `height` | Fixed height | `height="300px"` |
