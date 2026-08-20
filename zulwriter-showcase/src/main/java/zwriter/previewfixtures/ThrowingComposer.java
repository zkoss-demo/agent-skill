package zwriter.previewfixtures;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;

/**
 * Negative fixture for the preview launcher's fail-soft controller mode (P0-2, AC-3): a real
 * Composer whose {@code doAfterCompose} throws. Rendered with {@code --run-controllers}, the
 * launcher must degrade to an isolated render, report {@code CONTROLLERS: failed -> isolated},
 * name this failure in {@code WARNINGS} and still deliver the screenshot with exit 0.
 *
 * <p>It lives here, and not in the launcher's own test sourceSet, because that sourceSet has no ZK
 * compile dependency (by design -- see {@code CoreIndependenceTest}) and {@code UiFactory.newComposer}
 * returns {@code org.zkoss.zk.ui.util.Composer}, so a Composer cannot be compiled there at all. The
 * launcher-side unit mirrors of these cases therefore use ViewModels, which need no ZK type.
 *
 * <p>Not part of any corpus: {@code test/run-regression.py} globs {@code *.zul} non-recursively in
 * {@code src/main/webapp}, so the matching pages sit in {@code webapp/preview-fixtures/}.
 */
public class ThrowingComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        throw new IllegalStateException("preview fixture: this composer always fails");
    }
}
