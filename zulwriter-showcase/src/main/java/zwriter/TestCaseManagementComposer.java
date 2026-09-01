package zwriter;

import java.util.Arrays;
import java.util.List;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.event.Event;
import org.zkoss.zul.Button;
import org.zkoss.zul.Checkbox;
import org.zkoss.zul.Combobox;
import org.zkoss.zul.DefaultTreeModel;
import org.zkoss.zul.DefaultTreeNode;
import org.zkoss.zul.Grid;
import org.zkoss.zul.Label;
import org.zkoss.zul.ListModelList;
import org.zkoss.zul.Messagebox;
import org.zkoss.zul.Textbox;
import org.zkoss.zul.Tree;
import org.zkoss.zul.TreeNode;

/**
 * Composer for {@code test-case-management.zul} — the TestFlow Pro test-suite editor.
 *
 * <p>Extraction pass: the suite tree and the test steps now live here and reach the page through
 * {@code setModel()} on the wired tree and grid, rendered by the {@code <template name="model">}
 * elements left in the ZUL. The literal {@code <treeitem>} and {@code <row>} elements the layout was
 * judged against have been deleted — a model discards markup rows silently, so leaving them would
 * have kept markup on the page that displays nothing.
 *
 * <p>Which branches ship open, and which case is selected, come from the model too
 * ({@code addOpenObject} / {@code addToSelection}): the design shows Auth Module expanded and its
 * three siblings collapsed, and that is a property of the data, not of the markup.
 *
 * <p>Field captions, the LOW/HIGH labels and the connection indicator stayed in the ZUL. They are
 * chrome, still correct tomorrow against tomorrow's suite.
 */
public class TestCaseManagementComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    /** One node of the project explorer: a project, a module, or a test case. */
    public static class SuiteNode {
        private final String name;
        private final String icon;
        private final boolean selected;

        SuiteNode(String name, String icon, boolean selected) {
            this.name = name;
            this.icon = icon;
            this.selected = selected;
        }

        public String getName() {
            return name;
        }

        public String getNodeSclass() {
            return selected ? "tc-node tc-node-on" : "tc-node";
        }

        public String getIconSclass() {
            if (selected) {
                return icon + " tc-node-icon tc-node-icon-on";
            }
            return "z-icon-folder-open".equals(icon)
                    ? icon + " tc-node-icon tc-node-icon-folder"
                    : icon + " tc-node-icon";
        }

        public String getLabelSclass() {
            return selected ? "tc-node-label tc-node-label-on" : "tc-node-label";
        }
    }

    /** One step of the selected test case. */
    public static class Step {
        private final int number;
        private final String action;
        private final String expected;
        private final boolean editing;

        Step(int number, String action, String expected, boolean editing) {
            this.number = number;
            this.action = action;
            this.expected = expected;
            this.editing = editing;
        }

        public int getNumber() {
            return number;
        }

        public String getAction() {
            return action;
        }

        public String getExpected() {
            return expected;
        }

        /** The step being configured in the right-hand panel is the one that shows its controls. */
        public boolean isEditing() {
            return editing;
        }

        public String getRowSclass() {
            return editing ? "tc-row-on" : "";
        }

        public String getNumberSclass() {
            return editing ? "tc-stepno-on" : "tc-stepno";
        }
    }

    private static final List<Step> STEPS = Arrays.asList(
            new Step(1, "Navigate to /login",
                    "Login page is displayed with username/password fields", false),
            new Step(2, "Enter valid credentials",
                    "Credentials are accepted, login button becomes active", true),
            new Step(3, "Click 'Submit' button",
                    "User is redirected to user dashboard with welcome message", false));

    @Wire
    private Tree suiteTree;
    @Wire
    private Grid stepGrid;
    @Wire
    private Textbox searchBox;
    @Wire
    private Combobox actionType;
    @Wire
    private Textbox inputData;
    @Wire
    private Textbox locatorValue;
    @Wire
    private Checkbox screenshotToggle;
    @Wire
    private Button cssBtn;
    @Wire
    private Button xpathBtn;
    @Wire
    private Button idBtn;
    @Wire
    private Label breadcrumb;
    @Wire
    private Label caseState;
    @Wire
    private Label caseTitle;
    @Wire
    private Label caseMeta;
    @Wire
    private Label configSub;
    @Wire
    private Label agentStatus;
    @Wire
    private Label projectName;
    @Wire
    private Label totalSteps;
    @Wire
    private Label estimatedTime;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);

        suiteTree.setModel(buildSuiteModel());
        stepGrid.setModel(new ListModelList<>(STEPS));

        breadcrumb.setValue("E-commerce App / Auth Module / Login Test");
        caseState.setValue("DRAFT");
        caseTitle.setValue("Login Test Case");
        caseMeta.setValue("TC-102 \u2022 Last edited by John Doe 2h ago");

        Step editing = STEPS.stream().filter(Step::isEditing).findFirst().orElse(STEPS.get(0));
        configSub.setValue("Configuring Step #" + editing.getNumber());
        actionType.setValue("Type Text");
        inputData.setValue("admin_user@test.com");
        locatorValue.setValue("#username-input");
        screenshotToggle.setChecked(true);

        agentStatus.setValue("Connected to Cloud Agent");
        projectName.setValue("Project: E-commerce_Prod_v2");
        totalSteps.setValue("Total Steps: " + STEPS.size());
        estimatedTime.setValue("Estimated Time: 1m 45s");
    }

    /**
     * Builds the explorer tree, then opens the project and the Auth Module and selects the Login
     * Test — the state the design shows. The three sibling modules are left closed.
     */
    private static DefaultTreeModel<SuiteNode> buildSuiteModel() {
        DefaultTreeNode<SuiteNode> loginTest =
                new DefaultTreeNode<>(new SuiteNode("Login Test", "z-icon-file-text-o", true));
        DefaultTreeNode<SuiteNode> authModule = new DefaultTreeNode<>(
                new SuiteNode("Auth Module", "z-icon-folder", false),
                Arrays.<TreeNode<SuiteNode>>asList(
                        loginTest,
                        new DefaultTreeNode<>(
                                new SuiteNode("Signup Flow", "z-icon-file-text-o", false)),
                        new DefaultTreeNode<>(
                                new SuiteNode("Password Recovery", "z-icon-file-text-o", false))));

        DefaultTreeNode<SuiteNode> project = new DefaultTreeNode<>(
                new SuiteNode("E-commerce App", "z-icon-folder-open", false),
                Arrays.<TreeNode<SuiteNode>>asList(
                        authModule,
                        module("Payment Flow", "Checkout Test"),
                        module("Shopping Cart", "Add To Cart Test"),
                        module("Inventory Management", "Stock Sync Test")));

        DefaultTreeNode<SuiteNode> root = new DefaultTreeNode<>(null,
                Arrays.<TreeNode<SuiteNode>>asList(project));

        DefaultTreeModel<SuiteNode> model = new DefaultTreeModel<>(root);
        model.addOpenObject(project);
        model.addOpenObject(authModule);
        model.addToSelection(loginTest);
        return model;
    }

    /** A collapsed module with a single case inside it, so the branch is genuinely collapsible. */
    private static DefaultTreeNode<SuiteNode> module(String name, String caseName) {
        return new DefaultTreeNode<>(new SuiteNode(name, "z-icon-folder", false),
                Arrays.<TreeNode<SuiteNode>>asList(
                        new DefaultTreeNode<>(
                                new SuiteNode(caseName, "z-icon-file-text-o", false))));
    }

    @Listen("onClick = #newCaseBtn")
    public void onNewCase() {
        Messagebox.show("Create a test case under the selected module here.", "New Test Case",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #addSuiteBtn")
    public void onAddSuite() {
        Messagebox.show("Add a suite or module to the project here.", "Project Explorer",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #runBtn")
    public void onRun() {
        Messagebox.show("Queue this test case on the cloud agent here.", "Run Test",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #exportBtn")
    public void onExport() {
        Messagebox.show("Export the case as JSON or Gherkin here.", "Export",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #addStepLink")
    public void onAddStep() {
        Messagebox.show("Append a step to this test case here.", "Add New Step",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Selecting a case in the explorer is what loads the centre and right panels. */
    @Listen("onSelect = #suiteTree")
    public void onSelectCase() {
        if (suiteTree.getSelectedItem() == null) {
            return;
        }
        Messagebox.show("Load the selected test case here.", "Project Explorer",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /**
     * The three locator-type buttons behave as one segmented control, so the handler moves the
     * "on" class rather than toggling each button independently.
     */
    @Listen("onClick = #cssBtn, #xpathBtn, #idBtn")
    public void onLocatorType(Event event) {
        Component picked = event.getTarget();
        for (Button button : new Button[] {cssBtn, xpathBtn, idBtn}) {
            button.setSclass(button == picked ? "tc-seg-btn tc-seg-on" : "tc-seg-btn");
        }
    }

    @Listen("onClick = #saveConfigBtn")
    public void onSaveConfig() {
        Messagebox.show("Save step: " + actionType.getValue()
                + " \"" + inputData.getValue() + "\""
                + " at " + locatorValue.getValue()
                + (screenshotToggle.isChecked() ? ", screenshot on failure" : ""),
                "Save Configuration", Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #resetConfigBtn")
    public void onResetConfig() {
        Messagebox.show("Discard the unsaved step changes here.", "Reset Changes",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Enter in the search box narrows the project explorer. */
    @Listen("onOK = #searchBox")
    public void onSearch() {
        Messagebox.show("Filter the explorer by \"" + searchBox.getValue() + "\" here.", "Search",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
