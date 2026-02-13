package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.event.Events;
import org.zkoss.zk.ui.event.SelectEvent;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.*;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;

/**
 * MVC Composer for the Navigation Dashboard page.
 * Provides a collapsible sidebar with tree navigation and a main area
 * displaying recent tasks in a filterable, sortable grid.
 *
 * Replace the sample data methods with real service/repository calls.
 */
public class NavDashboardComposer extends SelectorComposer<Component> {

    // --- Header ---
    @Wire
    private Label currentDateLabel;
    @Wire
    private Label pageTitleLabel;
    @Wire
    private Label breadcrumbLabel;

    // --- Navigation ---
    @Wire
    private Textbox navSearchBox;
    @Wire
    private Tree navTree;

    // --- Filters ---
    @Wire
    private Textbox taskSearchBox;
    @Wire
    private Combobox statusFilter;
    @Wire
    private Combobox priorityFilter;

    // --- Summary Cards ---
    @Wire
    private Label totalCountLabel;
    @Wire
    private Label todoCountLabel;
    @Wire
    private Label inProgressCountLabel;
    @Wire
    private Label doneCountLabel;

    // --- Task Grid ---
    @Wire
    private Listbox taskListbox;
    @Wire
    private Label taskCountLabel;

    // --- Data ---
    private List<Task> allTasks;
    private List<Task> filteredTasks;

    private static final SimpleDateFormat DATE_FMT = new SimpleDateFormat("MMMM d, yyyy");
    private static final SimpleDateFormat SHORT_DATE_FMT = new SimpleDateFormat("MMM d, yyyy");

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        allTasks = getSampleTasks();
        filteredTasks = new ArrayList<>(allTasks);
        loadHeader();
        updateSummaryCards();
        renderTaskGrid();
    }

    // ===== Header =====

    private void loadHeader() {
        currentDateLabel.setValue(DATE_FMT.format(new Date()));
    }

    // ===== Tree Navigation =====

    @Listen("onSelect = #navTree")
    public void onNavSelect(SelectEvent<Treeitem, ?> event) {
        Treeitem selected = event.getSelectedItems().iterator().next();
        Treecell cell = (Treecell) selected.getTreerow().getFirstChild();
        String label = cell.getLabel();
        pageTitleLabel.setValue(label);

        // Build breadcrumb from the tree hierarchy
        StringBuilder breadcrumb = new StringBuilder();
        Treeitem current = selected;
        List<String> path = new ArrayList<>();
        while (current != null) {
            Treecell currentCell = (Treecell) current.getTreerow().getFirstChild();
            path.add(0, currentCell.getLabel());
            Component parent = current.getParent(); // treechildren
            if (parent != null && parent.getParent() instanceof Treeitem) {
                current = (Treeitem) parent.getParent();
            } else {
                current = null;
            }
        }
        breadcrumb.append(String.join(" > ", path));
        breadcrumbLabel.setValue(breadcrumb.toString());
    }

    @Listen("onChanging = #navSearchBox")
    public void onNavSearch() {
        // Placeholder for filtering tree items based on search text.
        // A full implementation would show/hide tree nodes matching the query.
    }

    // ===== Filters =====

    @Listen("onClick = #applyFilterBtn")
    public void onApplyFilter() {
        applyFilters();
    }

    @Listen("onClick = #clearFilterBtn")
    public void onClearFilter() {
        taskSearchBox.setValue("");
        statusFilter.setValue("");
        statusFilter.setSelectedIndex(-1);
        priorityFilter.setValue("");
        priorityFilter.setSelectedIndex(-1);
        filteredTasks = new ArrayList<>(allTasks);
        updateSummaryCards();
        renderTaskGrid();
    }

    private void applyFilters() {
        String searchText = taskSearchBox.getValue().trim().toLowerCase();
        String statusValue = statusFilter.getSelectedItem() != null
                ? statusFilter.getSelectedItem().getValue().toString() : "ALL";
        String priorityValue = priorityFilter.getSelectedItem() != null
                ? priorityFilter.getSelectedItem().getValue().toString() : "ALL";

        filteredTasks = allTasks.stream()
                .filter(t -> {
                    if (!searchText.isEmpty()) {
                        return t.getName().toLowerCase().contains(searchText)
                                || t.getDescription().toLowerCase().contains(searchText);
                    }
                    return true;
                })
                .filter(t -> "ALL".equals(statusValue) || t.getStatus().equals(statusValue))
                .filter(t -> "ALL".equals(priorityValue) || t.getPriority().equals(priorityValue))
                .collect(Collectors.toList());

        updateSummaryCards();
        renderTaskGrid();
    }

    // ===== Summary Cards =====

    private void updateSummaryCards() {
        long total = filteredTasks.size();
        long todo = filteredTasks.stream().filter(t -> "TODO".equals(t.getStatus())).count();
        long inProgress = filteredTasks.stream().filter(t -> "IN_PROGRESS".equals(t.getStatus())).count();
        long done = filteredTasks.stream().filter(t -> "DONE".equals(t.getStatus())).count();

        totalCountLabel.setValue(String.valueOf(total));
        todoCountLabel.setValue(String.valueOf(todo));
        inProgressCountLabel.setValue(String.valueOf(inProgress));
        doneCountLabel.setValue(String.valueOf(done));
    }

    // ===== Task Grid =====

    private void renderTaskGrid() {
        taskListbox.getItems().clear();

        for (Task task : filteredTasks) {
            Listitem li = new Listitem();

            // ID
            li.appendChild(new Listcell(task.getId()));

            // Task Name and description
            Listcell nameCell = new Listcell();
            Vlayout nameLayout = new Vlayout();
            nameLayout.setSpacing("2px");
            Label nameLabel = new Label(task.getName());
            nameLabel.setStyle("font-weight: bold; color: #333");
            nameLayout.appendChild(nameLabel);
            Label descLabel = new Label(task.getDescription());
            descLabel.setStyle("font-size: 12px; color: #999");
            descLabel.setMaxlength(60);
            nameLayout.appendChild(descLabel);
            nameCell.appendChild(nameLayout);
            li.appendChild(nameCell);

            // Assignee
            li.appendChild(new Listcell(task.getAssignee()));

            // Status badge
            Listcell statusCell = new Listcell();
            Label statusLabel = new Label(getStatusDisplay(task.getStatus()));
            statusLabel.setStyle(getStatusStyle(task.getStatus()));
            statusCell.appendChild(statusLabel);
            li.appendChild(statusCell);

            // Priority badge
            Listcell priorityCell = new Listcell();
            Label priorityLabel = new Label(task.getPriority());
            priorityLabel.setStyle(getPriorityStyle(task.getPriority()));
            priorityCell.appendChild(priorityLabel);
            li.appendChild(priorityCell);

            // Due Date
            li.appendChild(new Listcell(SHORT_DATE_FMT.format(task.getDueDate())));

            // Actions
            Listcell actionCell = new Listcell();
            Hlayout actionLayout = new Hlayout();
            actionLayout.setSpacing("4px");

            Button editBtn = new Button();
            editBtn.setIconSclass("z-icon-pencil");
            editBtn.setTooltiptext("Edit Task");
            editBtn.addEventListener(Events.ON_CLICK, e -> onEditTask(task));
            actionLayout.appendChild(editBtn);

            Button deleteBtn = new Button();
            deleteBtn.setIconSclass("z-icon-trash");
            deleteBtn.setTooltiptext("Delete Task");
            deleteBtn.addEventListener(Events.ON_CLICK, e -> onDeleteTask(task));
            actionLayout.appendChild(deleteBtn);

            actionCell.appendChild(actionLayout);
            li.appendChild(actionCell);

            taskListbox.appendChild(li);
        }

        taskCountLabel.setValue("Showing " + filteredTasks.size() + " of " + allTasks.size() + " tasks");
    }

    // ===== Actions =====

    @Listen("onClick = #addTaskBtn")
    public void onAddTask() {
        // TODO: Open a dialog or navigate to task creation page
    }

    private void onEditTask(Task task) {
        // TODO: Open edit dialog for the given task
    }

    private void onDeleteTask(Task task) {
        Messagebox.show("Delete task \"" + task.getName() + "\"?",
                "Confirm Delete", Messagebox.YES | Messagebox.NO,
                Messagebox.QUESTION, event -> {
                    if (Messagebox.ON_YES.equals(event.getName())) {
                        allTasks.remove(task);
                        filteredTasks.remove(task);
                        updateSummaryCards();
                        renderTaskGrid();
                    }
                });
    }

    @Listen("onClick = #refreshBtn")
    public void onRefresh() {
        allTasks = getSampleTasks();
        applyFilters();
    }

    @Listen("onClick = #exportBtn")
    public void onExport() {
        // TODO: Implement CSV or Excel export of filteredTasks
    }

    // ===== Styling Helpers =====

    private String getStatusDisplay(String status) {
        switch (status) {
            case "TODO": return "To Do";
            case "IN_PROGRESS": return "In Progress";
            case "IN_REVIEW": return "In Review";
            case "DONE": return "Done";
            default: return status;
        }
    }

    private String getStatusStyle(String status) {
        String base = "font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: bold; ";
        switch (status) {
            case "TODO":
                return base + "color: #1565c0; background: #e3f2fd";
            case "IN_PROGRESS":
                return base + "color: #e65100; background: #fff3e0";
            case "IN_REVIEW":
                return base + "color: #6a1b9a; background: #f3e5f5";
            case "DONE":
                return base + "color: #2e7d32; background: #e8f5e9";
            default:
                return base + "color: #666; background: #f5f5f5";
        }
    }

    private String getPriorityStyle(String priority) {
        String base = "font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: bold; ";
        switch (priority) {
            case "HIGH":
                return base + "color: #c62828; background: #ffebee";
            case "MEDIUM":
                return base + "color: #e65100; background: #fff3e0";
            case "LOW":
                return base + "color: #2e7d32; background: #e8f5e9";
            default:
                return base + "color: #666; background: #f5f5f5";
        }
    }

    // ===== Sample Data (replace with real service calls) =====

    private List<Task> getSampleTasks() {
        List<Task> tasks = new ArrayList<>();
        tasks.add(new Task("TSK-001", "Design system architecture",
                "Create high-level architecture diagrams and component design",
                "Alice Chen", "DONE", "HIGH", new Date(126, 1, 5)));
        tasks.add(new Task("TSK-002", "Implement user authentication",
                "Set up OAuth2 login flow with JWT token management",
                "Bob Miller", "IN_PROGRESS", "HIGH", new Date(126, 1, 14)));
        tasks.add(new Task("TSK-003", "Build navigation dashboard",
                "Create the main navigation page with sidebar and task grid",
                "Carol Davis", "IN_PROGRESS", "MEDIUM", new Date(126, 1, 18)));
        tasks.add(new Task("TSK-004", "Write unit tests for API",
                "Cover all REST endpoints with JUnit tests",
                "David Kim", "TODO", "MEDIUM", new Date(126, 1, 20)));
        tasks.add(new Task("TSK-005", "Configure CI/CD pipeline",
                "Set up Jenkins pipeline with build, test, and deploy stages",
                "Eve Johnson", "TODO", "LOW", new Date(126, 1, 25)));
        tasks.add(new Task("TSK-006", "Database migration script",
                "Create Flyway migration for new user_preferences table",
                "Alice Chen", "IN_REVIEW", "HIGH", new Date(126, 1, 12)));
        tasks.add(new Task("TSK-007", "Performance optimization",
                "Analyze and improve page load time for the dashboard",
                "Bob Miller", "TODO", "MEDIUM", new Date(126, 2, 1)));
        tasks.add(new Task("TSK-008", "API documentation",
                "Generate Swagger/OpenAPI docs for all endpoints",
                "Carol Davis", "DONE", "LOW", new Date(126, 1, 8)));
        tasks.add(new Task("TSK-009", "Security audit review",
                "Review OWASP Top 10 compliance across all modules",
                "David Kim", "IN_PROGRESS", "HIGH", new Date(126, 1, 16)));
        tasks.add(new Task("TSK-010", "User feedback integration",
                "Add feedback form and rating widget to the main dashboard",
                "Eve Johnson", "TODO", "LOW", new Date(126, 2, 5)));
        return tasks;
    }

    // ===== Inner Data Class =====

    /**
     * Represents a task entry. Consider moving to a separate model file
     * for production use.
     */
    public static class Task {
        private final String id;
        private final String name;
        private final String description;
        private final String assignee;
        private String status;
        private final String priority;
        private final Date dueDate;

        public Task(String id, String name, String description, String assignee,
                    String status, String priority, Date dueDate) {
            this.id = id;
            this.name = name;
            this.description = description;
            this.assignee = assignee;
            this.status = status;
            this.priority = priority;
            this.dueDate = dueDate;
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getDescription() { return description; }
        public String getAssignee() { return assignee; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public String getPriority() { return priority; }
        public Date getDueDate() { return dueDate; }
    }
}
