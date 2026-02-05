---
name: zul-writer
description: Helps users write ZUL pages for the ZK Framework through a structured workflow
context: fork
---
# ZUL Writer


## Workflow Overview

This skill guides users through a 3-step process to create well-structured ZUL pages:

1. **Clarify Requirements** - Gather information about the page purpose and technical needs
2. **Generate ZUL** - Create the ZUL file based on gathered requirements
3. **Validate** - Verify correctness and suggest companion Java classes

---

## Step 1: Clarify User Requirements

### Purpose
Ask targeted questions to understand user needs before generating any code. This ensures the generated ZUL matches the user's exact requirements.

### Questions to Ask

#### 1. ZK Version
```
Which ZK version are you using?
- ZK 8.x (EE/CE)
- ZK 9.x (EE/CE)
- ZK 10.x (EE/CE)
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
* if users have installed zk-doc mcp server, ask it for component information
#### XML Structure
Always start with proper XML declaration and ZK namespaces:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?page title="Page Title"?>
<zk xmlns="http://www.zkoss.org/2005/zul"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.zkoss.org/2005/zul http://www.zkoss.org/2005/zul/zul.xsd">

    <!-- Page content here -->

</zk>
```

#### MVC Pattern Structure
```xml
<window id="mainWin" title="Page Title" border="normal"
        apply="com.example.controller.MyComposer">
    <!-- Components with id attributes for wire binding -->
    <textbox id="nameInput"/>
    <button id="submitBtn" label="Submit"/>
</window>
```

#### MVVM Pattern Structure
```xml
<window id="mainWin" title="Page Title" border="normal"
        viewModel="@id('vm') @init('com.example.viewmodel.MyViewModel')">
    <!-- Components with data binding expressions -->
    <textbox value="@bind(vm.name)"/>
    <button label="Submit" onClick="@command('submit')"/>
</window>
```

### Layout Best Practices

#### Use Flexible Sizing
```xml
<!-- Good: Use hflex/vflex for responsive layouts -->
<hlayout>
    <textbox hflex="1"/>
    <button label="Search" hflex="min"/>
</hlayout>

<!-- Avoid: Fixed pixel widths -->
<hlayout>
    <textbox width="300px"/>
    <button label="Search" width="80px"/>
</hlayout>
```

#### Borderlayout Example
```xml
<borderlayout>
    <north height="60px" border="none">
        <div>Header content</div>
    </north>
    <west width="200px" splittable="true" collapsible="true">
        <div>Navigation</div>
    </west>
    <center border="none">
        <div>Main content</div>
    </center>
    <south height="30px" border="none">
        <div>Footer</div>
    </south>
</borderlayout>
```

### Component Patterns

#### Form with Validation (MVVM)
```xml
<grid>
    <columns>
        <column width="120px"/>
        <column/>
    </columns>
    <rows>
        <row>
            <label value="Name:"/>
            <textbox value="@bind(vm.user.name)"
                     constraint="no empty: Name is required"
                     hflex="1"/>
        </row>
        <row>
            <label value="Email:"/>
            <textbox value="@bind(vm.user.email)"
                     constraint="/.+@.+\..+/: Invalid email format"
                     hflex="1"/>
        </row>
        <row>
            <label value="Age:"/>
            <intbox value="@bind(vm.user.age)"
                    constraint="no negative,no zero"
                    hflex="1"/>
        </row>
    </rows>
</grid>
<hlayout style="margin-top: 10px">
    <button label="Save" onClick="@command('save')"/>
    <button label="Cancel" onClick="@command('cancel')"/>
</hlayout>
```

#### Data Grid with Selection (MVVM)
```xml
<listbox model="@load(vm.items)"
         selectedItem="@bind(vm.selectedItem)"
         hflex="1" vflex="1">
    <listhead>
        <listheader label="ID" width="80px"/>
        <listheader label="Name" hflex="2"/>
        <listheader label="Status" hflex="1"/>
        <listheader label="Actions" width="120px"/>
    </listhead>
    <template name="model" var="item">
        <listitem>
            <listcell label="@load(item.id)"/>
            <listcell label="@load(item.name)"/>
            <listcell label="@load(item.status)"/>
            <listcell>
                <button label="Edit" onClick="@command('edit', item=item)"/>
                <button label="Delete" onClick="@command('delete', item=item)"/>
            </listcell>
        </listitem>
    </template>
</listbox>
```

#### Master-Detail Pattern (MVVM)
```xml
<hlayout vflex="1" hflex="1">
    <!-- Master list -->
    <listbox model="@load(vm.items)"
             selectedItem="@bind(vm.selectedItem)"
             hflex="1" vflex="1">
        <listhead>
            <listheader label="Name"/>
        </listhead>
        <template name="model" var="item">
            <listitem label="@load(item.name)"/>
        </template>
    </listbox>

    <!-- Detail panel -->
    <vlayout hflex="2" vflex="1"
             visible="@load(not empty vm.selectedItem)">
        <label value="@load(vm.selectedItem.name)"
               style="font-weight: bold; font-size: 16px"/>
        <separator/>
        <label value="@load(vm.selectedItem.description)"/>
    </vlayout>
</hlayout>
```

#### Dialog/Popup (MVVM)
```xml
<window id="editDialog" title="Edit Item" border="normal"
        width="400px" mode="modal" closable="true"
        viewModel="@id('vm') @init('com.example.EditViewModel')">
    <vlayout>
        <grid>
            <columns>
                <column width="100px"/>
                <column/>
            </columns>
            <rows>
                <row>
                    <label value="Name:"/>
                    <textbox value="@bind(vm.item.name)" hflex="1"/>
                </row>
            </rows>
        </grid>
        <hlayout style="margin-top: 10px">
            <button label="OK" onClick="@command('confirm')"/>
            <button label="Cancel" onClick="@command('cancel')"/>
        </hlayout>
    </vlayout>
</window>
```

---

## Step 3: Validate Generated ZUL
validate generated ZUL file with @scripts/validate-zul.py

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
- [ ] IDs are unique within the page
- [ ] Avoid inline styles where possible (use sclass)
- [ ] Use `hflex`/`vflex` instead of fixed dimensions
- [ ] Include meaningful labels and tooltips for accessibility

### Companion Java Class Suggestions

#### For MVC Pattern - Composer Class
```java
package com.example.controller;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zul.*;

public class MyComposer extends SelectorComposer<Component> {

    @Wire
    private Textbox nameInput;

    @Wire
    private Button submitBtn;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        // Initialization logic
    }

    @Listen("onClick = #submitBtn")
    public void onSubmit() {
        String name = nameInput.getValue();
        // Handle submit
    }
}
```

#### For MVVM Pattern - ViewModel Class
```java
package com.example.viewmodel;

import org.zkoss.bind.annotation.*;
import org.zkoss.zk.ui.select.annotation.Wire;

public class MyViewModel {

    private String name;
    private List<Item> items;
    private Item selectedItem;

    @Init
    public void init() {
        // Initialization logic
        items = loadItems();
    }

    // Getters and setters for binding
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public List<Item> getItems() { return items; }
    public Item getSelectedItem() { return selectedItem; }
    public void setSelectedItem(Item item) { this.selectedItem = item; }

    @Command
    @NotifyChange({"items", "selectedItem"})
    public void save() {
        // Save logic
    }

    @Command
    public void cancel() {
        // Cancel logic
    }
}
```

---

## Complete Examples

### Example 1: Simple Form (MVVM)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?page title="User Registration"?>
<zk xmlns="http://www.zkoss.org/2005/zul">
    <window id="registrationWin" title="User Registration" border="normal"
            width="500px"
            viewModel="@id('vm') @init('com.example.vm.RegistrationViewModel')">
        <vlayout>
            <grid>
                <columns>
                    <column width="120px" align="right"/>
                    <column/>
                </columns>
                <rows>
                    <row>
                        <label value="Username:"/>
                        <textbox value="@bind(vm.user.username)"
                                 constraint="no empty" hflex="1"/>
                    </row>
                    <row>
                        <label value="Email:"/>
                        <textbox value="@bind(vm.user.email)"
                                 constraint="/.+@.+\..+/: Invalid email"
                                 hflex="1"/>
                    </row>
                    <row>
                        <label value="Password:"/>
                        <textbox type="password"
                                 value="@bind(vm.user.password)"
                                 constraint="no empty" hflex="1"/>
                    </row>
                    <row>
                        <label value="Country:"/>
                        <combobox model="@load(vm.countries)"
                                  selectedItem="@bind(vm.user.country)"
                                  hflex="1" readonly="true">
                            <template name="model" var="country">
                                <comboitem label="@load(country.name)"/>
                            </template>
                        </combobox>
                    </row>
                </rows>
            </grid>
            <separator/>
            <hlayout>
                <button label="Register" onClick="@command('register')"
                        mold="trendy"/>
                <button label="Clear" onClick="@command('clear')"/>
            </hlayout>
        </vlayout>
    </window>
</zk>
```

### Example 2: Data Management Page (MVVM)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?page title="Product Management"?>
<zk xmlns="http://www.zkoss.org/2005/zul">
    <borderlayout hflex="1" vflex="1"
                  viewModel="@id('vm') @init('com.example.vm.ProductViewModel')">
        <north height="50px" border="none">
            <hlayout valign="middle" hflex="1" style="padding: 10px">
                <label value="Product Management"
                       style="font-size: 18px; font-weight: bold"/>
                <space hflex="1"/>
                <button label="Add Product"
                        onClick="@command('showAddDialog')"
                        iconSclass="z-icon-plus"/>
            </hlayout>
        </north>
        <west width="250px" title="Categories" splittable="true"
              collapsible="true">
            <listbox model="@load(vm.categories)"
                     selectedItem="@bind(vm.selectedCategory)"
                     vflex="1">
                <template name="model" var="cat">
                    <listitem label="@load(cat.name)"/>
                </template>
            </listbox>
        </west>
        <center border="none">
            <vlayout vflex="1" hflex="1" style="padding: 10px">
                <!-- Search bar -->
                <hlayout>
                    <textbox value="@bind(vm.searchKeyword)"
                             placeholder="Search products..."
                             hflex="1" instant="true"
                             onChange="@command('search')"/>
                    <button label="Search" onClick="@command('search')"
                            iconSclass="z-icon-search"/>
                </hlayout>
                <separator/>
                <!-- Product grid -->
                <listbox model="@load(vm.products)"
                         selectedItem="@bind(vm.selectedProduct)"
                         hflex="1" vflex="1" emptyMessage="No products found">
                    <listhead>
                        <listheader label="ID" width="60px" sort="auto(id)"/>
                        <listheader label="Name" hflex="2" sort="auto(name)"/>
                        <listheader label="Category" hflex="1"/>
                        <listheader label="Price" width="100px"
                                    sort="auto(price)" align="right"/>
                        <listheader label="Stock" width="80px" align="center"/>
                        <listheader label="Actions" width="150px"
                                    align="center"/>
                    </listhead>
                    <template name="model" var="prod">
                        <listitem>
                            <listcell label="@load(prod.id)"/>
                            <listcell label="@load(prod.name)"/>
                            <listcell label="@load(prod.category.name)"/>
                            <listcell label="@load(prod.price) @converter('formattedNumber', format='$#,##0.00')"/>
                            <listcell label="@load(prod.stock)"/>
                            <listcell>
                                <hlayout>
                                    <button label="Edit"
                                            onClick="@command('edit', product=prod)"
                                            iconSclass="z-icon-edit"/>
                                    <button label="Delete"
                                            onClick="@command('delete', product=prod)"
                                            iconSclass="z-icon-trash"/>
                                </hlayout>
                            </listcell>
                        </listitem>
                    </template>
                </listbox>
                <!-- Paging -->
                <paging totalSize="@load(vm.totalSize)"
                        pageSize="@load(vm.pageSize)"
                        activePage="@bind(vm.activePage)"/>
            </vlayout>
        </center>
    </borderlayout>
</zk>
```

### Example 3: Simple List Page (MVC)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?page title="Task List"?>
<zk xmlns="http://www.zkoss.org/2005/zul">
    <window id="taskWin" title="My Tasks" border="normal"
            width="600px"
            apply="com.example.controller.TaskComposer">
        <vlayout>
            <hlayout>
                <textbox id="taskInput" hflex="1"
                         placeholder="Enter new task..."/>
                <button id="addBtn" label="Add Task"/>
            </hlayout>
            <separator/>
            <listbox id="taskList" hflex="1" height="300px"
                     emptyMessage="No tasks yet">
                <listhead>
                    <listheader label="Done" width="60px"/>
                    <listheader label="Task" hflex="1"/>
                    <listheader label="Actions" width="80px"/>
                </listhead>
            </listbox>
            <hlayout>
                <label id="statusLabel" value="0 tasks"/>
                <space hflex="1"/>
                <button id="clearBtn" label="Clear Completed"/>
            </hlayout>
        </vlayout>
    </window>
</zk>
```

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

---

## Troubleshooting Common Issues

### Issue: Data binding not working
- Verify `viewModel` attribute is on a container component
- Check that getter/setter methods exist in ViewModel
- Ensure `@NotifyChange` is used after data modifications

### Issue: Components not displaying
- Check if parent has defined height (required for `vflex`)
- Verify component is not hidden by CSS
- Check for JavaScript errors in browser console

### Issue: Events not firing
- MVC: Verify `@Listen` annotation matches component ID
- MVVM: Check `@command` method exists and is public
- Ensure event name is correct (e.g., `onClick`, not `onclick`)

### Issue: Constraint validation not showing
- Ensure constraint syntax is correct
- Check that component is not readonly
- Verify form submission triggers validation
