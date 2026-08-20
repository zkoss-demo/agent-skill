package zwriter.previewfixtures;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;

/**
 * Negative fixture for the preview launcher's controller budget (P0-2, AC-4): a real Composer that
 * sleeps far past any sane {@code --controller-timeout}. The launcher must abandon it at the budget,
 * retry isolated, and still deliver the screenshot with exit 0.
 *
 * <p>Sibling of {@link ThrowingComposer}; see its javadoc for why these live here rather than in
 * the launcher's own test sourceSet. Sleeping (rather than busy-looping) so the launcher's
 * interrupt lands and the abandoned thread actually ends.
 */
public class SleepingComposer extends SelectorComposer<Component> {

    private static final long serialVersionUID = 1L;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        try {
            Thread.sleep(60_000L);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
