package zwriter;

import java.util.Arrays;
import java.util.List;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Label;
import org.zkoss.zul.Listbox;
import org.zkoss.zul.ListModelList;
import org.zkoss.zul.Messagebox;
import org.zkoss.zul.Progressmeter;
import org.zkoss.zul.Tab;
import org.zkoss.zul.Textbox;

/**
 * Composer for {@code bank-reconciliation.zul} — the FinCore Recon reconciliation screen.
 *
 * <p>Extraction pass: the transactions now live here and reach the page through {@code setModel()}
 * on the wired listbox, rendered by the {@code <template name="model">} left in the ZUL. The eight
 * literal {@code <listitem>} elements the layout was judged against have been deleted — a model
 * discards markup rows silently, so leaving them would have kept rows on the page that display
 * nothing.
 *
 * <p>Sixteen transactions against a {@code pageSize} of eight, which is what puts the second page
 * on the pager. Column captions, the tab wording and the connection indicators stayed in the ZUL:
 * they are chrome, still correct tomorrow against tomorrow's ledger.
 */
public class BankReconciliationComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    /** One line of the bank statement, beside its ledger match. */
    public static class Transaction {
        private final String date;
        private final String description;
        private final String detail;
        private final String reference;
        private final String debit;
        private final String credit;
        private final String status;
        private final String matchId;

        Transaction(String date, String description, String detail, String reference,
                String debit, String credit, String status, String matchId) {
            this.date = date;
            this.description = description;
            this.detail = detail;
            this.reference = reference;
            this.debit = debit;
            this.credit = credit;
            this.status = status;
            this.matchId = matchId;
        }

        public String getDate() {
            return date;
        }

        public String getDescription() {
            return description;
        }

        public String getDetail() {
            return detail;
        }

        public String getReference() {
            return reference;
        }

        /** An em dash stands in for "no amount on this side", as the design shows. */
        public String getDebitText() {
            return debit == null ? "—" : debit;
        }

        public String getDebitSclass() {
            return debit == null ? "br-nil" : "br-debit br-mono";
        }

        public String getCreditText() {
            return credit == null ? "—" : credit;
        }

        public String getCreditSclass() {
            return credit == null ? "br-nil" : "br-credit br-mono";
        }

        public String getStatus() {
            return status;
        }

        public String getStatusSclass() {
            return "br-status br-status-" + status.toLowerCase();
        }

        public String getStatusDotSclass() {
            return "br-status-dot br-dot-" + status.toLowerCase();
        }

        public String getStatusTextSclass() {
            return "br-status-label br-status-text-" + status.toLowerCase();
        }

        public String getMatchId() {
            return matchId;
        }

        public boolean isMatched() {
            return matchId != null;
        }

        /** The template needs the negative too; EL dialects differ on {@code not}. */
        public boolean isUnmatched() {
            return matchId == null;
        }
    }

    private static final List<Transaction> TRANSACTIONS = Arrays.asList(
            new Transaction("Oct 24, 2023", "Wire Transfer Outbound - Amazon AWS",
                    "Cloud Services Sub - North Virginia", "WT-90218-AF",
                    "1,240.00", null, "PENDING", null),
            new Transaction("Oct 24, 2023", "Stripe Payout #24110", "Sales Batch Oct 23rd",
                    "STR-PX-8812", null, "14,210.50", "MATCHED", "#M-9412"),
            new Transaction("Oct 23, 2023", "Office Lease - Metropolis Towers",
                    "Monthly Rent Payment", "CHK-004412", "8,500.00", null, "FLAGGED", null),
            new Transaction("Oct 23, 2023", "Client Deposit - Global Tech Inc",
                    "Invoice #INV-2023-45", "DP-55123-01", null, "4,500.00", "PENDING", null),
            new Transaction("Oct 22, 2023", "Corporate Card - P. Smith", "Travel & Lodging - NY",
                    "CC-44910-XX", "642.18", null, "MATCHED", "#M-9399"),
            new Transaction("Oct 22, 2023", "Software License - Figma Inc",
                    "Design Team Subscription", "FIG-SUBS-10", "150.00", null, "PENDING", null),
            new Transaction("Oct 21, 2023", "Internal Transfer - Payroll",
                    "Staff Wages - Biweekly", "PAY-OCT-21", "42,500.00", null,
                    "MATCHED", "#M-9350"),
            new Transaction("Oct 21, 2023", "Refund - Delta Airlines", "Cancelled Business Trip",
                    "REF-DA-901", null, "890.25", "PENDING", null),
            new Transaction("Oct 20, 2023", "Utility Payment - Con Edison",
                    "Head Office Electricity", "UTL-88120", "3,180.44", null, "PENDING", null),
            new Transaction("Oct 20, 2023", "Client Deposit - Nordwind Group",
                    "Invoice #INV-2023-41", "DP-55098-03", null, "18,900.00",
                    "MATCHED", "#M-9341"),
            new Transaction("Oct 19, 2023", "Merchant Fees - Stripe", "September Settlement",
                    "STR-FEE-0919", "412.77", null, "PENDING", null),
            new Transaction("Oct 19, 2023", "Insurance Premium - Aviva",
                    "Professional Indemnity Q4", "INS-Q4-2023", "6,750.00", null,
                    "FLAGGED", null),
            new Transaction("Oct 18, 2023", "Client Deposit - Helios Retail",
                    "Invoice #INV-2023-38", "DP-55071-02", null, "7,320.10",
                    "MATCHED", "#M-9318"),
            new Transaction("Oct 18, 2023", "Cloud Storage - Backblaze", "Archive Tier B2",
                    "BB-SUBS-77", "289.05", null, "PENDING", null),
            new Transaction("Oct 17, 2023", "FX Settlement - EUR/USD", "Treasury Hedge Roll",
                    "FX-EU-4410", "12,004.60", null, "PENDING", null),
            new Transaction("Oct 17, 2023", "Interest Credit - Chase Business",
                    "Monthly Interest", "INT-OCT-23", null, "1,105.88", "MATCHED", "#M-9302"));

    private static final int PAGE_SIZE = 8;
    private static final int RECONCILED_COUNT = 142;

    @Wire
    private Listbox txList;
    @Wire
    private Textbox searchBox;
    @Wire
    private Tab unreconciledTab;
    @Wire
    private Tab reconciledTab;
    @Wire
    private Label userName;
    @Wire
    private Label userRole;
    @Wire
    private Label userInitials;
    @Wire
    private Label statementBalance;
    @Wire
    private Label statementNote;
    @Wire
    private Label bookBalance;
    @Wire
    private Label bookNote;
    @Wire
    private Label difference;
    @Wire
    private Progressmeter matchMeter;
    @Wire
    private Label matchCount;
    @Wire
    private Label matchPercent;
    @Wire
    private Label rangeNote;
    @Wire
    private Label systemInfo;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);

        // setModel() copies the model's own multiple flag onto the listbox, and ListModelList
        // defaults to single selection -- so without this the checkmark column renders as radio
        // buttons and multiple="true" in the ZUL is silently overruled.
        ListModelList<Transaction> model = new ListModelList<>(TRANSACTIONS);
        model.setMultiple(true);
        txList.setModel(model);

        userName.setValue("Sarah Jenkins");
        userRole.setValue("SENIOR ACCOUNTANT");
        userInitials.setValue("SJ");

        statementBalance.setValue("$1,422,904.55");
        statementNote.setValue("Last synced: 14 mins ago");
        bookBalance.setValue("$1,418,250.20");
        bookNote.setValue("GL Account: 10100-Cash");
        difference.setValue("$4,654.35");

        int matched = 142;
        int total = 158;
        // Rounded, not truncated: 142/158 is 89.9%, and truncating reports it as 89%.
        int percent = Math.round(matched * 100f / total);
        matchMeter.setValue(percent);
        matchCount.setValue("Matches: " + matched + "/" + total);
        matchPercent.setValue(percent + "% Complete");

        int shown = Math.min(PAGE_SIZE, TRANSACTIONS.size());
        rangeNote.setValue("Showing 1 - " + shown + " of " + TRANSACTIONS.size()
                + " transactions");

        unreconciledTab.setLabel("Unreconciled (" + TRANSACTIONS.size() + ")");
        reconciledTab.setLabel("Reconciled (" + RECONCILED_COUNT + ")");

        systemInfo.setValue("SYSTEM V4.2.1 • LATENCY: 24MS");
    }

    @Listen("onClick = #autoMatchBtn")
    public void onAutoMatch() {
        Messagebox.show("Run the auto-matching pass over the unreconciled transactions here.",
                "Auto-match", Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #finalizeBtn")
    public void onFinalize() {
        Messagebox.show("Close the period once the difference is nil.", "Finalize",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    @Listen("onClick = #adjustmentBtn")
    public void onAdjustment() {
        Messagebox.show("Post a manual adjustment here.", "Adjustment",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Enter in the search box narrows the transaction list. */
    @Listen("onOK = #searchBox")
    public void onSearch() {
        String term = searchBox.getValue();
        Messagebox.show("Filter the transactions by \"" + term + "\" here.", "Search",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Selecting rows is what the checkbox column is for; report what the user picked. */
    @Listen("onSelect = #txList")
    public void onSelectTransactions() {
        int picked = txList.getSelectedCount();
        Messagebox.show(picked + " transaction(s) selected.", "Selection",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
