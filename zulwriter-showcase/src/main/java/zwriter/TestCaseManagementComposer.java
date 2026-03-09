package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.util.Clients;
import org.zkoss.zul.*;

public class TestCaseManagementComposer extends SelectorComposer<Component> {

    @Wire
    private Tree projectTree;

    @Wire
    private Listbox stepsListbox;

    @Wire
    private Button newTestCaseBtn;

    @Wire
    private Button addStepBtn;

    @Wire
    private Button exportBtn;

    @Wire
    private Button runTestBtn;

    @Wire
    private Button refreshBtn;

    @Wire
    private Button collapseAllBtn;

    // Step configuration fields
    @Wire
    private Combobox actionTypeCombo;

    @Wire
    private Textbox inputDataBox;

    @Wire
    private Textbox locatorValueBox;

    @Wire
    private Checkbox screenshotToggle;

    // Metadata labels
    @Wire
    private Label testCaseId;

    @Wire
    private Label lastEditedBy;

    @Wire
    private Label lastEditedTime;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        // Initial state: step 2 is selected in the listbox
        if (stepsListbox.getItemCount() > 1) {
            stepsListbox.setSelectedIndex(1);
        }
    }

    @Listen("onSelect = #projectTree")
    public void onProjectTreeSelect() {
        Treeitem selected = projectTree.getSelectedItem();
        if (selected == null) return;
        // TODO: load the selected test case into the center panel
    }

    @Listen("onClick = #newTestCaseBtn")
    public void onNewTestCase() {
        // TODO: open a dialog to create a new test case
        Messagebox.show("Create new test case", "New Test Case",
                Messagebox.OK | Messagebox.CANCEL, Messagebox.QUESTION);
    }

    @Listen("onClick = #addStepBtn")
    public void onAddStep() {
        // TODO: append a new blank step row and open step configuration
        int nextNum = stepsListbox.getItemCount() + 1;
        Listitem item = new Listitem();
        item.appendChild(new Listcell(String.valueOf(nextNum)));
        item.appendChild(new Listcell(""));
        item.appendChild(new Listcell(""));
        item.appendChild(new Listcell(""));
        stepsListbox.appendChild(item);
        stepsListbox.setSelectedItem(item);
    }

    @Listen("onClick = #exportBtn")
    public void onExport() {
        // TODO: export test case to CSV / PDF
        Clients.showNotification("Export started", "info", null, "top_center", 2000);
    }

    @Listen("onClick = #runTestBtn")
    public void onRunTest() {
        // TODO: trigger test execution
        Clients.showNotification("Running test: " + testCaseId.getValue(),
                "info", null, "top_center", 3000);
    }

    @Listen("onClick = #refreshBtn")
    public void onRefresh() {
        // TODO: reload test case data from backend
        lastEditedTime.setValue("just now");
    }

    @Listen("onClick = #collapseAllBtn")
    public void onCollapseAll() {
        collapseTreeChildren(projectTree.getTreechildren());
    }

    @Listen("onSelect = #stepsListbox")
    public void onStepSelect() {
        Listitem selected = stepsListbox.getSelectedItem();
        if (selected == null) return;
        // TODO: populate step configuration panel from selected step's data
        int idx = stepsListbox.getIndexOfItem(selected) + 1;
        // Update config panel header (done via client-side or update label via component id)
    }

    /**
     * Save configuration for the currently selected step.
     * Called from the native Save Configuration button via ZK event forwarding,
     * or wire via an onClick listener on a ZK button added behind the native button.
     */
    public void saveConfiguration() {
        String actionType = actionTypeCombo.getValue();
        String inputData = inputDataBox.getValue();
        String locatorValue = locatorValueBox.getValue();
        boolean screenshot = screenshotToggle.isChecked();

        // TODO: persist configuration to selected step's model
        Clients.showNotification("Configuration saved", "info", null, "top_center", 2000);
    }

    /**
     * Reset configuration fields to the last saved state.
     */
    public void resetChanges() {
        // TODO: reload fields from saved state
        inputDataBox.setValue("");
        locatorValueBox.setValue("");
        screenshotToggle.setChecked(false);
        actionTypeCombo.setValue("Type Text");
    }

    // ---- helpers ----

    private void collapseTreeChildren(Treechildren children) {
        if (children == null) return;
        for (Component c : children.getChildren()) {
            if (c instanceof Treeitem) {
                Treeitem ti = (Treeitem) c;
                ti.setOpen(false);
                collapseTreeChildren(ti.getTreechildren());
            }
        }
    }
}
