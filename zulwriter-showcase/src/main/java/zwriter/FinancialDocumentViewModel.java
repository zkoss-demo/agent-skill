package zwriter;

import org.zkoss.bind.annotation.*;
import org.zkoss.zk.ui.event.UploadEvent;
import org.zkoss.zul.ListModelList;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;

public class FinancialDocumentViewModel {

    // --- Document header ---
    private FinancialDocument document;

    // --- Reference data ---
    private List<String> documentTypes;
    private List<String> currencies;
    private List<String> departments;
    private List<String> fiscalPeriods;
    private ListModelList<AccountCode> accountCodes;
    private List<String> costCenters;
    private List<TaxCode> taxCodes;

    // --- Payee search ---
    private String payeeSearchKeyword;
    private ListModelList<Payee> payeeResults;

    // --- Disbursement line items ---
    private ListModelList<LineItem> lineItems;
    private Set<LineItem> selectedLines;

    // --- Posting ---
    private ListModelList<JournalEntry> journalEntries;

    // --- Attachments ---
    private ListModelList<Attachment> attachments;

    // --- Approval history ---
    private ListModelList<ApprovalRecord> approvalHistory;

    // --- Action controls ---
    private String selectedAction;
    private String actionComments;

    @Init
    public void init() {
        document = new FinancialDocument();
        document.setDocumentNumber(generateDocumentNumber());
        document.setDocumentDate(new Date());
        document.setStatus("DRAFT");

        documentTypes = Arrays.asList(
            "Payment Voucher", "Disbursement Request", "Petty Cash",
            "Check Request", "Wire Transfer", "Journal Voucher"
        );
        currencies = Arrays.asList("USD", "EUR", "GBP", "JPY", "CNY");
        departments = Arrays.asList(
            "Finance", "Accounting", "Operations", "HR",
            "IT", "Sales", "Marketing", "Procurement"
        );
        fiscalPeriods = Arrays.asList(
            "2026-01", "2026-02", "2026-03", "2026-04",
            "2026-05", "2026-06", "2026-07", "2026-08",
            "2026-09", "2026-10", "2026-11", "2026-12"
        );
        costCenters = Arrays.asList("CC-100", "CC-200", "CC-300", "CC-400", "CC-500");

        accountCodes = new ListModelList<>();
        taxCodes = new ListModelList<>();
        payeeResults = new ListModelList<>();
        lineItems = new ListModelList<>();
        selectedLines = new LinkedHashSet<>();
        journalEntries = new ListModelList<>();
        attachments = new ListModelList<>();
        approvalHistory = new ListModelList<>();

        loadAccountCodes();
        loadTaxCodes();
    }

    // --- Commands ---

    @Command
    @NotifyChange({"payeeResults"})
    public void searchPayee() {
        payeeResults.clear();
        // TODO: Replace with actual payee/vendor lookup service
    }

    @Command
    @NotifyChange({"document"})
    public void selectPayee() {
        if (document.getPayee() != null) {
            document.setPayeeName(document.getPayee().getName());
        }
    }

    @Command
    @NotifyChange({"lineItems", "subtotal", "totalTax", "grandTotal", "document"})
    public void addLine() {
        LineItem newLine = new LineItem();
        newLine.setAmount(BigDecimal.ZERO);
        newLine.setTaxAmount(BigDecimal.ZERO);
        newLine.setNetAmount(BigDecimal.ZERO);
        lineItems.add(newLine);
        recalculateDocument();
    }

    @Command
    @NotifyChange({"lineItems", "selectedLines", "subtotal", "totalTax", "grandTotal", "document"})
    public void removeSelectedLines() {
        if (selectedLines != null && !selectedLines.isEmpty()) {
            lineItems.removeAll(selectedLines);
            selectedLines.clear();
            recalculateDocument();
        }
    }

    @Command
    @NotifyChange({"lineItems", "subtotal", "totalTax", "grandTotal", "document"})
    public void recalculateLine(@BindingParam("line") LineItem line) {
        if (line.getAmount() != null && line.getTaxCode() != null) {
            BigDecimal taxRate = line.getTaxCode().getRate();
            line.setTaxAmount(line.getAmount().multiply(taxRate).divide(
                BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP));
            line.setNetAmount(line.getAmount().add(line.getTaxAmount()));
        } else if (line.getAmount() != null) {
            line.setTaxAmount(BigDecimal.ZERO);
            line.setNetAmount(line.getAmount());
        }
        recalculateDocument();
    }

    @Command
    @NotifyChange({"lineItems"})
    public void onAccountSelect(@BindingParam("line") LineItem line) {
        if (line.getAccountCode() != null) {
            line.setAccountName(line.getAccountCode().getName());
        }
    }

    @Command
    public void editLine(@BindingParam("line") LineItem line) {
        // TODO: Open inline edit or dialog for detailed line editing
    }

    @Command
    @NotifyChange({"document", "lineItems", "journalEntries"})
    public void save() {
        recalculateDocument();
        generateJournalEntries();
        // TODO: Persist document and line items
    }

    @Command
    @NotifyChange({"document", "lineItems", "journalEntries", "approvalHistory"})
    public void executeAction() {
        if (selectedAction == null) {
            return;
        }
        switch (selectedAction) {
            case "DRAFT":
                document.setStatus("DRAFT");
                break;
            case "SUBMIT":
                document.setStatus("PENDING_APPROVAL");
                break;
            case "APPROVE":
                document.setStatus("APPROVED");
                break;
            case "REJECT":
                document.setStatus("REJECTED");
                break;
            case "RETURN":
                document.setStatus("RETURNED");
                break;
        }
        // TODO: Add approval history record and persist
    }

    @Command
    public void printPreview() {
        // TODO: Generate print-friendly preview
    }

    @Command
    public void cancel() {
        // TODO: Navigate back or close window
    }

    @Command
    @NotifyChange({"attachments"})
    public void uploadAttachment(@ContextParam(ContextType.TRIGGER_EVENT) UploadEvent event) {
        // TODO: Handle file upload and persist attachment
    }

    @Command
    public void downloadAttachment(@BindingParam("att") Attachment att) {
        // TODO: Stream file download
    }

    @Command
    @NotifyChange({"attachments"})
    public void deleteAttachment(@BindingParam("att") Attachment att) {
        attachments.remove(att);
    }

    // --- Helper methods ---

    private void recalculateDocument() {
        BigDecimal total = BigDecimal.ZERO;
        for (LineItem line : lineItems) {
            if (line.getNetAmount() != null) {
                total = total.add(line.getNetAmount());
            }
        }
        document.setTotalAmount(total);
    }

    private void generateJournalEntries() {
        journalEntries.clear();
        // TODO: Generate debit/credit journal entries based on line items
    }

    private String generateDocumentNumber() {
        // TODO: Replace with actual sequence generator
        return "FD-" + System.currentTimeMillis();
    }

    private void loadAccountCodes() {
        // TODO: Load from service/DAO
    }

    private void loadTaxCodes() {
        // TODO: Load from service/DAO
    }

    // --- Computed properties ---

    public BigDecimal getSubtotal() {
        return lineItems.stream()
            .map(l -> l.getAmount() != null ? l.getAmount() : BigDecimal.ZERO)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public BigDecimal getTotalTax() {
        return lineItems.stream()
            .map(l -> l.getTaxAmount() != null ? l.getTaxAmount() : BigDecimal.ZERO)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public BigDecimal getGrandTotal() {
        return lineItems.stream()
            .map(l -> l.getNetAmount() != null ? l.getNetAmount() : BigDecimal.ZERO)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public boolean isCanApprove() {
        // TODO: Check if current user has approval privileges
        return "PENDING_APPROVAL".equals(document.getStatus());
    }

    public String getStatusColor() {
        if (document == null || document.getStatus() == null) return "#333333";
        switch (document.getStatus()) {
            case "DRAFT": return "#999999";
            case "PENDING_APPROVAL": return "#CC8800";
            case "APPROVED": return "#006600";
            case "REJECTED": return "#CC0000";
            case "RETURNED": return "#CC6600";
            default: return "#333333";
        }
    }

    // --- Getters and setters ---

    public FinancialDocument getDocument() { return document; }
    public void setDocument(FinancialDocument document) { this.document = document; }

    public List<String> getDocumentTypes() { return documentTypes; }
    public List<String> getCurrencies() { return currencies; }
    public List<String> getDepartments() { return departments; }
    public List<String> getFiscalPeriods() { return fiscalPeriods; }
    public ListModelList<AccountCode> getAccountCodes() { return accountCodes; }
    public List<String> getCostCenters() { return costCenters; }
    public List<TaxCode> getTaxCodes() { return taxCodes; }

    public String getPayeeSearchKeyword() { return payeeSearchKeyword; }
    public void setPayeeSearchKeyword(String payeeSearchKeyword) { this.payeeSearchKeyword = payeeSearchKeyword; }
    public ListModelList<Payee> getPayeeResults() { return payeeResults; }

    public ListModelList<LineItem> getLineItems() { return lineItems; }
    public Set<LineItem> getSelectedLines() { return selectedLines; }
    public void setSelectedLines(Set<LineItem> selectedLines) { this.selectedLines = selectedLines; }

    public ListModelList<JournalEntry> getJournalEntries() { return journalEntries; }
    public ListModelList<Attachment> getAttachments() { return attachments; }
    public ListModelList<ApprovalRecord> getApprovalHistory() { return approvalHistory; }

    public String getSelectedAction() { return selectedAction; }
    public void setSelectedAction(String selectedAction) { this.selectedAction = selectedAction; }
    public String getActionComments() { return actionComments; }
    public void setActionComments(String actionComments) { this.actionComments = actionComments; }

    // --- Inner model classes (replace with your domain entities) ---

    public static class FinancialDocument {
        private String documentNumber;
        private String documentType;
        private Date documentDate;
        private String currency;
        private Payee payee;
        private String payeeName;
        private String department;
        private String description;
        private BigDecimal totalAmount = BigDecimal.ZERO;
        private String status;
        private Date postingDate;
        private String fiscalPeriod;
        private String glAccount;
        private String referenceNumber;
        private String postingRemarks;

        public String getDocumentNumber() { return documentNumber; }
        public void setDocumentNumber(String documentNumber) { this.documentNumber = documentNumber; }
        public String getDocumentType() { return documentType; }
        public void setDocumentType(String documentType) { this.documentType = documentType; }
        public Date getDocumentDate() { return documentDate; }
        public void setDocumentDate(Date documentDate) { this.documentDate = documentDate; }
        public String getCurrency() { return currency; }
        public void setCurrency(String currency) { this.currency = currency; }
        public Payee getPayee() { return payee; }
        public void setPayee(Payee payee) { this.payee = payee; }
        public String getPayeeName() { return payeeName; }
        public void setPayeeName(String payeeName) { this.payeeName = payeeName; }
        public String getDepartment() { return department; }
        public void setDepartment(String department) { this.department = department; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public BigDecimal getTotalAmount() { return totalAmount; }
        public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public Date getPostingDate() { return postingDate; }
        public void setPostingDate(Date postingDate) { this.postingDate = postingDate; }
        public String getFiscalPeriod() { return fiscalPeriod; }
        public void setFiscalPeriod(String fiscalPeriod) { this.fiscalPeriod = fiscalPeriod; }
        public String getGlAccount() { return glAccount; }
        public void setGlAccount(String glAccount) { this.glAccount = glAccount; }
        public String getReferenceNumber() { return referenceNumber; }
        public void setReferenceNumber(String referenceNumber) { this.referenceNumber = referenceNumber; }
        public String getPostingRemarks() { return postingRemarks; }
        public void setPostingRemarks(String postingRemarks) { this.postingRemarks = postingRemarks; }
    }

    public static class Payee {
        private String code;
        private String name;

        public Payee() {}
        public Payee(String code, String name) {
            this.code = code;
            this.name = name;
        }

        public String getCode() { return code; }
        public void setCode(String code) { this.code = code; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
    }

    public static class AccountCode {
        private String code;
        private String name;

        public AccountCode() {}
        public AccountCode(String code, String name) {
            this.code = code;
            this.name = name;
        }

        public String getCode() { return code; }
        public void setCode(String code) { this.code = code; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
    }

    public static class TaxCode {
        private String code;
        private String description;
        private BigDecimal rate;

        public TaxCode() {}
        public TaxCode(String code, String description, BigDecimal rate) {
            this.code = code;
            this.description = description;
            this.rate = rate;
        }

        public String getCode() { return code; }
        public void setCode(String code) { this.code = code; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public BigDecimal getRate() { return rate; }
        public void setRate(BigDecimal rate) { this.rate = rate; }
    }

    public static class LineItem {
        private AccountCode accountCode;
        private String accountName;
        private String costCenter;
        private String description;
        private BigDecimal amount;
        private TaxCode taxCode;
        private BigDecimal taxAmount;
        private BigDecimal netAmount;

        public AccountCode getAccountCode() { return accountCode; }
        public void setAccountCode(AccountCode accountCode) { this.accountCode = accountCode; }
        public String getAccountName() { return accountName; }
        public void setAccountName(String accountName) { this.accountName = accountName; }
        public String getCostCenter() { return costCenter; }
        public void setCostCenter(String costCenter) { this.costCenter = costCenter; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public BigDecimal getAmount() { return amount; }
        public void setAmount(BigDecimal amount) { this.amount = amount; }
        public TaxCode getTaxCode() { return taxCode; }
        public void setTaxCode(TaxCode taxCode) { this.taxCode = taxCode; }
        public BigDecimal getTaxAmount() { return taxAmount; }
        public void setTaxAmount(BigDecimal taxAmount) { this.taxAmount = taxAmount; }
        public BigDecimal getNetAmount() { return netAmount; }
        public void setNetAmount(BigDecimal netAmount) { this.netAmount = netAmount; }
    }

    public static class JournalEntry {
        private String account;
        private String description;
        private BigDecimal debit;
        private BigDecimal credit;

        public JournalEntry() {}
        public JournalEntry(String account, String description, BigDecimal debit, BigDecimal credit) {
            this.account = account;
            this.description = description;
            this.debit = debit;
            this.credit = credit;
        }

        public String getAccount() { return account; }
        public void setAccount(String account) { this.account = account; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public BigDecimal getDebit() { return debit; }
        public void setDebit(BigDecimal debit) { this.debit = debit; }
        public BigDecimal getCredit() { return credit; }
        public void setCredit(BigDecimal credit) { this.credit = credit; }
    }

    public static class Attachment {
        private String fileName;
        private String fileSize;
        private String uploadedBy;
        private String uploadDate;

        public String getFileName() { return fileName; }
        public void setFileName(String fileName) { this.fileName = fileName; }
        public String getFileSize() { return fileSize; }
        public void setFileSize(String fileSize) { this.fileSize = fileSize; }
        public String getUploadedBy() { return uploadedBy; }
        public void setUploadedBy(String uploadedBy) { this.uploadedBy = uploadedBy; }
        public String getUploadDate() { return uploadDate; }
        public void setUploadDate(String uploadDate) { this.uploadDate = uploadDate; }
    }

    public static class ApprovalRecord {
        private int step;
        private String approverName;
        private String action;
        private String actionDate;
        private String comments;

        public int getStep() { return step; }
        public void setStep(int step) { this.step = step; }
        public String getApproverName() { return approverName; }
        public void setApproverName(String approverName) { this.approverName = approverName; }
        public String getAction() { return action; }
        public void setAction(String action) { this.action = action; }
        public String getActionDate() { return actionDate; }
        public void setActionDate(String actionDate) { this.actionDate = actionDate; }
        public String getComments() { return comments; }
        public void setComments(String comments) { this.comments = comments; }
    }
}
