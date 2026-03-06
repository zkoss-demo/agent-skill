package zwriter;

import org.zkoss.bind.annotation.BindingParam;
import org.zkoss.bind.annotation.Command;
import org.zkoss.bind.annotation.Init;
import org.zkoss.bind.annotation.NotifyChange;

import java.util.ArrayList;
import java.util.List;

public class EnterpriseKanbanViewModel {

    // --- State ---
    private List<KanbanTask> pendingTasks;
    private List<KanbanTask> processingTasks;
    private List<KanbanTask> waitingTasks;

    @Init
    public void init() {
        pendingTasks = new ArrayList<>();
        pendingTasks.add(new KanbanTask(
                "Database Schema Migration",
                "Upgrade legacy PostgreSQL clusters to v15 and optimize indexes for resource reporting.",
                "HIGH PRIORITY", "priority-high",
                "Marcus", "/img/avatar1.png",
                "OCT 24", "task-due"));
        pendingTasks.add(new KanbanTask(
                "API Documentation Audit",
                "Review all public endpoints for compliance with the new enterprise security standards.",
                "MEDIUM", "priority-medium",
                "Sarah", "/img/avatar2.png",
                "OCT 28", "task-due"));

        processingTasks = new ArrayList<>();
        processingTasks.add(new KanbanTask(
                "Frontend Design Implementation",
                "Converting Figma assets to Tailwind components for the resource dashboard UI.",
                "ACTIVE", "priority-active",
                "Elena", "/img/avatar3.png",
                "TODAY", "task-due-today"));
        processingTasks.add(new KanbanTask(
                "Q3 Financial Reporting Export",
                "Validation of CSV data exports for the quarterly board meeting presentation.",
                "IN REVIEW", "priority-review",
                "David", "/img/avatar4.png",
                "TOMORROW", "task-due-tomorrow"));

        waitingTasks = new ArrayList<>();
        waitingTasks.add(new KanbanTask(
                "SSO Authentication Bridge",
                "Integration with Azure AD for client-side authentication. Waiting for API credentials.",
                "BLOCKED", "priority-blocked",
                "Anna", "/img/avatar5.png",
                "PENDING", "task-due"));
    }

    // --- Commands ---

    @Command
    @NotifyChange({"pendingTasks", "processingTasks", "waitingTasks"})
    public void newTask() {
        // TODO: Open a dialog to create a new task
    }

    @Command
    @NotifyChange({"pendingTasks", "processingTasks", "waitingTasks"})
    public void addTask(@BindingParam("col") String col) {
        // TODO: Open a dialog to add a task to the specified column
    }

    // --- Getters ---

    public List<KanbanTask> getPendingTasks()    { return pendingTasks; }
    public List<KanbanTask> getProcessingTasks() { return processingTasks; }
    public List<KanbanTask> getWaitingTasks()    { return waitingTasks; }

    // =========================================================
    // Inner model class — move to a separate file when needed
    // =========================================================
    public static class KanbanTask {
        private final String title;
        private final String description;
        private final String priorityLabel;
        private final String prioritySclass;   // CSS sclass suffix, e.g. "priority-high"
        private final String assigneeName;
        private final String assigneeAvatar;
        private final String dueDateDisplay;
        private final String dueDateSclass;

        public KanbanTask(String title, String description,
                          String priorityLabel, String prioritySclass,
                          String assigneeName, String assigneeAvatar,
                          String dueDateDisplay, String dueDateSclass) {
            this.title          = title;
            this.description    = description;
            this.priorityLabel  = priorityLabel;
            this.prioritySclass = prioritySclass;
            this.assigneeName   = assigneeName;
            this.assigneeAvatar = assigneeAvatar;
            this.dueDateDisplay = dueDateDisplay;
            this.dueDateSclass  = dueDateSclass;
        }

        public String getTitle()          { return title; }
        public String getDescription()    { return description; }
        public String getPriorityLabel()  { return priorityLabel; }
        public String getPrioritySclass() { return prioritySclass; }
        public String getAssigneeName()   { return assigneeName; }
        public String getAssigneeAvatar() { return assigneeAvatar; }
        public String getDueDateDisplay() { return dueDateDisplay; }
        public String getDueDateSclass()  { return dueDateSclass; }
    }
}
