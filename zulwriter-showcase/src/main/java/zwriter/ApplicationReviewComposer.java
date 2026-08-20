package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.Executions;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.util.Clients;
import org.zkoss.zul.Label;
import org.zkoss.zul.Span;
import org.zkoss.zul.Textbox;

/**
 * Composer for application-review.zul - renders a submitted application summary.
 */
public class ApplicationReviewComposer extends SelectorComposer<Component> {

	// --- Wired components ---
	@Wire
	private Textbox searchBox;
	@Wire
	private Label breadcrumbCurrent;
	@Wire
	private Label referenceChip;
	@Wire
	private Label statusBadge;
	@Wire
	private Label fullName;
	@Wire
	private Label dateOfBirth;
	@Wire
	private Label residentialAddress;
	@Wire
	private Label applicationType;
	@Wire
	private Label submissionDate;
	@Wire
	private Span priorityDot;
	@Wire
	private Label priorityLevel;
	@Wire
	private Label reviewingOffice;
	@Wire
	private Label verificationId;

	private ApplicationSummary summary;

	// --- Initialization ---
	@Override
	public void doAfterCompose(Component comp) throws Exception {
		super.doAfterCompose(comp);
		summary = loadSummary();
		renderSummary();
	}

	/** Replace with a real service/repository lookup by reference number. */
	private ApplicationSummary loadSummary() {
		ApplicationSummary s = new ApplicationSummary();
		s.referenceNumber = "REF-2023-0892";
		s.status = "FINALIZED";
		s.fullName = "John Quincy Doe";
		s.dateOfBirth = "January 15, 1985";
		s.residentialAddress = "123 Maple Avenue, Springfield, IL 62704";
		s.applicationType = "Corporate License Renewal";
		s.submissionDate = "August 24, 2023 • 14:32 EST";
		s.priority = "High Priority";
		s.reviewingOffice = "Dept. of Commerce Central";
		s.verificationId = "VID-00981-XYZ";
		return s;
	}

	private void renderSummary() {
		breadcrumbCurrent.setValue("Review " + summary.referenceNumber);
		referenceChip.setValue(summary.referenceNumber);
		statusBadge.setValue(summary.status);
		fullName.setValue(summary.fullName);
		dateOfBirth.setValue(summary.dateOfBirth);
		residentialAddress.setValue(summary.residentialAddress);
		applicationType.setValue(summary.applicationType);
		submissionDate.setValue(summary.submissionDate);
		priorityLevel.setValue(summary.priority);
		priorityDot.setSclass("gp-dot " + priorityDotSclass(summary.priority));
		reviewingOffice.setValue(summary.reviewingOffice);
		verificationId.setValue(summary.verificationId);
	}

	private String priorityDotSclass(String priority) {
		if (priority.startsWith("High")) {
			return "gp-dot-high";
		}
		return priority.startsWith("Low") ? "gp-dot-low" : "gp-dot-normal";
	}

	// --- Events ---
	@Listen("onOK = #searchBox")
	public void onSearch() {
		// Replace with a redirect to the application search results page.
		Clients.showNotification("Searching applications for: " + searchBox.getValue());
	}

	@Listen("onClick = #notificationsBtn")
	public void onShowNotifications() {
		Clients.showNotification("No new notifications.");
	}

	@Listen("onClick = #trackProgressBtn")
	public void onTrackProgress() {
		Executions.sendRedirect("app-tracker.zul?ref=" + summary.referenceNumber);
	}

	@Listen("onClick = #printBtn")
	public void onPrintSummary() {
		Clients.print();
	}

	@Listen("onClick = #downloadPdfBtn")
	public void onDownloadPdf() {
		// Replace with Filedownload.save(pdfBytes, "application/pdf", fileName).
		Clients.showNotification("Preparing PDF for " + summary.referenceNumber + "...");
	}

	@Listen("onClick = #homeBtn")
	public void onReturnHome() {
		Executions.sendRedirect("index.zul");
	}

	// --- Data model (move to its own file in a real application) ---
	public static class ApplicationSummary {
		public String referenceNumber;
		public String status;
		public String fullName;
		public String dateOfBirth;
		public String residentialAddress;
		public String applicationType;
		public String submissionDate;
		public String priority;
		public String reviewingOffice;
		public String verificationId;
	}
}
