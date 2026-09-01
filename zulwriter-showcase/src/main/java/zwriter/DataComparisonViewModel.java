package zwriter;

import java.util.Arrays;
import java.util.List;

import org.zkoss.bind.annotation.Command;
import org.zkoss.zul.Messagebox;

/**
 * ViewModel for {@code data-comparison-modal.zul}.
 *
 * <p>Extraction pass: the six compared fields now live here and the grid reads them through a bound
 * {@code model} plus a {@code <template name="model">}. The literal {@code <row>} elements the
 * layout was judged against have been deleted — setting a model discards them silently, so leaving
 * them behind would have kept markup on the page that displays nothing.
 *
 * <p>The word "MODIFIED" stayed in the ZUL and the flag's visibility came here: the caption is
 * chrome, whether a given field earned it is data.
 */
public class DataComparisonViewModel {

    /** One field, before and after, plus the styling its state earns. */
    public static class FieldDiff {
        private final String fieldName;
        private final String originalValue;
        private final String originalTone;
        private final String revisedValue;
        private final boolean modified;
        private final String revisedTone;
        private final String revisedIcon;
        private final boolean avatarShown;

        FieldDiff(String fieldName, String originalValue, String originalTone,
                String revisedValue, boolean modified, String revisedTone, String revisedIcon,
                boolean avatarShown) {
            this.fieldName = fieldName;
            this.originalValue = originalValue;
            this.originalTone = originalTone;
            this.revisedValue = revisedValue;
            this.modified = modified;
            this.revisedTone = revisedTone;
            this.revisedIcon = revisedIcon;
            this.avatarShown = avatarShown;
        }

        public String getFieldName() {
            return fieldName;
        }

        public String getOriginalValue() {
            return originalValue;
        }

        public String getRevisedValue() {
            return revisedValue;
        }

        public boolean isModified() {
            return modified;
        }

        /**
         * How the superseded value reads: normally when nothing changed, struck through when it was
         * replaced outright, dimmed when it was merely superseded. Which of the three a field gets
         * is a judgement about that field, not something derivable from the new value -- so it is
         * carried as data rather than inferred here.
         */
        public String getOriginalSclass() {
            if ("gone".equals(originalTone)) {
                return "dc-old-gone";
            }
            return "muted".equals(originalTone) ? "dc-old-muted" : "dc-old";
        }

        public String getRevisedSclass() {
            if ("alert".equals(revisedTone)) {
                return "dc-new-alert";
            }
            return "changed".equals(revisedTone) ? "dc-new-changed" : "dc-new";
        }

        public String getRevisedIconSclass() {
            if (revisedIcon == null) {
                return "";
            }
            return "alert".equals(revisedTone)
                    ? revisedIcon + " dc-new-icon-alert"
                    : revisedIcon + " dc-new-icon";
        }

        public boolean isRevisedIconShown() {
            return revisedIcon != null;
        }

        public boolean isAvatarShown() {
            return avatarShown;
        }
    }

    private final List<FieldDiff> fieldDiffs = Arrays.asList(
            new FieldDiff("Reference ID", "REF-99201", "plain", "REF-99201", false,
                    "plain", null, false),
            new FieldDiff("Status", "Pending", "gone", "Approved", true,
                    "changed", "z-icon-check-circle", false),
            new FieldDiff("Modified Date", "2023-10-01 10:00", "muted", "2023-10-02 14:30", true,
                    "changed", null, false),
            new FieldDiff("Modified By", "j.doe@company.com", "muted", "a.smith@company.com", true,
                    "changed", null, true),
            new FieldDiff("Priority", "Medium", "muted", "High", true,
                    "alert", "z-icon-exclamation", false),
            new FieldDiff("Department", "Finance", "plain", "Finance", false,
                    "plain", null, false));

    public List<FieldDiff> getFieldDiffs() {
        return fieldDiffs;
    }

    public String getOriginalVersionLabel() {
        return "v1.2 (Original)";
    }

    public String getRevisedVersionLabel() {
        return "v1.3 (Revised)";
    }

    public String getOriginalColumnLabel() {
        return "ORIGINAL (V1.2)";
    }

    public String getRevisedColumnLabel() {
        return "REVISED (V1.3)";
    }

    /** Invoked by the header's X and by the "Done" button. */
    @Command
    public void close() {
        Messagebox.show("Close the comparison and return to the revision list here.",
                "Compare Revisions", Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Invoked by the "Download PDF" button in the footer. */
    @Command
    public void downloadPdf() {
        Messagebox.show("Render the comparison as a PDF here.", "Download PDF",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
