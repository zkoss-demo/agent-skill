package zwriter.previewfixtures;

/**
 * Supplies the include path for {@code preview-fixtures/include-bound-src.zul}.
 *
 * <p>A plain POJO on purpose: a ViewModel needs no ZK annotation to expose a getter, so this adds
 * no dependency. Isolated, it is never instantiated at all -- which is the point of the fixture,
 * because that is what leaves the include's {@code src} unset and produces the silent gap. With
 * {@code --run-controllers} it runs and the same page includes the fragment for real.
 */
public class IncludeViewModel {

    public String getPage() {
        return "/preview-fixtures/include-fragment.zul";
    }
}
