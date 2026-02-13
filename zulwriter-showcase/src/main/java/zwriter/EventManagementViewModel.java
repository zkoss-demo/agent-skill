package zwriter;

import org.zkoss.bind.annotation.*;
import org.zkoss.zul.ListModelList;

import java.util.*;

public class EventManagementViewModel {

    // --- Filter fields ---
    private String filterStatus;
    private Date filterDateFrom;
    private Date filterDateTo;

    // --- Grid data ---
    private ListModelList<EventItem> events;
    private Set<EventItem> selectedEvents;

    // --- Pagination ---
    private int activePage;
    private int pageSize = 20;
    private int totalSize;

    // --- Status options ---
    private List<String> statusOptions;

    @Init
    public void init() {
        statusOptions = Arrays.asList(
            "All", "Pending", "Approved", "Rejected", "Processing", "Completed", "Failed"
        );
        selectedEvents = new LinkedHashSet<>();
        loadEvents();
    }

    // --- Commands ---

    @Command
    @NotifyChange({"events", "totalSize", "activePage", "selectedEvents"})
    public void search() {
        activePage = 0;
        selectedEvents.clear();
        loadEvents();
    }

    @Command
    @NotifyChange({"filterStatus", "filterDateFrom", "filterDateTo",
                   "events", "totalSize", "activePage", "selectedEvents"})
    public void resetFilters() {
        filterStatus = null;
        filterDateFrom = null;
        filterDateTo = null;
        activePage = 0;
        selectedEvents.clear();
        loadEvents();
    }

    @Command
    @NotifyChange({"events", "totalSize", "activePage"})
    public void onPaging() {
        loadEvents();
    }

    @Command
    @NotifyChange({"events", "selectedEvents"})
    public void bulkApprove() {
        // TODO: Implement bulk approve logic for selectedEvents
        selectedEvents.clear();
        loadEvents();
    }

    @Command
    @NotifyChange({"events", "selectedEvents"})
    public void bulkReject() {
        // TODO: Implement bulk reject logic for selectedEvents
        selectedEvents.clear();
        loadEvents();
    }

    @Command
    @NotifyChange({"events", "selectedEvents", "totalSize"})
    public void bulkDelete() {
        // TODO: Implement bulk delete logic for selectedEvents
        selectedEvents.clear();
        loadEvents();
    }

    @Command
    @NotifyChange("selectedEvents")
    public void clearSelection() {
        selectedEvents.clear();
    }

    @Command
    public void viewEvent(@BindingParam("event") EventItem event) {
        // TODO: Open detail view / dialog for the event
    }

    @Command
    public void editEvent(@BindingParam("event") EventItem event) {
        // TODO: Open edit dialog for the event
    }

    // --- Data loading ---

    private void loadEvents() {
        // TODO: Replace with actual service/DAO call using filters and pagination
        // Example: eventService.find(filterStatus, filterDateFrom, filterDateTo, activePage, pageSize)
        if (events == null) {
            events = new ListModelList<>();
        }
        events.setMultiple(true);
        totalSize = 0; // set from service
    }

    // --- Computed properties ---

    public int getTotalPages() {
        return pageSize > 0 ? Math.max(1, (int) Math.ceil((double) totalSize / pageSize)) : 1;
    }

    // --- Getters and setters ---

    public String getFilterStatus() {
        return filterStatus;
    }

    public void setFilterStatus(String filterStatus) {
        this.filterStatus = filterStatus;
    }

    public Date getFilterDateFrom() {
        return filterDateFrom;
    }

    public void setFilterDateFrom(Date filterDateFrom) {
        this.filterDateFrom = filterDateFrom;
    }

    public Date getFilterDateTo() {
        return filterDateTo;
    }

    public void setFilterDateTo(Date filterDateTo) {
        this.filterDateTo = filterDateTo;
    }

    public ListModelList<EventItem> getEvents() {
        return events;
    }

    public Set<EventItem> getSelectedEvents() {
        return selectedEvents;
    }

    public void setSelectedEvents(Set<EventItem> selectedEvents) {
        this.selectedEvents = selectedEvents;
    }

    public int getActivePage() {
        return activePage;
    }

    public void setActivePage(int activePage) {
        this.activePage = activePage;
    }

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public int getTotalSize() {
        return totalSize;
    }

    public List<String> getStatusOptions() {
        return statusOptions;
    }

    // --- Inner model class (replace with your domain entity) ---

    public static class EventItem {
        private String eventId;
        private String type;
        private String status;
        private String context;
        private Date createdAt;
        private Date updatedAt;

        public EventItem() {}

        public EventItem(String eventId, String type, String status,
                         String context, Date createdAt, Date updatedAt) {
            this.eventId = eventId;
            this.type = type;
            this.status = status;
            this.context = context;
            this.createdAt = createdAt;
            this.updatedAt = updatedAt;
        }

        public String getEventId() { return eventId; }
        public void setEventId(String eventId) { this.eventId = eventId; }

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }

        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }

        public String getContext() { return context; }
        public void setContext(String context) { this.context = context; }

        public Date getCreatedAt() { return createdAt; }
        public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }

        public Date getUpdatedAt() { return updatedAt; }
        public void setUpdatedAt(Date updatedAt) { this.updatedAt = updatedAt; }
    }
}
