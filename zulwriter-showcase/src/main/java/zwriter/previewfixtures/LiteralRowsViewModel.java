package zwriter.previewfixtures;

import java.util.Arrays;
import java.util.List;

/**
 * ViewModel for {@code preview-fixtures/literal-rows-discarded.zul}.
 *
 * <p>Supplies rows whose text shares nothing with the literal rows the fixture leaves in the
 * markup, so a test can tell which set reached the page.
 */
public class LiteralRowsViewModel {

    public List<String> getItems() {
        return Arrays.asList("MODEL-ROW-ONE", "MODEL-ROW-TWO", "MODEL-ROW-THREE");
    }
}
