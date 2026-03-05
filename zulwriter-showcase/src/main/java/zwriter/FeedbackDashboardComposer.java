package zwriter;

import org.zkoss.chart.Charts;
import org.zkoss.chart.Legend;
import org.zkoss.chart.Series;
import org.zkoss.chart.Title;
import org.zkoss.chart.XAxis;
import org.zkoss.chart.YAxis;
import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Progressmeter;

/**
 * MVC Composer for the Monthly Feedback Dashboard page.
 * Wires the progress meter and initialises both ZK Charts components.
 * Replace sample data with real service/repository calls.
 */
public class FeedbackDashboardComposer extends SelectorComposer<Component> {

    private static final String[] MONTHS = {"Jan", "Feb", "Mar", "Apr", "May", "Jun"};

    @Wire
    private Progressmeter submissionProgress;

    @Wire
    private Charts satisfactionChart;

    @Wire
    private Charts themesChart;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        loadProgressStatus();
        initSatisfactionChart();
        initThemesChart();
    }

    /**
     * Loads the current submission progress percentage.
     * Replace with real data from your service layer.
     */
    private void loadProgressStatus() {
        submissionProgress.setValue(60);
    }

    /**
     * Configures the bar chart showing monthly satisfaction scores (out of 5).
     */
    private void initSatisfactionChart() {
        satisfactionChart.setColors(new String[]{"#2d6be4"});

        XAxis xAxis = satisfactionChart.getXAxis();
        xAxis.setCategories(MONTHS);

        YAxis yAxis = satisfactionChart.getYAxis();
        yAxis.setMin(0);
        yAxis.setMax(5);

        // Sample monthly satisfaction scores — replace with real data
        Series series = new Series();
        series.setName("Satisfaction Score");
        series.setData(3.8, 4.1, 3.9, 3.7, 4.0, 4.2);
        satisfactionChart.addSeries(series);
    }

    /**
     * Configures the spline chart showing the number of feedback themes per month.
     */
    private void initThemesChart() {
        themesChart.setColors(new String[]{"#9b59b6"});

        XAxis xAxis = themesChart.getXAxis();
        xAxis.setCategories(MONTHS);

        YAxis yAxis = themesChart.getYAxis();
        yAxis.setMin(0);

        // Sample monthly theme counts — replace with real data
        Series series = new Series();
        series.setName("Themes");
        series.setData(2.1, 2.8, 2.3, 3.1, 2.7, 3.5);
        themesChart.addSeries(series);
    }

    /**
     * Handles the "Submit Feedback" button click.
     * Navigate to your feedback form or open a modal dialog here.
     */
    @Listen("onClick = #submitFeedbackBtn")
    public void onSubmitFeedback() {
        // TODO: e.g. Executions.sendRedirect("/submit-feedback.zul");
        //       or   Executions.createComponents("/feedback-form.zul", ..., null);
    }
}
