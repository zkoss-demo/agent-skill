package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.Executions;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Button;
import org.zkoss.zul.Textbox;

public class ApplicationReviewComposer extends SelectorComposer<Component> {

    @Wire
    private Textbox searchBox;

    @Wire
    private Button bellBtn;

    @Wire
    private Button trackProgressBtn;

    @Wire
    private Button printBtn;

    @Wire
    private Button downloadBtn;

    @Wire
    private Button returnHomeBtn;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        // Initialize page data here (e.g. load application details from service)
    }

    @Listen("onClick = #trackProgressBtn")
    public void onTrackProgress() {
        // Navigate to tracking page or open progress dialog
        Executions.sendRedirect("/track-progress?ref=REF-2023-0892");
    }

    @Listen("onClick = #printBtn")
    public void onPrint() {
        // Trigger browser print dialog via client-side script
        org.zkoss.zk.ui.util.Clients.evalJavaScript("window.print()");
    }

    @Listen("onClick = #downloadBtn")
    public void onDownloadPdf() {
        // Stream PDF to client (wire up to a PDF generation service)
        // Example: Executions.sendRedirect("/api/application/REF-2023-0892/pdf");
    }

    @Listen("onClick = #returnHomeBtn")
    public void onReturnHome() {
        Executions.sendRedirect("/");
    }
}
