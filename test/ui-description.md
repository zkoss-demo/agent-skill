this document contains various UI requirements, used to test agent skill "zul-writer"

## Simple UI Patterns

*   **Personal Profile Info**: A page displaying read-only user information with labels (e.g., Tax ID, Full Name, Parent's Name) and values. Includes a primary confirmation button at the bottom right.
*   **General Login Page**: A centered login box with a logo, a decorative landscape image, and input fields for organization, username, and password. Includes "Forgot Password" and "Login" buttons.

## Complicated UI Patterns

*   **Application Dashboard & Activity Feed**: A layout with a header. Main content area contains status summary boxes (Application Status, ID, Date, Amount) and a separate section for recent messages/notifications in a list format.
*   **Finalized Application Review**: A page with a large, colored status header displaying a reference number. Below is a detailed summary of personal and application data in a grid/table format, followed by several action buttons (e.g., Print, Return to Home).
*   **Spreadsheet Editor Interface**: A complex UI mimicking a spreadsheet application. Includes a toolbar with various editing tools (undo, redo, font styles, alignment, cell formatting), a formula bar, and a large grid with row (numeric) and column (alphabetic) headers.
*   **Data Comparison Modal**: A popup window with a side-by-side comparison of two data records. Each side is a table listing multiple fields (Reference ID, Status, Timestamps, User-related fields) to highlight differences between revisions.
*   **Multi-level Navigation Dashboard**: A complex layout featuring a collapsible sidebar menu with hierarchical "tree-like" navigation. The main area displays recent tasks in a grid with filters and sorting options.
*   **Admin Search & Management Grid**: A comprehensive management page with a search filter bar at the top (Status, Date range). Below is a large data grid with checkboxes for bulk actions, numerous columns (Event ID, Type, Status, Context, Timestamps), and pagination controls at the bottom.
*   **Financial Document Processing**: A header-based form for document details. Includes a tabbed interface (Tabbox) with different sections (e.g., Disbursement, Posting Details). Inside a tab is a data grid for line items. Bottom section contains action radio buttons and save/submit buttons.
*   **Bank Reconciliation System**: A dense, tabular interface for financial reconciliation. Features a multi-row header, a toolbar with action buttons, a set of tabs for different reconciliation types, and a large data grid with many columns for transaction details.
*   **Test Case/Step Management System**: A specialized UI for managing test steps. Features a file-explorer style sidebar, a central grid of test steps with action icons, and a right-side configuration panel for the selected step.
*   **Enterprise Resource Kanban Board**: A dashboard featuring a "Kanban" or "Task Board" style layout. Multiple columns represent different statuses (e.g., Pending, Processing, Waiting). Each column contains cards with detailed task information, icons, and timestamps.
