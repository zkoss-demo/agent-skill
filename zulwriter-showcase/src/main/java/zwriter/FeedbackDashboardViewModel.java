package zwriter;

import java.util.Arrays;
import java.util.List;

import org.zkoss.bind.annotation.Command;
import org.zkoss.chart.Color;
import org.zkoss.chart.Credits;
import org.zkoss.chart.Exporting;
import org.zkoss.chart.Legend;
import org.zkoss.chart.model.CategoryModel;
import org.zkoss.chart.model.DefaultCategoryModel;
import org.zkoss.zul.Messagebox;

/**
 * ViewModel for {@code feedback-dashboard.zul}.
 *
 * <p>The two charts were here from the start, because a {@code <charts>} series has no literal form
 * in markup the way a {@code <row>} does — there is nothing to write into the ZUL and later
 * extract. The extraction pass has since moved the rest of the page's figures in beside them: the
 * submission progress, the current period, and the two summary headline numbers.
 *
 * <p>Section titles, the "/5" scale and the "Last 6 Months" window stayed in the ZUL. They are
 * chrome — still correct next month, against next month's numbers.
 *
 * <p>The chart chrome getters exist because ZK Charts takes {@code Legend}, {@code Credits} and
 * {@code Exporting} objects, not strings: {@code legend="false"} in the ZUL throws
 * {@code ClassCastException}. Supplying them from here keeps the page pure MVVM.
 */
public class FeedbackDashboardViewModel {

    private final CategoryModel satisfactionModel = buildSatisfactionModel();
    private final CategoryModel themesModel = buildThemesModel();

    private static CategoryModel buildSatisfactionModel() {
        DefaultCategoryModel model = new DefaultCategoryModel();
        model.setValue("Satisfaction", "Jan", 4.0);
        model.setValue("Satisfaction", "Feb", 4.6);
        model.setValue("Satisfaction", "Mar", 4.1);
        model.setValue("Satisfaction", "Apr", 3.4);
        model.setValue("Satisfaction", "May", 4.5);
        model.setValue("Satisfaction", "Jun", 4.3);
        return model;
    }

    private static CategoryModel buildThemesModel() {
        DefaultCategoryModel model = new DefaultCategoryModel();
        model.setValue("Themes raised", "Jan", 5);
        model.setValue("Themes raised", "Feb", 3);
        model.setValue("Themes raised", "Mar", 4);
        model.setValue("Themes raised", "Apr", 1);
        model.setValue("Themes raised", "May", 6);
        model.setValue("Themes raised", "Jun", 3);
        return model;
    }

    public CategoryModel getSatisfactionModel() {
        return satisfactionModel;
    }

    public CategoryModel getThemesModel() {
        return themesModel;
    }

    public int getProgressPercent() {
        return 60;
    }

    public String getProgressLabel() {
        return getProgressPercent() + "% Complete";
    }

    public String getCurrentPeriod() {
        return "October 2023";
    }

    public String getSatisfactionScore() {
        return "4.2";
    }

    public String getSatisfactionDelta() {
        return "+5%";
    }

    public String getThemeCount() {
        return "3 themes";
    }

    public String getThemesDelta() {
        return "+10%";
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
        return Arrays.asList(new Color("#3b82f6"));
    }

    public List<Color> getPurpleSeries() {
        return Arrays.asList(new Color("#a855f7"));
    }

    /** Invoked by the "Submit Feedback" button on the current-month card. */
    @Command
    public void submitFeedback() {
        Messagebox.show("Open this month's feedback form here.", "Submit Feedback",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
