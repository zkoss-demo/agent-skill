package demo.layout.kanban;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.zkoss.bind.annotation.Init;

public class KanbanViewModel {

    private static final KanbanTag TAG_MARKETING = new KanbanTag("#EA113B", "Marketing");
    private static final KanbanTag TAG_MEETING = new KanbanTag("#177FE5", "Meeting");
    private static final KanbanTag TAG_PLANNING = new KanbanTag("#1DBF5E", "Planning");
    private static final KanbanTag TAG_NEW = new KanbanTag("#FFBB22", "New");
    private List<KanbanTask> todoTasks;
    private List<KanbanTask> activeTasks;
    private List<KanbanTask> completeTasks;

    @Init
    public void init() {
        todoTasks = new ArrayList<KanbanTask>();
        List<KanbanTag> tags1 = new ArrayList<KanbanTag>();
        tags1.add(TAG_NEW);
        tags1.add(TAG_MARKETING);
        todoTasks.add(new KanbanTask("Loading animation",
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                "/widgets/layout/kanban/img/img1.png", tags1));
        todoTasks.add(new KanbanTask("New Year banner",
                "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
                "/widgets/layout/kanban/img/img1.png"));
        List<KanbanTag> tags2 = new ArrayList<KanbanTag>();
        tags2.add(TAG_PLANNING);
        tags2.add(TAG_MEETING);
        todoTasks.add(new KanbanTask("Renew landing page",
                "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                "/widgets/layout/kanban/img/img2.png", tags2));
        activeTasks = new ArrayList<KanbanTask>();
        List<KanbanTag> tags3 = new ArrayList<KanbanTag>();
        tags3.add(TAG_PLANNING);
        activeTasks.add(new KanbanTask("Layout images",
                "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis sollicitudin mauris.",
                "/widgets/layout/kanban/img/img3.png", tags3));
        completeTasks = new ArrayList<KanbanTask>();
        List<KanbanTag> tags4 = new ArrayList<KanbanTag>();
        tags4.add(TAG_PLANNING);
        tags4.add(TAG_MEETING);
        tags4.add(TAG_MARKETING);
        completeTasks.add(new KanbanTask("Advertising poster",
                "Integer in mauris eu nibh euismod gravida. Duis ac tellus et risus vulputate vehicula. Donec lobortis risus a elit.",
                "/widgets/layout/kanban/img/img1.png", tags4));
        List<KanbanTag> tags5 = new ArrayList<KanbanTag>();
        tags5.add(TAG_NEW);
        completeTasks.add(new KanbanTask("Interview document",
                "Etiam tempor. Ut ullamcorper, ligula eu tempor congue, eros est euismod turpis, id tincidunt sapien risus a quam. Maecenas fermentum consequat mi.",
                "/widgets/layout/kanban/img/img3.png", tags5));
    }

    public List<KanbanTask> getTodoTasks() {
        return todoTasks;
    }

    public List<KanbanTask> getActiveTasks() {
        return activeTasks;
    }

    public List<KanbanTask> getCompleteTasks() {
        return completeTasks;
    }

}