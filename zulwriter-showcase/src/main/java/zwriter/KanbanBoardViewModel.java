package zwriter;

import org.zkoss.bind.annotation.Command;
import org.zkoss.zul.Messagebox;

/**
 * ViewModel for {@code kanban-board.zul}.
 *
 * <p>The board's task data is still literal markup in the ZUL, so this class holds only the page's
 * behaviour: the two commands its buttons invoke. Moving the cards into getters here is the
 * extraction pass, and it belongs after the layout has been settled against the literal render.
 */
public class KanbanBoardViewModel {

    /** Invoked by the "New Task" button in the top bar. */
    @Command
    public void newTask() {
        Messagebox.show("Open the new-task form here.", "New Task",
                Messagebox.OK, Messagebox.INFORMATION);
    }

    /** Invoked by the dashed placeholder at the foot of the PENDING column. */
    @Command
    public void addTask() {
        Messagebox.show("Add a task to PENDING here.", "Add Task",
                Messagebox.OK, Messagebox.INFORMATION);
    }
}
