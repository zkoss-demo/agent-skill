package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.*;

import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * MVC Composer for the Application Dashboard page.
 * Displays an overview with status summary cards and a recent messages list.
 * Replace the sample data methods with real service/repository calls.
 */
public class AppDashboardComposer extends SelectorComposer<Component> {

    // --- Wired components: Header ---
    @Wire
    private Label currentDateLabel;

    // --- Wired components: Status Cards ---
    @Wire
    private Label appStatusLabel;
    @Wire
    private Label appStatusDetailLabel;
    @Wire
    private Label appIdLabel;
    @Wire
    private Label appIdDetailLabel;
    @Wire
    private Label submissionDateLabel;
    @Wire
    private Label submissionDateDetailLabel;
    @Wire
    private Label amountLabel;
    @Wire
    private Label amountDetailLabel;

    // --- Wired components: Messages ---
    @Wire
    private Label messageCountLabel;
    @Wire
    private Listbox messageListbox;

    // --- Formatters ---
    private static final NumberFormat CURRENCY_FMT = NumberFormat.getCurrencyInstance(Locale.US);
    private static final SimpleDateFormat DATE_FMT = new SimpleDateFormat("MMMM d, yyyy");
    private static final SimpleDateFormat SHORT_DATE_FMT = new SimpleDateFormat("MMM d, yyyy");

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        loadDashboard();
    }

    /**
     * Loads all dashboard data and populates the UI.
     */
    private void loadDashboard() {
        loadHeader();
        loadStatusCards();
        loadMessages();
    }

    /**
     * Populates the header area with the current date.
     */
    private void loadHeader() {
        currentDateLabel.setValue(DATE_FMT.format(new Date()));
    }

    /**
     * Populates the four status summary cards.
     * Replace the sample values with real data from your service layer.
     */
    private void loadStatusCards() {
        // Application Status
        appStatusLabel.setValue("Approved");
        appStatusDetailLabel.setValue("Final review completed");

        // Application ID
        appIdLabel.setValue("APP-2026-0042");
        appIdDetailLabel.setValue("Submitted by John Doe");

        // Submission Date
        submissionDateLabel.setValue("Feb 3, 2026");
        submissionDateDetailLabel.setValue("15 days ago");

        // Amount
        amountLabel.setValue(CURRENCY_FMT.format(12500.00));
        amountDetailLabel.setValue("Approved budget allocation");
    }

    /**
     * Populates the recent messages / notifications list.
     * Replace the sample data with real notification data from your service layer.
     */
    private void loadMessages() {
        List<Message> messages = getSampleMessages();
        messageCountLabel.setValue(messages.size() + " messages");

        for (Message msg : messages) {
            Listitem li = new Listitem();

            // Icon cell
            Listcell iconCell = new Listcell();
            Label iconLabel = new Label();
            iconLabel.setSclass(msg.isRead() ? "z-icon-envelope-o" : "z-icon-envelope");
            iconLabel.setStyle(msg.isRead() ? "color: #bbb" : "color: #1565c0");
            iconCell.appendChild(iconLabel);
            li.appendChild(iconCell);

            // Subject cell
            Listcell subjectCell = new Listcell();
            Vlayout subjectLayout = new Vlayout();
            subjectLayout.setSpacing("2px");
            Label subjectLabel = new Label(msg.getSubject());
            subjectLabel.setStyle(msg.isRead()
                    ? "color: #666"
                    : "font-weight: bold; color: #333");
            subjectLayout.appendChild(subjectLabel);
            Label previewLabel = new Label(msg.getPreview());
            previewLabel.setStyle("color: #999; font-size: 12px");
            previewLabel.setMaxlength(80);
            subjectLayout.appendChild(previewLabel);
            subjectCell.appendChild(subjectLayout);
            li.appendChild(subjectCell);

            // From cell
            li.appendChild(new Listcell(msg.getFrom()));

            // Date cell
            li.appendChild(new Listcell(SHORT_DATE_FMT.format(msg.getDate())));

            // Priority cell
            Listcell priorityCell = new Listcell();
            Label priorityLabel = new Label(msg.getPriority());
            String priorityStyle = getPriorityStyle(msg.getPriority());
            priorityLabel.setStyle(priorityStyle);
            priorityCell.appendChild(priorityLabel);
            li.appendChild(priorityCell);

            messageListbox.appendChild(li);
        }
    }

    /**
     * Returns inline style for the priority badge based on the priority level.
     */
    private String getPriorityStyle(String priority) {
        String base = "font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: bold; ";
        switch (priority.toLowerCase()) {
            case "high":
                return base + "color: #c62828; background: #ffebee";
            case "medium":
                return base + "color: #e65100; background: #fff3e0";
            case "low":
                return base + "color: #2e7d32; background: #e8f5e9";
            default:
                return base + "color: #666; background: #f5f5f5";
        }
    }

    @Listen("onClick = #refreshBtn")
    public void onRefresh() {
        // Clear existing message items
        messageListbox.getItems().clear();
        // Reload all dashboard data
        loadDashboard();
    }

    @Listen("onClick = #viewAllBtn")
    public void onViewAllMessages() {
        // TODO: Navigate to the full messages page
        // e.g., Executions.sendRedirect("/messages.zul");
    }

    // --- Sample data (replace with real data access) ---

    private List<Message> getSampleMessages() {
        List<Message> messages = new ArrayList<>();
        messages.add(new Message(
                "Application Approved",
                "Your application APP-2026-0042 has been approved by the review committee.",
                "Review Board", new Date(126, 1, 11), "High", false));
        messages.add(new Message(
                "Budget Allocation Updated",
                "The budget for Q1 2026 has been finalized. Please review the updated figures.",
                "Finance Dept", new Date(126, 1, 10), "Medium", false));
        messages.add(new Message(
                "Document Submission Reminder",
                "Please submit the remaining supporting documents by February 15, 2026.",
                "Admin Office", new Date(126, 1, 9), "High", false));
        messages.add(new Message(
                "System Maintenance Notice",
                "Scheduled maintenance window on Feb 16, 2026 from 2:00 AM to 5:00 AM EST.",
                "IT Support", new Date(126, 1, 8), "Low", true));
        messages.add(new Message(
                "Weekly Status Report Available",
                "The weekly status report for the period ending Feb 7 is now available.",
                "Project Manager", new Date(126, 1, 7), "Medium", true));
        return messages;
    }

    // --- Inner data class ---

    /**
     * Represents a notification or message entry.
     * Consider moving to a separate model file for production use.
     */
    public static class Message {
        private final String subject;
        private final String preview;
        private final String from;
        private final Date date;
        private final String priority;
        private final boolean read;

        public Message(String subject, String preview, String from,
                       Date date, String priority, boolean read) {
            this.subject = subject;
            this.preview = preview;
            this.from = from;
            this.date = date;
            this.priority = priority;
            this.read = read;
        }

        public String getSubject() { return subject; }
        public String getPreview() { return preview; }
        public String getFrom() { return from; }
        public Date getDate() { return date; }
        public String getPriority() { return priority; }
        public boolean isRead() { return read; }
    }
}
