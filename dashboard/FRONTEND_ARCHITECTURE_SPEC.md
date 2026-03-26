# FRONTEND ARCHITECTURE SPECIFICATION
## BugleRock CNS - Executive Command Center

### 1. Overview
The frontend serves as the unified, single-pane-of-glass dashboard for the BugleRock CNS system. It provides partners and institutional users with high-level pipeline observability, AI agent triaging metrics, and immediate escalation interventions.

### 2. Technology Stack
- **Framework**: React 18+ (Functional Components, Hooks)
- **Tooling**: Vite (for rapid dev server and optimized production build)
- **Styling**: Tailwind CSS (with highly customized Material Design-inspired color system)
- **Icons**: Google Material Symbols Outlined

### 3. Component Hierarchy
- `App` (App Entry Point)
  - `ExecutiveDashboard` (Main Layout Wrapper & State Manager)
    - `SideNavBar` (Static navigation & system health)
    - `TopNavBar` (Search, contextual actions, user profile)
    - `MainContent` (Dynamic content based on state)
      - `OverviewView` (Default View)
        - `KPI Metrics Row`
        - `Departmental Pipeline Heatmap` (Interactable Table)
        - `AI Escalation Desk` (Risk alert list)
      - `DepartmentDetailView` (Drill-down View - Rendered conditionally when a department is selected)

### 4. State Management
- **Local Layout State**: `useState` inside `ExecutiveDashboard` (`selectedDept`) dictates what is rendered in the `MainContent` area.
- clicking a row in the Pipeline Heatmap sets `selectedDept`, which hides the Dashboard Overview and reveals the `DepartmentDetailView` tailored to that specific entity.
- *Future Iterations* may utilize Context API or Zustand to manage deeper nesting as modular complexity scales over time.

### 5. Styling & Theming
- The design system implements an "Institutional Grade" color scheme mimicking Material 3 tokenized variables.
- Colors mapped in `tailwind.config.js` enable streamlined semantic classes rather than bespoke custom HEX definitions (e.g., `bg-surface-container-lowest`, `text-on-surface`, `border-outline-variant`).
- Dark Mode is natively accounted for through structured conditional variables combined with Tailwind's `dark:` pseudo-classes.
