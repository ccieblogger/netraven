# UI/UX Design: Configuration Backup Module

This spec outlines a user-friendly interface in Vue 3.5.13 (headless-first) styled with your existing NetRaven theme and Tailwind CSS utility classes. It introduces a top-level **Backups** navigation parent, under which the Configuration Backup Viewer and any future backup-related pages live as children.

---

## 📂 Navigation Structure

```text
└── Backups
    ├── Configuration Snapshots   ← Current page
    ├── Backup Schedules           ← Future scheduled jobs management
    └── Audit Logs                 ← Future change history overview
```

* **Backups (Parent)**: in the main side-nav, labeled with a hard-drive icon; expands/collapses its children.
* **Configuration Snapshots**: when selected, highlights in the nav and loads the Config Backup Viewer.
* **Child Links**: styled using `<NavLink>` components (headless) with active/inactive states matching the NetRaven color pallet (e.g., `text-primary` for active, `text-secondary` for inactive).

---

## 🎨 Theming & Style Guidelines

1. **Color Palette**: use your existing Tailwind palette tokens (e.g., `bg-card`, `text-text-primary`, `btn-primary`).
2. **Headless Components**: leverage headless UI libraries (e.g., @headlessui/vue) for accessible dropdowns, modals, and tabs—styled via Tailwind to match the theme.
3. **Tailwind Config**: ensure Tailwind is configured with your custom NetRaven colors, typography, and border-radius scales so all components inherit consistent styling.
4. **Dark/Light Modes**: mirror your app’s global theme toggler; override Tailwind’s `dark:` variants on interactive elements.
5. **Responsive Breakpoints**: follow existing breakpoints (`sm`, `md`, `lg`), ensuring the timeline panel collapses into an accordion or slide-over on smaller viewports.

---

## 🗂 Main Pages & Components

### 1. Backups Parent Nav

* **Component**: `<SidebarGroup>` (headless) with props for label, icon, and child links array.
* **Behavior**: Click toggles its expanded state; active child automatically expands parent.

### 2. Configuration Snapshots Page

* **Search & Filter Bar** (persistent at top): InputText, DeviceDropdown (headless `<Listbox>`), DateRangePicker (headless `<Popover>`), and Search button.
* **Snapshots Table** (`<DataTable>`): columns for Device, Snapshot ID, Retrieved At, Snippet, Actions.
* **Actions**: Headless `<Menu>` for per-row actions: View, Diff, Download.

### 3. Timeline Slide-Over Panel

* **Component**: `<TransitionChild>` slide-over from right.
* **Content**: `<Timeline>` listing version bullets with timestamps and action buttons (icon-only `<Button>`s).

### 4. Diff Modal

* **Component**: `<Dialog>` from @headlessui/vue.
* **Selectors**: headless `<Listbox>` for version pickers.
* **Viewer**: `<pre>` wrapper with monospace font and line-number gutter; styled to highlight additions/deletions.

### 5. Raw Config Code View

* **Route**: `/backups/configurations/:device/:snapshotId`
* **Layout**: `<Split>` component into two panes; left: code block with copy button; right: optional diff view if `?diffWith` param present.

---

## 🔄 Interaction Flows & State

1. **Navigate**: User clicks **Backups** in sidebar → children appear; clicking **Configuration Snapshots** loads page.
2. **Search**: User sets filters → clicks Search → calls `/configs/search` → table data updates.
3. **View Timeline**: Click row’s **Actions > Timeline** → slide-over opens, fetches `/configs/{device}` snapshots.
4. **Generate Diff**: From timeline or table, open Diff modal, select two versions → on confirm, call `/configs/{d}/{v1}/diff/{v2}`.
5. **Download**: Click Download in menu → triggers file download via API streaming.

---

## ✅ Deployment Best Practices (May 2025)

* **Vue 3.5.13**: check the official docs for composition API improvements and headless-ui compatibility.
* **Bundling**: use Vite with the latest plugins for tree-shaking and faster dev reloads.
* **Accessibility (a11y)**: ensure headless components include proper ARIA roles—refer to May 2025 best-practice guides on vuejs.org and @headlessui/vue repo.
* **Testing**: write Jest + Vue Testing Library tests for component states (nav expansion, modal open/close).

> **Developer Note**: Search online (May 2025) for the latest guidance on deploying Vue 3.5 apps—especially around Vite production optimizations, CSS purging, and SSG/SSR options if applicable.

---

*This spec aligns with NetRaven’s existing style and headless-first philosophy, centralizing all backup-related features under a clear navigation hierarchy.*

---

# 🚀 Implementation Plan & GitHub Issues

Break the work into discrete, AI-assignable workstreams. Copy each section below as a separate GitHub Issue.

## Workstream 1: Sidebar Navigation & Routing

**Title:** Add Backups Parent Navigation and Child Routes

**Description:**
Implement the **Backups** parent in the existing sidebar, with child links for Configuration Snapshots, Backup Schedules, and Audit Logs. Set up Vue Router routes.

**Tasks:**

* Create a `<SidebarGroup>` component that accepts `label`, `icon`, and `children` props.
* Update main `Sidebar.vue` to import and render `<SidebarGroup>` for the Backups section.
* Define routes in `router/index.js`:

  ```js
  {
    path: '/backups',
    component: () => import('@/layouts/BackupsLayout.vue'),
    children: [
      { path: 'configurations', name: 'ConfigSnapshots', component: () => import('@/views/ConfigSnapshots.vue') },
      { path: 'schedules', name: 'BackupSchedules', component: () => import('@/views/BackupSchedules.vue') },
      { path: 'audit-logs', name: 'AuditLogs', component: () => import('@/views/AuditLogs.vue') },
    ]
  }
  ```
* Ensure active link highlighting uses `RouterLink` `exact-active` and Tailwind classes `text-primary` / `text-secondary`.

**Acceptance Criteria:**

* Sidebar shows Backups parent, which expands/collapses.
* Clicking a child navigates to corresponding route and view (views can be placeholders).

---

## Workstream 2: Config Snapshots Page Scaffold

**Title:** Scaffold Configuration Snapshots View & Components

**Description:**
Build the base **Configuration Snapshots** page: search/filter bar, snapshots table, and placeholder actions.

**Tasks:**

* Create `views/ConfigSnapshots.vue` with:

  * `<SearchBar />` component containing InputText, DeviceDropdown (`<Listbox>`), DateRangePicker (`<Popover>`), and Search button.
  * `<SnapshotsTable />` component wired to a mock dataset.
* Define `components/SearchBar.vue` and `components/SnapshotsTable.vue`:

  * Use headless `<Listbox>`, `<Popover>`, and Tailwind styling.
  * DataTable columns: Device, Snapshot ID, Retrieved At, Snippet, Actions.
* Integrate sample API call stub using Axios to `/configs/search` (mock URL).
* Write basic unit tests (Vue Testing Library) for SearchBar and SnapshotsTable rendering.

**Acceptance Criteria:**

* ConfigSnapshots view loads with search bar and table populating sample data.
* Filters and search button exist but can be stubbed.

---

## Workstream 3: Timeline Slide-Over Panel

**Title:** Implement Timeline Slide-Over Panel for Snapshots

**Description:**
Develop the slide-over panel that shows the version timeline for a selected device.

**Tasks:**

* Create `components/TimelinePanel.vue` using `<TransitionChild>` to slide in from the right.
* Fetch snapshot list from API endpoint `/configs/{device}` on open.
* Render a `<Timeline>` list of items with timestamp and action buttons (View, Diff).
* Ensure panel is responsive: collapses to full-screen on `sm` breakpoint.
* Add unit tests for panel open/close and data rendering.

**Acceptance Criteria:**

* Clicking Timeline action in table row opens the slide-over with a list of versions.
* Close button hides the panel.

---

## Workstream 4: Config Diff Page & Modal Implementation

**Title:** Implement Unified Config Diff Page and Modal

**Description:**
Create a **dedicated full-page Config Diff** view and a **modal variant** to support both consolidated (unified) and side-by-side diff comparisons. All behaviors are fully specified; no optional features.

**Access Patterns:**

* **Full-Page Diff:** Available via direct URL `/backups/configurations/:device/:snapshotA/diff/:snapshotB` and through an “Open Full Diff” button in the Snapshots Table and Timeline panel.
* **Modal Diff:** Launch via “Quick Diff” action in Snapshots Table row or Timeline panel; opens in a `<Dialog>` overlay without changing routes.

**Design Specifications:**

1. **Routing & Navigation**

   * Add Vue Router entry:

     ```js
     {
       path: '/backups/configurations/:device/:snapshotA/diff/:snapshotB',
       name: 'ConfigDiffPage',
       component: () => import('@/views/ConfigDiffPage.vue')
     }
     ```
   * Include a `<RouterLink>` button labeled “Open Full Diff” in each snapshot row’s action menu, linking to the above route.
   * In `TimelinePanel.vue`, include a `<Button>` labeled “Full Diff” next to each version entry, navigating to the diff page.

2. **Full-Page Diff View (`ConfigDiffPage.vue`)**

   * **Layout:**

     ```html
     <div class="p-6">
       <h1 class="text-2xl font-semibold mb-4">Config Diff: {{ device }}</h1>
       <Tab.Group>
         <Tab.List class="flex space-x-4 border-b">
           <Tab class="px-4 py-2">Unified</Tab>
           <Tab class="px-4 py-2">Side‑by‑Side</Tab>
         </Tab.List>
         <Tab.Panels class="mt-4">
           <Tab.Panel>
             <pre class="font-mono text-sm overflow-auto whitespace-pre-wrap"><code>{{ unifiedDiff }}</code></pre>
           </Tab.Panel>
           <Tab.Panel>
             <div class="grid grid-cols-2 gap-4">
               <CodeBlock :content="snapshotAData" />
               <CodeBlock :content="snapshotBData" />
             </div>
           </Tab.Panel>
         </Tab.Panels>
       </Tab.Group>
     </div>
     ```

   * **Unified Diff Rendering:**

     * Generate diff via `diff.createPatch(device, snapshotAData, snapshotBData)`.
     * Wrap each line in `<span>`; apply `bg-green-100` for lines starting with `+` and `bg-red-100` for `-`.
     * Prepend line numbers via a CSS grid gutter or inline counter.

   * **Side‑by‑Side Rendering:**

     * Compute `diff.diffLines(snapshotAData, snapshotBData)`.
     * Highlight added lines in the right pane with `bg-green-100`; removed lines in left pane with `bg-red-100`.

3. **Modal Variant (`ConfigDiffModal.vue`)**

   * **Structure:**

     ```html
     <Dialog as="div" class="fixed inset-0 z-50 flex items-center justify-center">
       <Dialog.Overlay class="fixed inset-0 bg-black opacity-30" />
       <div class="bg-card rounded-2xl shadow-lg max-w-4xl w-full p-6">
         <div class="flex justify-between items-center mb-4">
           <Dialog.Title class="text-xl font-semibold">Quick Config Diff</Dialog.Title>
           <Button icon="X" @click="close()" />
         </div>
         <Tab.Group>
           <Tab.List class="flex space-x-4 border-b">
             <Tab class="px-3 py-1">Unified</Tab>
             <Tab class="px-3 py-1">Side‑by‑Side</Tab>
           </Tab.List>
           <Tab.Panels class="mt-4">
             <Tab.Panel>
               <pre class="font-mono text-xs overflow-auto"><code>{{ unifiedDiff }}</code></pre>
             </Tab.Panel>
             <Tab.Panel>
               <div class="grid grid-cols-2 gap-2">
                 <CodeBlock :content="snapshotAData" class="h-64 overflow-auto" />
                 <CodeBlock :content="snapshotBData" class="h-64 overflow-auto" />
               </div>
             </Tab.Panel>
           </Tab.Panels>
         </Tab.Group>
       </div>
     </Dialog>
     ```
   * **Behavior:**

     * Modal opens with backdrop; width constrained to `max-w-4xl`.
     * Always available on the Snapshots Table and Timeline panel.
     * Closes on backdrop click or close button.

4. **Data & Methods**

   * In both page and modal, use:

     ```js
     onMounted(async () => {
       const [aRes, bRes] = await Promise.all([
         axios.get(`/configs/${device}/${snapshotA}`),
         axios.get(`/configs/${device}/${snapshotB}`)
       ]);
       snapshotAData.value = aRes.data.config;
       snapshotBData.value = bRes.data.config;
       unifiedDiff.value = diff.createPatch(device, snapshotAData.value, snapshotBData.value);
     });
     ```

5. **Responsive & Accessibility**

   * **Breakpoint `<sm`:** switch the side‑by‑side grid to `grid-cols-1`.
   * Use `<Dialog>` ARIA roles and ensure `<Tab>` has `aria-selected` attributes.
   * Ensure `<CodeBlock>` can scroll vertically with `overflow-auto`.

6. **Testing**

   * Write Jest tests for `diff.createPatch` and `diff.diffLines` integration in both components.
   * Cypress E2E: verify page load, mode toggle, and modal open/close.

**Acceptance Criteria:**

* Full-page diff page and modal render identical unified and side‑by‑side views.
* Actions “Open Full Diff” and “Quick Diff” both work consistently.
* No discretionary decisions remain; the design is fully specified.

---

## Workstream 5: Raw Config Viewer and Download---## Workstream 5: Raw Config Viewer and Download
**Title:** Implement Raw Config View and Download Functionality

**Description:**
Add the route and view to display raw configuration text and enable file download.

**Tasks:**

* Create `views/ConfigRawView.vue` at route `/backups/configurations/:device/:snapshotId`.
* On mount, fetch `/configs/{device}/{snapshotId}` and display in a `<CodeBlock>` with copy-to-clipboard button.
* If query param `diffWith` is present, fetch and show diff side-by-side using a `<Split>` layout.
* Implement Download button that GETs the raw config and triggers a browser download (use `response.blob()`).
* Add tests verifying fetch and display behaviors.

**Acceptance Criteria:**

* Visiting the raw view route shows the config text and allows copy/download.
* `?diffWith` toggles side-by-side diff view.

---

## Workstream 6: Integration & End-to-End Testing

**Title:** End-to-End Tests for Config Backup Module

**Description:**
Write E2E tests using Cypress (or preferred framework) covering primary user flows.

**Tasks:**

* Write E2E test for:

  1. Navigating to **Backups > Configuration Snapshots**.
  2. Performing a search and verifying table updates.
  3. Opening Timeline panel and checking snapshots list.
  4. Opening Diff modal and verifying diff content.
  5. Viewing raw config and downloading file.
* Mock API responses via fixtures to simulate backend.
* Ensure tests run in CI (update GitHub Actions workflow).

**Acceptance Criteria:**

* All E2E scenarios pass in CI with mock data.

---

*Copy each of these sections as separate GitHub issues to assign and track progress.*
