# GARUDA v0.5 — S2 UI Stabilization Report

Scope: UI/UX Stabilization and Navigation Repair. All work is frontend-only; the backend
(`rules_engine` and API) was not modified.

## Summary

Every page in the application now renders real backend data with explicit loading, error, and
empty states. Navigation is repaired and consistent across routes. No dummy data was added;
missing data renders empty states. All crash-prone UI patterns (unsafe `JSON.parse`, NaN dates,
unhandled mutations) were removed.

## What changed

### Infrastructure (new)

- `src/components/ui/` — Button, Card, Badge, LoadingState, ErrorState, EmptyState,
  ConfirmDialog, PageHeader, Breadcrumbs.
- `src/components/ToastContainer.tsx` + `src/store/useToastStore.ts` — global toasts.
- `src/components/ErrorBoundary.tsx` — crash boundary with Try Again / Reload.
- `src/utils/errorMessage.ts` — axios-aware error messages.
- `src/utils/json.ts` — crash-proof `parseTagArray` / `parseJsonField`.
- `src/main.tsx` — mounted ErrorBoundary + ToastContainer; tuned QueryClient defaults.

### Navigation repair

- `Sidebar` — added Missions (route existed but was unreachable from nav).
- `TopNav` — dynamic page titles for all routes incl. project pages; real health indicator
  (was hardcoded "System Online"); project id shown in header.
- `Breadcrumbs` added to DatasetManager, AssetLibrary, PipelineManager, MissionManager.
- `PipelineManager` / `MissionManager` — removed duplicated detail views (they rendered both in
  the sidebar and main content); pipeline/mission stores now seeded with `projectId`.
- `DatasetManager` / `AssetLibrary` — guard against missing `projectId` with EmptyState.

### Pages

- `ProjectDashboard` — effect now opens each project once; NaN-safe dates; safe tag parsing;
  loading placeholders for dataset/AOI/pipeline/asset stats.
- `QueryBuilderPage` — fixed `page_size` pagination bug; save-query error feedback + required
  project id.
- `RuleManager` — full rewrite: toasts, error/retry, confirm-delete, config-driven selects.
- `AlertDashboard` — full rewrite: fixed status actions to send valid backend statuses
  (`acknowledged`, `dismissed`, `in_review`, `resolved`, `archived`), toasts, error/retry,
  stats grid.
- `Settings` — replaced fake config sections with real health + EmptyState.
- `About` — version/environment from health endpoint (was hardcoded).
- `Dashboard` — loading/error states for stats and recent projects; NaN-safe dates.
- `CreateProjectModal` — form resets on open; Escape closes; consolidated form state.

### Components

- Crash fixes: `JSON.parse` on tags in `DatasetList`, `AssetDetails`, `MissionDetails` →
  `parseTagArray`; `Object.keys(stats.by_type)` guarded in `AssetStats` / `DatasetStats`.
- List views (`AssetList`, `PipelineList`, `MissionList`, `TimelineList`, `DatasetList`,
  `QueueView`) — error state with retry + empty state.
- Detail views (`DatasetDetails`, `AssetDetails`, `PipelineDetails`, `MissionDetails`,
  `TimelineDetails`) — loading/error/retry states.
- Stats components — loading/error states; AssetStats no longer shows "Loading stats..."
  forever without a project.
- Workspace panels (`ProjectExplorer`, `LayerManager`, `PropertiesPanel`) — loading/error
  states; import/delete feedback.
- Mutation feedback (toasts): dataset import, layer import, collection create, pipeline create,
  mission create, timeline create, favorites/pin/archive/restore/delete across modules.
- Destructive actions moved to `ConfirmDialog` where native `confirm()` was previously used.

## Lint/build verification

- Added `varsIgnorePattern: '^_'` / `argsIgnorePattern: '^_'` to `.eslintrc.cjs` to match the
  codebase's existing `_`-prefix convention.
- Fixed `react-hooks/exhaustive-deps` warnings in `MapCanvas` and `WorkspaceLayout`
  (intentional mount-once effects documented with `eslint-disable-next-line`).
- Results: `tsc --noEmit` clean, `eslint` clean (0 warnings), `vite build` succeeds.
- Known build note: main bundle exceeds 500 kB (OpenLayers + app); chunking is a future
  optimization, not a defect.

## Remaining known issues

- `TimelineList` / `TimelineDetails` / `LayerManager` still use native `confirm()` for some
  deletes (kept to preserve behavior; `ConfirmDialog` used for the primary flows).
- `ComparisonViewer` fires update mutations on slider moves without toasts (low).
- No automated test framework is installed in `frontend/package.json`; UI states were verified
  via typecheck/lint/build and manual QA checklist (`docs/UI_QA_CHECKLIST.md`). Adding Vitest +
  React Testing Library is recommended for S3.

## Do-not-implement compliance

No AI models, change detection, forecasting, threat scoring, satellite downloading, online
maps, cloud services, third-party integrations, new databases, or new architecture were added.
No dummy data was introduced. The existing dark GARUDA visual identity was preserved.
