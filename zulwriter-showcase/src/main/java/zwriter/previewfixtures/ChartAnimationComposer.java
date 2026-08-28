package zwriter.previewfixtures;

import org.zkoss.chart.Charts;
import org.zkoss.chart.Series;
import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Wire;

/**
 * D2 regression fixture: a zkcharts area chart left on its DEFAULT entry animation.
 *
 * <p>Highcharts animates a line/area series in by widening an SVG clip rect over ~1000ms, driven by
 * requestAnimationFrame -- not by a CSS animation or transition. Playwright's
 * {@code animations="disabled"} screenshot option therefore does nothing to it, and a capture taken
 * as soon as ZK has mounted lands mid-flight: the curve stops at some arbitrary month. The point of
 * this fixture is that NOTHING here asks for the defect. The page is what an author would naturally
 * write, and the preview pipeline is what has to make it reproducible.
 *
 * <p>Deliberately no {@code setAnimation(false)} anywhere: the moment this composer disables the
 * animation itself, it stops testing the pipeline and starts testing Highcharts.
 *
 * <p>Twelve points and a visible line width so that a partial render is unmistakable, and fixed
 * pixel sizes on the chart so the geometry does not depend on the viewport.
 */
public class ChartAnimationComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    @Wire
    private Charts revenueChart;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        Series series = revenueChart.getSeries();
        series.setName("Revenue");
        series.setData(41, 58, 47, 72, 66, 91, 84, 103, 96, 118, 109, 134);
    }
}
