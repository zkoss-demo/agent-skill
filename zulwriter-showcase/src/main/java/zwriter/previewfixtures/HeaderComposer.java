package zwriter.previewfixtures;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.Executions;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.Label;

/**
 * Positive fixture for P2-8: a real Composer that reads a request header in
 * {@code doAfterCompose} and paints it. Rendered with {@code --run-controllers}, the launcher must
 * report {@code CONTROLLERS: executed} -- reading a header is now an ordinary success, where before
 * P2-8 the mock request held no headers at all and this returned {@code null}.
 *
 * <p>It lives here, and not in the launcher's own test sourceSet, because that sourceSet has no ZK
 * compile dependency (by design -- see {@code CoreIndependenceTest}) and {@code UiFactory.newComposer}
 * returns {@code org.zkoss.zk.ui.util.Composer}, so a Composer cannot be compiled there at all. The
 * launcher-side unit mirror of this case therefore uses a {@code <zscript>}, which needs no ZK type.
 *
 * <p>Not part of any corpus: {@code test/run-regression.py} globs {@code *.zul} non-recursively in
 * {@code src/main/webapp}, so the matching page sits in {@code webapp/preview-fixtures/}.
 */
public class HeaderComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    @Wire
    private Label filledByComposer;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        String ua = Executions.getCurrent().getHeader("user-agent");
        filledByComposer.setValue("composer saw UA=[" + ua + "]");
    }
}
