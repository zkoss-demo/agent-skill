package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Button;
import org.zkoss.zul.Image;
import org.zkoss.zul.Label;
import org.zkoss.zul.Window;

/**
 * Composer for the Compare Revisions modal dialog (data-comparison-modal.zul).
 *
 * Scaffold: replace the sample data and TODO comments with real service calls.
 */
public class CompareRevisionsComposer extends SelectorComposer<Component> {

    // --- Wired components ---

    @Wire
    private Window compareRevisionsWin;

    @Wire
    private Image modifiedByAvatar;

    @Wire
    private Label modifiedByEmail;

    @Wire
    private Button downloadPdfBtn;

    @Wire
    private Button doneBtn;

    // --- Initialization ---

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        loadRevisionData();
    }

    /**
     * Populates the dialog with revision comparison data.
     * TODO: Replace sample data with actual revision service call, e.g.:
     *   RevisionDiff diff = revisionService.compare(originalId, revisedId);
     */
    private void loadRevisionData() {
        // Sample data — static rows are already defined in ZUL.
        // Dynamic fields (avatar, email) are set here.

        // TODO: load avatar URL from user profile service
        modifiedByAvatar.setSrc("/img/avatar-asmith.png");

        // TODO: resolve email from revision diff
        modifiedByEmail.setValue("a.smith@company.com");
    }

    // --- Event Handlers ---

    @Listen("onClick = #downloadPdfBtn")
    public void onDownloadPdf() {
        // TODO: generate and stream PDF report to client
        // Example: Filedownload.save(pdfBytes, "application/pdf", "revision-diff.pdf");
    }

    @Listen("onClick = #doneBtn")
    public void onDone() {
        compareRevisionsWin.detach();
    }
}
