package zwriter;

import java.math.BigDecimal;
import java.text.NumberFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.util.Clients;
import org.zkoss.zul.Label;
import org.zkoss.zul.Progressmeter;
import org.zkoss.zul.Textbox;

/**
 * Composer for {@code app-tracker.zul} — the AppTracker Pro application overview.
 *
 * <p>This is working scaffolding: every value on the page comes from the sample data
 * built at the bottom of this class. Replace the {@code sample*()} methods with your
 * own service or repository calls; the {@code load*()} methods above them are already
 * written against the model types and need no changes.
 *
 * <p>The model types ({@link Application}, {@link ChecklistItem}, {@link Message}) are
 * declared as inner classes to keep the scaffold self-contained — move them into their
 * own files once the page talks to a real back end.
 */
public class AppTrackerComposer extends SelectorComposer<Component> {

	// --- Wired components: navigation ---
	@Wire
	private Textbox searchBox;

	// --- Wired components: summary stat cards ---
	@Wire
	private Label statusValue;
	@Wire
	private Label applicationId;
	@Wire
	private Label submissionDate;
	@Wire
	private Label processingFee;

	// --- Wired components: overall progress ---
	@Wire
	private Label progressPill;
	@Wire
	private Progressmeter progressBar;
	@Wire
	private Label progressStepIndex;
	@Wire
	private Label progressStepName;

	// --- Wired components: required checklist (meta column) ---
	@Wire
	private Label check1Meta;
	@Wire
	private Label check2Meta;
	@Wire
	private Label check3Meta;
	@Wire
	private Label check4Meta;

	// --- Wired components: recent messages ---
	@Wire
	private Label msg1Name;
	@Wire
	private Label msg1Time;
	@Wire
	private Label msg1Text;
	@Wire
	private Label msg2Name;
	@Wire
	private Label msg2Time;
	@Wire
	private Label msg2Text;
	@Wire
	private Label msg3Name;
	@Wire
	private Label msg3Time;
	@Wire
	private Label msg3Text;
	@Wire
	private Label msg4Name;
	@Wire
	private Label msg4Time;
	@Wire
	private Label msg4Text;

	// --- Formatters ---
	private static final DateTimeFormatter FULL_DATE = DateTimeFormatter.ofPattern("MMM d, yyyy", Locale.ENGLISH);
	private static final DateTimeFormatter SHORT_DATE = DateTimeFormatter.ofPattern("MMM d", Locale.ENGLISH);
	private static final NumberFormat CURRENCY = NumberFormat.getCurrencyInstance(Locale.US);

	// --- Initialization ---

	@Override
	public void doAfterCompose(Component comp) throws Exception {
		super.doAfterCompose(comp);
		loadSummary(sampleApplication());
		loadChecklist(sampleChecklist());
		loadMessages(sampleMessages());
	}

	/** Fills the four stat cards and the overall-progress card. */
	private void loadSummary(Application app) {
		statusValue.setValue(app.getStatus());
		applicationId.setValue(app.getId());
		submissionDate.setValue(FULL_DATE.format(app.getSubmittedOn()));
		processingFee.setValue(CURRENCY.format(app.getFee()));

		progressPill.setValue(app.getPercentComplete() + "% Complete");
		progressBar.setValue(app.getPercentComplete());
		progressStepIndex.setValue("Step " + app.getCurrentStep() + " of " + app.getTotalSteps() + ":");
		progressStepName.setValue(app.getCurrentStepName());
	}

	/**
	 * Fills the meta column of the checklist. The rows themselves are declared in the
	 * ZUL, so only as many items as there are rows are consumed.
	 */
	private void loadChecklist(List<ChecklistItem> items) {
		Label[] metas = { check1Meta, check2Meta, check3Meta, check4Meta };
		for (int i = 0; i < metas.length && i < items.size(); i++)
			metas[i].setValue(items.get(i).getMeta());
	}

	/** Fills the name, timestamp and body of each message row declared in the ZUL. */
	private void loadMessages(List<Message> messages) {
		Label[] names = { msg1Name, msg2Name, msg3Name, msg4Name };
		Label[] times = { msg1Time, msg2Time, msg3Time, msg4Time };
		Label[] texts = { msg1Text, msg2Text, msg3Text, msg4Text };
		for (int i = 0; i < names.length && i < messages.size(); i++) {
			Message m = messages.get(i);
			names[i].setValue(m.getSender());
			times[i].setValue(m.getSentAgo());
			texts[i].setValue(m.getBody());
		}
	}

	// --- Event handlers ---

	@Listen("onClick = #exportPdfBtn")
	public void onExportPdf() {
		// TODO replace with your reporting service, then stream the file to the browser.
		Clients.showNotification("Preparing the application PDF…");
	}

	@Listen("onClick = #editDetailsBtn")
	public void onEditDetails() {
		// TODO navigate to the edit form, or open it as a modal window.
		Clients.showNotification("Opening the application for editing…");
	}

	@Listen("onClick = #newMessageBtn")
	public void onNewMessage() {
		// TODO open a compose dialog and post through your messaging service.
		Clients.showNotification("Compose a new message to your case officer.");
	}

	@Listen("onClick = #liveChatBtn")
	public void onLiveChat() {
		// TODO hand off to your support-chat widget.
		Clients.showNotification("Connecting you to live chat support…");
	}

	@Listen("onClick = #notificationsBtn")
	public void onNotifications() {
		Clients.showNotification("You have 4 unread notifications.");
	}

	@Listen("onClick = #settingsBtn")
	public void onSettings() {
		Clients.showNotification("Account settings are not wired up in this scaffold.");
	}

	@Listen("onOK = #searchBox")
	public void onSearch() {
		String keyword = searchBox.getValue();
		// TODO query your application store and navigate to the results page.
		Clients.showNotification(keyword == null || keyword.isEmpty()
				? "Enter an application ID or applicant name to search."
				: "Searching applications for \"" + keyword + "\"…");
	}

	// --- Sample data (replace with real service calls) ---

	private Application sampleApplication() {
		Application app = new Application();
		app.setStatus("Under Review");
		app.setId("APP-88241-TX");
		app.setSubmittedOn(LocalDate.of(2023, 10, 24));
		app.setFee(new BigDecimal("1250.00"));
		app.setPercentComplete(65);
		app.setCurrentStep(3);
		app.setTotalSteps(5);
		app.setCurrentStepName("Document Verification");
		return app;
	}

	private List<ChecklistItem> sampleChecklist() {
		return List.of(
				ChecklistItem.completed(LocalDate.of(2023, 10, 25)),
				ChecklistItem.completed(LocalDate.of(2023, 10, 26)),
				ChecklistItem.pending("In Progress"),
				ChecklistItem.pending("Upcoming"));
	}

	private List<Message> sampleMessages() {
		return List.of(
				new Message("Marcus Chen", "2m ago",
						"\"We need a higher resolution scan of your passport's front page.\""),
				new Message("Sarah Jenkins", "1h ago",
						"\"Your employment history for 2021 has been successfully verified.\""),
				new Message("System Bot", "5h ago",
						"\"Application status updated to 'In Review' after document submission.\""),
				new Message("Leo Roberts", "Yesterday",
						"\"Welcome to AppTracker! I'll be your main point of contact.\""));
	}

	// --- Model types ---

	/** The application being tracked, plus its position in the review workflow. */
	public static class Application {
		private String status;
		private String id;
		private LocalDate submittedOn;
		private BigDecimal fee;
		private int percentComplete;
		private int currentStep;
		private int totalSteps;
		private String currentStepName;

		public String getStatus() {
			return status;
		}

		public void setStatus(String status) {
			this.status = status;
		}

		public String getId() {
			return id;
		}

		public void setId(String id) {
			this.id = id;
		}

		public LocalDate getSubmittedOn() {
			return submittedOn;
		}

		public void setSubmittedOn(LocalDate submittedOn) {
			this.submittedOn = submittedOn;
		}

		public BigDecimal getFee() {
			return fee;
		}

		public void setFee(BigDecimal fee) {
			this.fee = fee;
		}

		public int getPercentComplete() {
			return percentComplete;
		}

		public void setPercentComplete(int percentComplete) {
			this.percentComplete = percentComplete;
		}

		public int getCurrentStep() {
			return currentStep;
		}

		public void setCurrentStep(int currentStep) {
			this.currentStep = currentStep;
		}

		public int getTotalSteps() {
			return totalSteps;
		}

		public void setTotalSteps(int totalSteps) {
			this.totalSteps = totalSteps;
		}

		public String getCurrentStepName() {
			return currentStepName;
		}

		public void setCurrentStepName(String currentStepName) {
			this.currentStepName = currentStepName;
		}
	}

	/**
	 * One row of the required checklist. A completed item shows the date it cleared;
	 * anything still outstanding shows a status word instead.
	 */
	public static class ChecklistItem {
		private final LocalDate completedOn;
		private final String statusText;

		private ChecklistItem(LocalDate completedOn, String statusText) {
			this.completedOn = completedOn;
			this.statusText = statusText;
		}

		public static ChecklistItem completed(LocalDate completedOn) {
			return new ChecklistItem(completedOn, null);
		}

		public static ChecklistItem pending(String statusText) {
			return new ChecklistItem(null, statusText);
		}

		/** What the right-hand column of the row displays. */
		public String getMeta() {
			return completedOn != null ? SHORT_DATE.format(completedOn) : statusText;
		}
	}

	/** One entry in the Recent Messages panel. */
	public static class Message {
		private final String sender;
		private final String sentAgo;
		private final String body;

		public Message(String sender, String sentAgo, String body) {
			this.sender = sender;
			this.sentAgo = sentAgo;
			this.body = body;
		}

		public String getSender() {
			return sender;
		}

		public String getSentAgo() {
			return sentAgo;
		}

		public String getBody() {
			return body;
		}
	}
}
