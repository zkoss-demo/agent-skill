package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.util.Clients;
import org.zkoss.zul.*;

import java.util.Arrays;
import java.util.List;

/**
 * Composer for app-tracker.zul — Application Overview page.
 *
 * Scaffold: uses hardcoded sample data.
 * TODO: Replace sample data methods with actual service/repository calls.
 */
public class AppTrackerComposer extends SelectorComposer<Component> {

    // --- Wired components ---
    @Wire private Label appStatusLabel;
    @Wire private Label appIdLabel;
    @Wire private Label submissionDateLabel;
    @Wire private Label processingFeeLabel;

    @Wire private Progressmeter progressBar;
    @Wire private Label progressPctLabel;
    @Wire private Label progressStepLabel;

    @Wire private Listbox checklistBox;
    @Wire private Listbox messagesBox;

    @Wire private Button exportPdfBtn;
    @Wire private Button editDetailsBtn;
    @Wire private Button sendMessageBtn;
    @Wire private Button liveChatBtn;

    // --- Initialization ---

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        loadStatusCards();
        loadProgressSection();
        loadChecklist();
        loadMessages();
    }

    // --- Data loading ---

    private void loadStatusCards() {
        // TODO: Replace with service call, e.g. applicationService.getById(appId)
        appStatusLabel.setValue("Under Review");
        appIdLabel.setValue("APP-88241-TX");
        submissionDateLabel.setValue("Oct 24, 2023");
        processingFeeLabel.setValue("$1,250.00");
    }

    private void loadProgressSection() {
        // TODO: Replace with calculated progress from application service
        int pct = 85;
        progressBar.setValue(pct);
        progressPctLabel.setValue(pct + "% Complete");
        progressStepLabel.setValue("Step 3 of 5: Document Verification");
    }

    private void loadChecklist() {
        // TODO: Replace with applicationService.getChecklistItems(appId)
        for (ChecklistItem item : getSampleChecklistItems()) {
            checklistBox.appendChild(buildChecklistItem(item));
        }
    }

    private void loadMessages() {
        // TODO: Replace with messageService.getRecentMessages(appId, limit=4)
        for (Message msg : getSampleMessages()) {
            messagesBox.appendChild(buildMessageItem(msg));
        }
    }

    // --- Component builders ---

    private Listitem buildChecklistItem(ChecklistItem item) {
        String iconClass;
        String iconContent;
        String metaHtml;

        switch (item.status) {
            case DONE:
                iconClass = "at-done";
                iconContent = "&#10003;";
                metaHtml = "<div class='at-check-date'>" + esc(item.meta) + "</div>";
                break;
            case IN_PROGRESS:
                iconClass = "at-progress";
                iconContent = "&#9679;";
                metaHtml = "<span class='at-badge at-badge-progress'>" + esc(item.meta) + "</span>";
                break;
            default: // UPCOMING
                iconClass = "at-upcoming";
                iconContent = "&#9679;";
                metaHtml = "<span class='at-badge at-badge-upcoming'>" + esc(item.meta) + "</span>";
                break;
        }

        Html html = new Html();
        html.setContent(
            "<div class='at-check-row'>" +
                "<div class='at-check-status " + iconClass + "'>" + iconContent + "</div>" +
                "<div class='at-check-info'>" +
                    "<div class='at-check-name'>" + esc(item.name) + "</div>" +
                    "<div class='at-check-desc'>" + esc(item.description) + "</div>" +
                "</div>" +
                "<div class='at-check-meta'>" + metaHtml + "</div>" +
            "</div>"
        );

        Listcell cell = new Listcell();
        cell.appendChild(html);
        Listitem li = new Listitem();
        li.appendChild(cell);
        return li;
    }

    private Listitem buildMessageItem(Message msg) {
        Html html = new Html();
        html.setContent(
            "<div class='at-msg-row'>" +
                "<div class='at-msg-avatar' style='background:" + msg.avatarColor + "'>" + esc(msg.initials) + "</div>" +
                "<div class='at-msg-body'>" +
                    "<div class='at-msg-hdr'>" +
                        "<span class='at-msg-name'>" + esc(msg.name) + "</span>" +
                        "<span class='at-msg-time'>" + esc(msg.time) + "</span>" +
                    "</div>" +
                    "<div class='at-msg-text'>" + esc(msg.preview) + "</div>" +
                "</div>" +
            "</div>"
        );

        Listcell cell = new Listcell();
        cell.appendChild(html);
        Listitem li = new Listitem();
        li.appendChild(cell);
        return li;
    }

    // --- Event handlers ---

    @Listen("onClick = #exportPdfBtn")
    public void onExportPdf() {
        // TODO: Implement PDF export — call documentService.exportPdf(appId)
        Clients.showNotification("Generating PDF export...", "info", null, "top_right", 3000);
    }

    @Listen("onClick = #editDetailsBtn")
    public void onEditDetails() {
        // TODO: Open edit details dialog or navigate to edit page
        Clients.showNotification("Edit details — not yet implemented", "warning", null, "top_right", 3000);
    }

    @Listen("onClick = #sendMessageBtn")
    public void onSendMessage() {
        // TODO: Open compose message dialog — Executions.createComponents("compose-message.zul", ...)
        Clients.showNotification("Compose message — not yet implemented", "info", null, "top_right", 3000);
    }

    @Listen("onClick = #liveChatBtn")
    public void onLiveChat() {
        // TODO: Integrate live chat provider (e.g., Intercom, Zendesk)
        Clients.showNotification("Connecting to live chat...", "info", null, "top_right", 3000);
    }

    // --- Sample data ---

    private List<ChecklistItem> getSampleChecklistItems() {
        return Arrays.asList(
            new ChecklistItem("Identity Verification",  "Government-issued ID required",        CheckStatus.DONE,        "Oct 25"),
            new ChecklistItem("Employment History",     "Last 3 years of employment records",   CheckStatus.DONE,        "Oct 28"),
            new ChecklistItem("Financial Statement",    "Processing bank statement info",        CheckStatus.IN_PROGRESS, "In Progress"),
            new ChecklistItem("Legal Background Check", "We will start this step soon",         CheckStatus.UPCOMING,    "Upcoming")
        );
    }

    private List<Message> getSampleMessages() {
        return Arrays.asList(
            new Message("Marcus Chan",   "MC", "#3b82f6", "1 day ago",
                        "We've received your highest resolution scan of your passport's front page."),
            new Message("Sarah Jenkins", "SJ", "#8b5cf6", "3 days ago",
                        "Your employment verification has been submitted successfully."),
            new Message("System Bot",    "SB", "#374151", "6 hrs ago",
                        "Application status updated to 'Under Review'."),
            new Message("Leo Roberts",   "LR", "#059669", "Yesterday",
                        "Please reach out if you need any assistance with the final steps.")
        );
    }

    // --- Utility ---

    private static String esc(String text) {
        if (text == null) return "";
        return text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\"", "&quot;")
                   .replace("'", "&#39;");
    }

    // --- Inner model classes ---
    // NOTE: Refactor these into separate domain model files for production use.

    public enum CheckStatus { DONE, IN_PROGRESS, UPCOMING }

    public static class ChecklistItem {
        public final String name, description, meta;
        public final CheckStatus status;

        public ChecklistItem(String name, String description, CheckStatus status, String meta) {
            this.name = name;
            this.description = description;
            this.status = status;
            this.meta = meta;
        }
    }

    public static class Message {
        public final String name, initials, avatarColor, time, preview;

        public Message(String name, String initials, String avatarColor, String time, String preview) {
            this.name = name;
            this.initials = initials;
            this.avatarColor = avatarColor;
            this.time = time;
            this.preview = preview;
        }
    }
}