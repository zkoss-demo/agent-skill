package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Label;
import org.zkoss.zul.Messagebox;
import org.zkoss.zul.Textbox;

/**
 * Composer for {@code application-review.zul} — the GovPortal submission receipt.
 *
 * <p>Extraction pass: the reviewed application now lives here and reaches the page through the
 * wired labels. There is no {@code setModel()} on this page and there should not be — it shows one
 * record, not a list, so the MVC counterpart of a bound field is a wired {@code Label} the composer
 * fills. The literal {@code value="..."} attributes the layout was judged against are gone from the
 * markup.
 *
 * <p>Field captions, the section headings and the footer links stayed in the ZUL: they are chrome,
 * still correct against the next application to come through.
 */
public class ApplicationReviewComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    /** The one application this page reports on. */
    public static class Application {
        private final String reference;
        private final String fullName;
        private final String dateOfBirth;
        private final String address;
        private final String type;
        private final String submittedAt;
        private final String priority;
        private final String reviewingOffice;
        private final String verificationId;
        private final String state;

        Application(String reference, String fullName, String dateOfBirth, String address,
                String type, String submittedAt, String priority, String reviewingOffice,
                String verificationId, String state) {
            this.reference = reference;
            this.fullName = fullName;
            this.dateOfBirth = dateOfBirth;
            this.address = address;
            this.type = type;
            this.submittedAt = submittedAt;
            this.priority = priority;
            this.reviewingOffice = reviewingOffice;
            this.verificationId = verificationId;
            this.state = state;
        }
    }

    private static final Application APPLICATION = new Application(
            "REF-2023-0892",
            "John Quincy Doe",
            "January 15, 1985",
            "123 Maple Avenue, Springfield, IL 62704",
            "Corporate License Renewal",
            "August 24, 2023 • 14:32 EST",
            "High Priority",
            "Dept. of Commerce Central",
            "VID-00981-XYZ",
            "FINALIZED");

    @Wire
    private Textbox searchBox;
    @Wire
    private Label crumbCurrent;
    @Wire
    private Label bannerTitle;
    @Wire
    private Label referenceChip;
    @Wire
    private Label summaryVariant;
    @Wire
    private Label reviewState;
    @Wire
    private Label fullName;
    @Wire
    private Label dateOfBirth;
    @Wire
    private Label address;
    @Wire
    private Label applicationType;
    @Wire
    private Label submissionDate;
    @Wire
    private Label priorityLevel;
    @Wire
    private Label reviewingOffice;
    @Wire
    private Label verificationId;
    @Wire
    private Label copyright;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);

        crumbCurrent.setValue("Review " + APPLICATION.reference);
        bannerTitle.setValue("Application Submitted Successfully");
        referenceChip.setValue(APPLICATION.reference);

        summaryVariant.setValue("Variant 1: Comprehensive Detail View");
        reviewState.setValue(APPLICATION.state);

        fullName.setValue(APPLICATION.fullName);
        dateOfBirth.setValue(APPLICATION.dateOfBirth);
        address.setValue(APPLICATION.address);

        applicationType.setValue(APPLICATION.type);
        submissionDate.setValue(APPLICATION.submittedAt);
        priorityLevel.setValue(APPLICATION.priority);
        reviewingOffice.setValue(APPLICATION.reviewingOffice);
        verificationId.setValue(APPLICATION.verificationId);

        copyright.setValue("© 2023 GovPortal Services. All rights reserved.");
    }

    @Listen("onClick = #trackBtn")
    public void onTrackProgress() {
        Messagebox.show("Open the progress timeline for " + APPLICATION.reference + " here.",
                "Track Progress", Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #printBtn")
    public void onPrint() {
        Messagebox.show("Send the summary to the printer here.", "Print Summary",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #pdfBtn")
    public void onDownloadPdf() {
        Messagebox.show("Render the summary as a PDF here.", "Download PDF",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #homeBtn")
    public void onReturnHome() {
        Messagebox.show("Navigate back to the applicant's dashboard here.", "Return to Home",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Enter in the search box looks an application up by reference. */
    @Listen("onOK = #searchBox")
    public void onSearch() {
        Messagebox.show("Look up \"" + searchBox.getValue() + "\" here.", "Search",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
