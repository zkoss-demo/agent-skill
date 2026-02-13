package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.util.Clients;
import org.zkoss.zul.*;

import java.text.NumberFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class BankReconciliationComposer extends SelectorComposer<Component> {

    @Wire
    private Listbox txnListbox;
    @Wire
    private Listbox reconciledListbox;
    @Wire
    private Listbox allTxnListbox;
    @Wire
    private Textbox searchBox;
    @Wire
    private Button autoMatchBtn;
    @Wire
    private Button finalizeBtn;
    @Wire
    private Button adjustmentBtn;

    private static final NumberFormat CURRENCY_FMT = NumberFormat.getNumberInstance(Locale.US);
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("MMM dd, yyyy");

    private List<Transaction> allTransactions;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        CURRENCY_FMT.setMinimumFractionDigits(2);
        CURRENCY_FMT.setMaximumFractionDigits(2);
        allTransactions = loadSampleData();
        populateUnreconciled();
        populateReconciled();
        populateAll();
    }

    private void populateUnreconciled() {
        txnListbox.getItems().clear();
        for (Transaction txn : allTransactions) {
            if ("PENDING".equals(txn.status)) {
                txnListbox.appendChild(createListitem(txn));
            }
        }
    }

    private void populateReconciled() {
        reconciledListbox.getItems().clear();
        for (Transaction txn : allTransactions) {
            if ("MATCHED".equals(txn.status)) {
                reconciledListbox.appendChild(createListitem(txn));
            }
        }
    }

    private void populateAll() {
        allTxnListbox.getItems().clear();
        for (Transaction txn : allTransactions) {
            allTxnListbox.appendChild(createListitem(txn));
        }
    }

    private Listitem createListitem(Transaction txn) {
        Listitem li = new Listitem();

        // Date
        li.appendChild(new Listcell(txn.date.format(DATE_FMT)));

        // Description (main + sub)
        Listcell descCell = new Listcell();
        Vlayout descLayout = new Vlayout();
        Label mainLabel = new Label(txn.description);
        mainLabel.setSclass("recon-desc-main");
        descLayout.appendChild(mainLabel);
        if (txn.subDescription != null && !txn.subDescription.isEmpty()) {
            Label subLabel = new Label(txn.subDescription);
            subLabel.setSclass("recon-desc-sub");
            descLayout.appendChild(subLabel);
        }
        descCell.appendChild(descLayout);
        li.appendChild(descCell);

        // Ref
        li.appendChild(new Listcell(txn.ref));

        // Amount
        li.appendChild(new Listcell(txn.amount > 0 ? CURRENCY_FMT.format(txn.amount) : ""));

        // Credit
        Listcell creditCell = new Listcell();
        if (txn.credit > 0) {
            Label creditLabel = new Label("+" + CURRENCY_FMT.format(txn.credit));
            creditLabel.setSclass("recon-amount recon-amount--credit");
            creditCell.appendChild(creditLabel);
        }
        li.appendChild(creditCell);

        // Debit
        Listcell debitCell = new Listcell();
        if (txn.debit > 0) {
            Label debitLabel = new Label(CURRENCY_FMT.format(txn.debit));
            debitLabel.setSclass("recon-amount recon-amount--debit");
            debitCell.appendChild(debitLabel);
        }
        li.appendChild(debitCell);

        // Status badge
        Listcell statusCell = new Listcell();
        Label badge = new Label(txn.status.substring(0, 1) + txn.status.substring(1).toLowerCase());
        badge.setSclass("recon-badge " +
                ("MATCHED".equals(txn.status) ? "recon-badge--matched" : "recon-badge--pending"));
        statusCell.appendChild(badge);
        li.appendChild(statusCell);

        // Action
        Listcell actionCell = new Listcell();
        Button actionBtn = new Button();
        actionBtn.setIconSclass("z-icon-ellipsis-h");
        actionBtn.setSclass("recon-action-btn");
        actionCell.appendChild(actionBtn);
        li.appendChild(actionCell);

        return li;
    }

    @Listen("onClick = #autoMatchBtn")
    public void onAutoMatch() {
        Clients.showNotification("Running auto-match...", "info", null, "middle_center", 2000);
    }

    @Listen("onClick = #finalizeBtn")
    public void onFinalize() {
        Clients.showNotification("Finalizing reconciliation...", "info", null, "middle_center", 2000);
    }

    @Listen("onClick = #adjustmentBtn")
    public void onAdjustment() {
        Clients.showNotification("Opening adjustment dialog...", "info", null, "middle_center", 2000);
    }

    @Listen("onChange = #searchBox")
    public void onSearch() {
        String query = searchBox.getValue().toLowerCase().trim();
        txnListbox.getItems().clear();
        for (Transaction txn : allTransactions) {
            if ("PENDING".equals(txn.status) && matchesSearch(txn, query)) {
                txnListbox.appendChild(createListitem(txn));
            }
        }
    }

    private boolean matchesSearch(Transaction txn, String query) {
        if (query.isEmpty()) return true;
        return txn.description.toLowerCase().contains(query)
                || txn.ref.toLowerCase().contains(query)
                || (txn.subDescription != null && txn.subDescription.toLowerCase().contains(query));
    }

    // --- Sample data ---

    private List<Transaction> loadSampleData() {
        List<Transaction> list = new ArrayList<>();
        list.add(new Transaction(LocalDate.of(2023, 10, 24), "Wire Transfer Outbound - Amazon AWS",
                "Cloud Services East - North Virginia", "WR_F01245", 1240.00, 0, 0, "PENDING"));
        list.add(new Transaction(LocalDate.of(2023, 10, 24), "Stripe Payout #24710",
                null, "PY_09213", 14256.99, 14256.99, 0, "PENDING"));
        list.add(new Transaction(LocalDate.of(2023, 10, 23), "Office Lease - Metropolis Towers",
                null, "OM_89212", 0, 0, 8500.00, "PENDING"));
        list.add(new Transaction(LocalDate.of(2023, 10, 23), "Client Deposit - Global Tech Inc",
                null, "DP_00121", 0, 9825.00, 0, "PENDING"));
        list.add(new Transaction(LocalDate.of(2023, 10, 22), "Corporate Card - P. Smith",
                "Travel & Lodging - NY", "CC_19243", 0, 0, 42.18, "MATCHED"));
        list.add(new Transaction(LocalDate.of(2023, 10, 22), "Software License - Figma Inc",
                null, "FS_10199", 0, 580.00, 0, "PENDING"));
        list.add(new Transaction(LocalDate.of(2023, 10, 21), "Internal Transfer - Payroll",
                null, "Pay_097_21", 0, 0, 45200.00, "MATCHED"));
        list.add(new Transaction(LocalDate.of(2023, 10, 21), "Refund - Delta Airlines",
                "Cancelled Business Trip", "REF_184_01", 0, 690.25, 0, "PENDING"));
        return list;
    }

    public static class Transaction {
        public final LocalDate date;
        public final String description;
        public final String subDescription;
        public final String ref;
        public final double amount;
        public final double credit;
        public final double debit;
        public final String status;

        public Transaction(LocalDate date, String description, String subDescription,
                           String ref, double amount, double credit, double debit, String status) {
            this.date = date;
            this.description = description;
            this.subDescription = subDescription;
            this.ref = ref;
            this.amount = amount;
            this.credit = credit;
            this.debit = debit;
            this.status = status;
        }
    }
}
