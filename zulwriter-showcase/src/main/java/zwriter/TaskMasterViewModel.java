package zwriter;

import java.util.Arrays;
import java.util.List;

import org.zkoss.bind.annotation.Command;
import org.zkoss.zul.DefaultTreeModel;
import org.zkoss.zul.DefaultTreeNode;
import org.zkoss.zul.Messagebox;
import org.zkoss.zul.TreeNode;

/**
 * ViewModel for {@code task-master.zul}.
 *
 * <p>Extraction pass: the sprint's tasks and the workspace tree now live here, and the ZUL reads
 * them through {@code @load} — a bound {@code model} for the tree, a {@code <forEach>} for the
 * cards. The literal rows the layout was judged against have been deleted from the markup.
 *
 * <p>Section titles, column captions and the empty-state wording stayed in the ZUL: they are chrome,
 * still correct tomorrow against tomorrow's tasks.
 */
public class TaskMasterViewModel {

    /** One row of the WORKSPACES tree. Carries its own style classes so the ZUL stays declarative. */
    public static class WorkspaceNode {
        private final String name;
        private final String icon;
        private final boolean active;

        WorkspaceNode(String name, String icon, boolean active) {
            this.name = name;
            this.icon = icon;
            this.active = active;
        }

        public String getName() {
            return name;
        }

        public String getNodeSclass() {
            return active ? "tm-node tm-node-on" : "tm-node";
        }

        public String getIconSclass() {
            return active ? icon + " tm-node-icon tm-node-icon-open" : icon + " tm-node-icon";
        }

        public String getLabelSclass() {
            return active ? "tm-node-label tm-node-label-on" : "tm-node-label";
        }
    }

    /** One task card in the "Recent Tasks" grid. */
    public static class Task {
        private final String statusLabel;
        private final String statusKey;
        private final String title;
        private final String description;
        private final String priority;
        private final List<String> assignees;

        Task(String statusLabel, String statusKey, String title, String description,
                String priority, List<String> assignees) {
            this.statusLabel = statusLabel;
            this.statusKey = statusKey;
            this.title = title;
            this.description = description;
            this.priority = priority;
            this.assignees = assignees;
        }

        public String getStatusLabel() {
            return statusLabel;
        }

        public String getStatusSclass() {
            return "tm-chip tm-chip-" + statusKey;
        }

        public String getTitle() {
            return title;
        }

        public String getDescription() {
            return description;
        }

        public String getPriorityLabel() {
            return priority.toUpperCase();
        }

        public String getPriorityIconSclass() {
            String glyph = "high".equals(priority) ? "z-icon-exclamation" : "z-icon-bars";
            return glyph + " tm-prio-icon tm-prio-" + priority;
        }

        public String getPrioritySclass() {
            return "tm-prio tm-prio-label-" + priority;
        }

        public List<String> getAssignees() {
            return assignees;
        }
    }

    private final DefaultTreeModel<WorkspaceNode> workspaceModel = buildWorkspaceModel();

    private final List<Task> tasks = Arrays.asList(
            new Task("IN PROGRESS", "progress", "Design System Audit: Components & Tokens",
                    "Review all core UI components against the new token set.",
                    "high", Arrays.asList("Elena Fischer", "Marcus Bell")),
            new Task("COMPLETED", "done", "API Endpoint Migration",
                    "Migrate existing legacy endpoints to the new Node.js gateway.",
                    "medium", Arrays.asList("David Chen")),
            new Task("TO DO", "todo", "User Interview Synthesis",
                    "Compile findings from the last 10 user interviews into a report.",
                    "high", Arrays.asList("Anna Kowalski")),
            new Task("IN PROGRESS", "progress", "Onboarding Flow Redesign",
                    "Iterate on the user registration flow to reduce drop-off rate.",
                    "low", Arrays.asList("Sarah Nguyen", "Priya Raman")));

    /**
     * Builds the workspace tree and opens the two branches the mockup shows expanded. The model is
     * held in a field rather than rebuilt per {@code @load}, so its open and selected state
     * survives a re-render.
     */
    private static DefaultTreeModel<WorkspaceNode> buildWorkspaceModel() {
        DefaultTreeNode<WorkspaceNode> sprint1 =
                new DefaultTreeNode<>(new WorkspaceNode("Sprint 1", "z-icon-bolt", true));
        DefaultTreeNode<WorkspaceNode> sprint2 =
                new DefaultTreeNode<>(new WorkspaceNode("Sprint 2 (Next)", "z-icon-history", false));
        DefaultTreeNode<WorkspaceNode> teamAlpha = new DefaultTreeNode<>(
                new WorkspaceNode("Team Alpha", "z-icon-users", false),
                Arrays.<TreeNode<WorkspaceNode>>asList(sprint1, sprint2));
        DefaultTreeNode<WorkspaceNode> teamBravo =
                new DefaultTreeNode<>(new WorkspaceNode("Team Bravo", "z-icon-users", false));
        DefaultTreeNode<WorkspaceNode> projects = new DefaultTreeNode<>(
                new WorkspaceNode("Projects", "z-icon-folder", true),
                Arrays.<TreeNode<WorkspaceNode>>asList(teamAlpha, teamBravo));
        DefaultTreeNode<WorkspaceNode> root =
                new DefaultTreeNode<>(null, Arrays.<TreeNode<WorkspaceNode>>asList(projects));

        DefaultTreeModel<WorkspaceNode> model = new DefaultTreeModel<>(root);
        model.addOpenObject(projects);
        model.addOpenObject(teamAlpha);
        model.addToSelection(sprint1);
        return model;
    }

    public DefaultTreeModel<WorkspaceNode> getWorkspaceModel() {
        return workspaceModel;
    }

    public List<Task> getTasks() {
        return tasks;
    }

    public String getCrumbProject() {
        return "Projects";
    }

    public String getCrumbTeam() {
        return "Team Alpha";
    }

    public String getCrumbSprint() {
        return "Sprint 1";
    }

    public String getUserName() {
        return "Alex Rivers";
    }

    public String getUserRole() {
        return "PROJECT LEAD";
    }

    /** Invoked by the "New Project" button pinned to the foot of the sidebar. */
    @Command
    public void newProject() {
        Messagebox.show("Open the new-project form here.", "New Project",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Invoked by the header's add button and by the dashed "Create New Task" card. */
    @Command
    public void newTask() {
        Messagebox.show("Add a task to Sprint 1 here.", "New Task",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
