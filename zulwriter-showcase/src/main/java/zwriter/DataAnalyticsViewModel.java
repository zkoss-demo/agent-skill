package zwriter;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.zkoss.bind.annotation.Command;
import org.zkoss.chart.Color;
import org.zkoss.chart.Credits;
import org.zkoss.chart.Exporting;
import org.zkoss.chart.Legend;
import org.zkoss.chart.model.CategoryModel;
import org.zkoss.chart.model.DefaultCategoryModel;
import org.zkoss.chart.model.DefaultPieModel;
import org.zkoss.chart.model.PieModel;
import org.zkoss.chart.plotOptions.PlotOptions;
import org.zkoss.zul.Messagebox;

/**
 * ViewModel for {@code data-analytics-dashboard.zul}.
 *
 * <p>The three charts were here from the start, because a {@code <charts>} series has no literal
 * form in markup the way a {@code <row>} does. The extraction pass has since moved the rest in
 * beside them: the KPI cards and the heatmap cells repeat through {@code <forEach>}, and the
 * department table reads a bound {@code model} through a {@code <template name="model">}. Its
 * literal rows are gone from the markup -- setting a model discards them silently, so leaving them
 * would have kept rows on the page that display nothing.
 *
 * <p>Column captions, panel titles and the LOW/HIGH DENSITY scale stayed in the ZUL. They are
 * chrome: still correct tomorrow, against tomorrow's figures.
 */
public class DataAnalyticsViewModel {

    /** One headline figure in the top row of cards. */
    public static class Kpi {
        private final String label;
        private final String value;
        private final String icon;
        private final String tone;
        private final String delta;
        private final boolean rising;

        Kpi(String label, String value, String icon, String tone, String delta, boolean rising) {
            this.label = label;
            this.value = value;
            this.icon = icon;
            this.tone = tone;
            this.delta = delta;
            this.rising = rising;
        }

        public String getLabel() {
            return label;
        }

        public String getValue() {
            return value;
        }

        public String getTileSclass() {
            return "da-kpi-tile da-tile-" + tone + " " + icon;
        }

        public String getDelta() {
            return delta;
        }

        public String getDeltaSclass() {
            return rising ? "da-delta-up" : "da-delta-down";
        }

        public String getDeltaIconSclass() {
            return rising
                    ? "z-icon-arrow-up da-delta-icon-up"
                    : "z-icon-arrow-down da-delta-icon-down";
        }
    }

    /** One slice of the regional split, as the page's own legend reads it. */
    public static class RegionShare {
        private final String name;
        private final int percent;
        private final String tone;

        RegionShare(String name, int percent, String tone) {
            this.name = name;
            this.percent = percent;
            this.tone = tone;
        }

        public String getLabel() {
            return name + ": " + percent + "%";
        }

        public String getDotSclass() {
            return "da-legend-dot da-dot-" + tone;
        }
    }

    /** One square of the density heatmap. */
    public static class DensityCell {
        private final String department;
        private final int level;

        DensityCell(String department, int level) {
            this.department = department;
            this.level = level;
        }

        public String getSclass() {
            return "da-heatcell da-heat-" + level;
        }

        public String getTooltip() {
            return department + " -- density level " + level + " of 5";
        }
    }

    /** One row of the department performance table. */
    public static class Department {
        private final String name;
        private final String manager;
        private final String status;
        private final int score;

        Department(String name, String manager, String status, int score) {
            this.name = name;
            this.manager = manager;
            this.status = status;
            this.score = score;
        }

        public String getName() {
            return name;
        }

        public String getManager() {
            return manager;
        }

        public String getStatusLabel() {
            return status;
        }

        public String getStatusSclass() {
            return "On Hold".equals(status) ? "da-chip da-chip-hold" : "da-chip da-chip-active";
        }

        public int getScore() {
            return score;
        }

        public String getBarSclass() {
            return "On Hold".equals(status) ? "da-perfbar da-perfbar-hold" : "da-perfbar";
        }
    }

    private final List<Kpi> kpis = Arrays.asList(
            new Kpi("Total Revenue", "$425,000", "z-icon-money", "blue", "12.5%", true),
            new Kpi("Active Users", "12,450", "z-icon-users", "sky", "2.1%", false),
            new Kpi("Conversion Rate", "3.2%", "z-icon-mouse-pointer", "amber", "0.8%", true),
            new Kpi("Avg. Session", "4m 32s", "z-icon-clock-o", "violet", "5.4%", true));

    private final List<RegionShare> regionShares = Arrays.asList(
            new RegionShare("North", 70, "north"),
            new RegionShare("South", 30, "south"));

    private final List<Department> departments = Arrays.asList(
            new Department("Engineering", "Alex Rivera", "Active", 85),
            new Department("Marketing", "Sarah Chen", "On Hold", 45),
            new Department("Sales", "Michael Scott", "Active", 92));

    private final List<DensityCell> densityCells = buildDensityCells();

    /**
     * Twenty squares, five per row: one column per weekday, one row per department band. The levels
     * are what the ZUL turns into a tint class.
     */
    private static List<DensityCell> buildDensityCells() {
        String[] bands = {"Engineering", "Marketing", "Sales", "Support"};
        String[] days = {"Mon", "Tue", "Wed", "Thu", "Fri"};
        int[][] levels = {
                {2, 3, 1, 4, 3},
                {3, 5, 2, 1, 4},
                {2, 2, 1, 4, 1},
                {1, 3, 3, 2, 1}};
        List<DensityCell> cells = new ArrayList<>();
        for (int band = 0; band < bands.length; band++) {
            for (int day = 0; day < days.length; day++) {
                cells.add(new DensityCell(bands[band] + " / " + days[day], levels[band][day]));
            }
        }
        return cells;
    }

    public List<Kpi> getKpis() {
        return kpis;
    }

    public List<RegionShare> getRegionShares() {
        return regionShares;
    }

    public List<DensityCell> getDensityCells() {
        return densityCells;
    }

    public List<Department> getDepartments() {
        return departments;
    }

    public String getTotalShareLabel() {
        return "100%";
    }

    public String getUserName() {
        return "Alex Rivera";
    }

    public String getUserRole() {
        return "Admin";
    }

    public String getSelectedPeriod() {
        return "Last 30 Days";
    }

    public String getSelectedRegion() {
        return "Global Region";
    }

    public String getSelectedDepartment() {
        return "All Departments";
    }

    private final CategoryModel revenueModel = buildRevenueModel();
    private final PieModel regionModel = buildRegionModel();

    private static CategoryModel buildRevenueModel() {
        DefaultCategoryModel model = new DefaultCategoryModel();
        String[] months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov"};
        int[] revenue = {96, 104, 168, 214, 208, 226, 268, 292, 281, 296, 244};
        for (int i = 0; i < months.length; i++) {
            model.setValue("Revenue", months[i], revenue[i]);
        }
        return model;
    }

    private static PieModel buildRegionModel() {
        DefaultPieModel model = new DefaultPieModel();
        model.setValue("North", 70);
        model.setValue("South", 30);
        return model;
    }

    public CategoryModel getRevenueModel() {
        return revenueModel;
    }

    public PieModel getRegionModel() {
        return regionModel;
    }

    /**
     * Turns the pie into the mockup's ring: a hollow centre, no slice labels (the page draws its own
     * legend below), and no slice borders. {@code <charts>} exposes {@code plotOptions} as a
     * bindable attribute, so this is all reachable without the ViewModel touching a component.
     */
    public PlotOptions getDonutPlotOptions() {
        PlotOptions options = new PlotOptions();
        options.getPie().setInnerSize("72%");
        options.getPie().setBorderWidth(0);
        options.getPie().getDataLabels().setEnabled(false);
        return options;
    }

    public Legend getNoLegend() {
        Legend legend = new Legend();
        legend.setEnabled(false);
        return legend;
    }

    public Credits getNoCredits() {
        Credits credits = new Credits();
        credits.setEnabled(false);
        return credits;
    }

    public Exporting getNoExporting() {
        Exporting exporting = new Exporting();
        exporting.setEnabled(false);
        return exporting;
    }

    public List<Color> getBlueSeries() {
        return Arrays.asList(new Color("#2563eb"));
    }

    public List<Color> getRegionSeries() {
        return Arrays.asList(new Color("#2563eb"), new Color("#f5b912"));
    }

    /** Invoked by the "Apply Filters" button in the filter bar. */
    @Command
    public void applyFilters() {
        Messagebox.show("Re-run the dashboard against the selected filters here.",
                "Apply Filters", Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Invoked by the refresh icon beside "Apply Filters". */
    @Command
    public void refresh() {
        Messagebox.show("Reload the current figures here.", "Refresh",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Invoked by the pencil on each department row. */
    @Command
    public void editDepartment() {
        Messagebox.show("Open the department's performance targets here.", "Edit Department",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Invoked by the floating action button. */
    @Command
    public void newReport() {
        Messagebox.show("Start a new report here.", "New Report",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
