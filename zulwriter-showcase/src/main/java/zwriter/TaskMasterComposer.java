package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Button;
import org.zkoss.zul.Combobox;
import org.zkoss.zul.Textbox;
import org.zkoss.zul.Tree;
import org.zkoss.zul.Treeitem;

public class TaskMasterComposer extends SelectorComposer<Component> {

    @Wire
    private Tree navTree;

    @Wire
    private Textbox searchBox;

    @Wire
    private Button newProjectBtn;

    @Wire
    private Button filterAllBtn;

    @Wire
    private Button filterPriorityBtn;

    @Wire
    private Button filterDueDateBtn;

    @Wire
    private Combobox sortCombo;

    @Wire
    private Button advFilterBtn;

    @Wire
    private Button notifBtn;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        // Initial state: "Status: All" filter is active
        updateFilterState("all");
    }

    @Listen("onClick = #newProjectBtn")
    public void onNewProject() {
        // TODO: open new project dialog
    }

    @Listen("onClick = #filterAllBtn")
    public void onFilterAll() {
        updateFilterState("all");
    }

    @Listen("onClick = #filterPriorityBtn")
    public void onFilterPriority() {
        updateFilterState("priority");
    }

    @Listen("onClick = #filterDueDateBtn")
    public void onFilterDueDate() {
        updateFilterState("dueDate");
    }

    @Listen("onSelect = #navTree")
    public void onNavSelect() {
        Treeitem selected = navTree.getSelectedItem();
        if (selected != null) {
            // TODO: load tasks for the selected sprint/team
        }
    }

    @Listen("onChange = #searchBox")
    public void onSearch() {
        String keyword = searchBox.getValue();
        // TODO: filter task cards by keyword
    }

    @Listen("onSelect = #sortCombo")
    public void onSortChange() {
        String sort = sortCombo.getValue();
        // TODO: re-sort task cards by selected criteria
    }

    @Listen("onClick = #notifBtn")
    public void onNotifications() {
        // TODO: show notifications popup
    }

    // -- helpers --

    private void updateFilterState(String active) {
        filterAllBtn.setSclass(      "filter-btn" + ("all".equals(active)      ? " filter-btn-active" : ""));
        filterPriorityBtn.setSclass( "filter-btn" + ("priority".equals(active) ? " filter-btn-active" : ""));
        filterDueDateBtn.setSclass(  "filter-btn" + ("dueDate".equals(active)  ? " filter-btn-active" : ""));
    }
}
