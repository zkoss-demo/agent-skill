package zwriter.previewfixtures;

import java.util.Arrays;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zul.ListModelList;
import org.zkoss.zul.Listbox;

/**
 * Composer for {@code preview-fixtures/literal-rows-setmodel.zul}.
 *
 * <p>The MVC half of the {@code literal-rows-discarded} rule: {@code setModel()} lives here, in
 * Java, where no ZUL-only check can see it. The listbox it wires still has its first-pass literal
 * rows in the markup, and setting a model discards them silently — which is the whole reason the
 * rule has to compare the markup against the rendered page.
 */
public class SetModelComposer extends SelectorComposer<Component> {

    @Wire
    private Listbox modelList;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        modelList.setModel(new ListModelList<>(
                Arrays.asList("MODEL-ROW-ONE", "MODEL-ROW-TWO", "MODEL-ROW-THREE")));
    }
}
