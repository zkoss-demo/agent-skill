package zwriter;

import org.zkoss.chart.Charts;
import org.zkoss.chart.Series;
import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.*;

import java.util.Arrays;
import java.util.List;

/**
 * Composer for data-analytics-dashboard.zul
 *
 * Scaffold — replace sample data and TODO comments with real service/repository calls.
 */
public class DataAnalyticsDashboardComposer extends SelectorComposer<Component> {

    // --- Wired components ---

    @Wire private Combobox periodFilter;
    @Wire private Combobox regionFilter;
    @Wire private Combobox deptFilter;

    @Wire private Button applyFiltersBtn;
    @Wire private Button refreshBtn;
    @Wire private Button addBtn;

    @Wire private Label totalRevenueLbl;
    @Wire private Label activeUsersLbl;
    @Wire private Label conversionRateLbl;
    @Wire private Label avgSessionLbl;

    @Wire private Charts revenueChart;
    @Wire private Charts regionalChart;

    @Wire private Listbox deptListbox;

    // --- Lifecycle ---

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        initFilters();
        loadKpiCards();
        loadRevenueChart();
        loadRegionalChart();
        loadDepartmentTable();
    }

    // --- Initialization helpers ---

    private void initFilters() {
        // Period filter
        for (String period : Arrays.asList("Last 7 Days", "Last 30 Days", "Last Quarter", "This Year")) {
            periodFilter.appendItem(period);
        }
        periodFilter.setValue("Last 30 Days");

        // Region filter
        for (String region : Arrays.asList("Global Region", "North", "South", "East", "West")) {
            regionFilter.appendItem(region);
        }
        regionFilter.setValue("Global Region");

        // Department filter
        for (String dept : Arrays.asList("All Departments", "Engineering", "Sales", "Marketing", "Operations", "Finance")) {
            deptFilter.appendItem(dept);
        }
        deptFilter.setValue("All Departments");
    }

    private void loadKpiCards() {
        // TODO: replace with real aggregated metrics from your analytics service
        totalRevenueLbl.setValue("$425,000");
        activeUsersLbl.setValue("12,450");
        conversionRateLbl.setValue("3.2%");
        avgSessionLbl.setValue("4m 32s");
    }

    private void loadRevenueChart() {
        // Area chart — monthly revenue over 12 months
        // TODO: replace with real time-series data from your reporting service
        Series series = revenueChart.getSeries();
        series.setName("Revenue");

        Number[] revenueData = {28000, 31500, 27000, 34200, 38000, 41500,
                                39800, 44000, 47500, 43200, 51000, 56800};
        series.setData(revenueData);

        revenueChart.getXAxis().setCategories(
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        );
        revenueChart.getYAxis().setTitle("Revenue (USD)");
    }

    private void loadRegionalChart() {
        // Donut chart — two-region breakdown matching the screenshot
        // TODO: replace with real regional data from your analytics service
        regionalChart.getPlotOptions().getPie().setInnerSize("60%");
        regionalChart.getTitle().setText("100%");
        regionalChart.getTitle().setStyle("fontSize:18px;fontWeight:700;color:#111827;");

        Series series = regionalChart.getSeries();
        series.addPoint("North", 70);
        series.addPoint("South", 30);

        // Hide the built-in legend (we render it in ZUL)
        regionalChart.getLegend().setEnabled(false);
    }

    private void loadDepartmentTable() {
        // TODO: replace with real department performance data from your service
        List<DepartmentRow> rows = Arrays.asList(
            new DepartmentRow("Engineering", "Alex Rivera",  "Active",  85),
            new DepartmentRow("Marketing",   "Sarah Chen",   "On Hold", 45),
            new DepartmentRow("Sales",       "Michael Scott","Active",  92)
        );

        ListModelList<DepartmentRow> model = new ListModelList<>(rows);
        deptListbox.setModel(model);
        deptListbox.setItemRenderer((Listitem item, Object data, int index) -> {
            DepartmentRow row = (DepartmentRow) data;

            new Listcell(row.getDepartment()).setParent(item);
            new Listcell(row.getManager()).setParent(item);

            // Status badge cell
            Listcell statusCell = new Listcell();
            Label statusLbl = new Label(row.getStatus());
            String badgeSclass = "status-badge " +
                ("Active".equals(row.getStatus()) ? "status-active" : "status-onhold");
            statusLbl.setSclass(badgeSclass);
            statusCell.appendChild(statusLbl);
            statusCell.setParent(item);

            // Performance bar cell — blue for Active, amber for On Hold
            Listcell perfCell = new Listcell();
            Hlayout perfRow = new Hlayout();
            perfRow.setSclass("perf-row");

            String barColor = "Active".equals(row.getStatus()) ? "perf-bar-blue" : "perf-bar-orange";

            org.zkoss.zk.ui.HtmlNativeComponent track =
                new org.zkoss.zk.ui.HtmlNativeComponent("div", null, null);
            track.setDynamicProperty("class", "perf-bar-track");

            org.zkoss.zk.ui.HtmlNativeComponent fill =
                new org.zkoss.zk.ui.HtmlNativeComponent("div", null, null);
            fill.setDynamicProperty("class", "perf-bar-fill " + barColor);
            fill.setDynamicProperty("style", "width:" + row.getPerformance() + "%;");
            track.appendChild(fill);

            Label perfNum = new Label(String.valueOf(row.getPerformance()));
            perfNum.setSclass("perf-num");

            perfRow.appendChild(track);
            perfRow.appendChild(perfNum);
            perfCell.appendChild(perfRow);
            perfCell.setParent(item);

            // Actions cell
            Listcell actionsCell = new Listcell();
            Button editBtn = new Button();
            editBtn.setIconSclass("z-icon-pencil");
            editBtn.addEventListener("onClick", e -> {
                // TODO: open edit dialog for row.getDepartment()
                Messagebox.show("Edit: " + row.getDepartment());
            });
            actionsCell.appendChild(editBtn);
            actionsCell.setParent(item);
        });
    }

    // --- Event handlers ---

    @Listen("onClick = #applyFiltersBtn")
    public void onApplyFilters() {
        String period = periodFilter.getValue();
        String region = regionFilter.getValue();
        String dept   = deptFilter.getValue();
        // TODO: reload KPI cards, charts, and department table using selected filter values
        loadKpiCards();
        loadDepartmentTable();
    }

    @Listen("onClick = #refreshBtn")
    public void onRefresh() {
        // TODO: refresh all data from the server
        loadKpiCards();
        loadRevenueChart();
        loadRegionalChart();
        loadDepartmentTable();
    }

    @Listen("onClick = #addBtn")
    public void onAdd() {
        // TODO: open a dialog to add a new department or data entry
        Messagebox.show("Add New — implement your dialog here.");
    }

    // --- Inner model ---

    /**
     * Represents one row in the Department Performance table.
     * Refactor to a separate file when integrating real business logic.
     */
    public static class DepartmentRow {
        private final String department;
        private final String manager;
        private final String status;
        private final int    performance; // 0–100

        public DepartmentRow(String department, String manager, String status, int performance) {
            this.department  = department;
            this.manager     = manager;
            this.status      = status;
            this.performance = performance;
        }

        public String getDepartment()  { return department; }
        public String getManager()     { return manager; }
        public String getStatus()      { return status; }
        public int    getPerformance() { return performance; }
    }
}
