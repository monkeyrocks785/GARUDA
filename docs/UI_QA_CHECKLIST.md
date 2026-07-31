# GARUDA UI QA Checklist (S2)

Manual + automated checklist used to verify UI/UX stabilization.

## Navigation & shell

- [ ] Sidebar shows all real routes: Dashboard, Projects, Missions, Timelines, Rules, Alerts, Settings, About.
- [ ] `TopNav` shows the correct page title for every route, including project routes.
- [ ] Project id is shown in the header when inside `/projects/:id/...`.
- [ ] Health indicator reflects real backend status (green/red), not a hardcoded value.
- [ ] Breadcrumbs appear on project-scoped pages (Datasets, Assets, Pipelines) and Missions.
- [ ] No route renders a blank page.

## Project flow

- [ ] Dashboard → project card opens `/projects/:id`.
- [ ] Project click opens the correct project (id round-trips through the URL and stores).
- [ ] Dataset/AOI/Pipeline/Asset stats load with placeholder state (not misleading zeros).
- [ ] Workspace map loads with a visible OSM basemap and restores saved view state.
- [ ] Missing `projectId` (manual URL) shows an EmptyState with "Go to Projects", never a crash.

## Data states

- [ ] Every list (projects, datasets, assets, pipelines, missions, timelines, queue) shows:
  - loading state while pending,
  - error state with Retry on failure,
  - empty state when the backend returns zero rows.
- [ ] Every detail panel (dataset, asset, pipeline, mission, timeline) shows loading/error/retry.
- [ ] Stats panels handle missing `by_type` without crashing.

## Mutations & feedback

- [ ] Create project/mission/pipeline/timeline/collection shows success + error toasts.
- [ ] Import dataset/geojson/kml/shapefile shows success + error toasts.
- [ ] Favorite/pin/archive/restore/delete actions show feedback.
- [ ] Delete/archive/remove actions require confirmation.
- [ ] Alert status actions send valid backend statuses and show feedback.

## Design consistency

- [ ] Pages use GARUDA dark slate/primary palette; no stray light-theme (gray/blue) surfaces.
- [ ] Shared `LoadingState`/`ErrorState`/`EmptyState` used rather than ad-hoc text.
- [ ] Modals: Escape closes, backdrop click closes, focus moves to confirm, `aria-modal` set.
- [ ] Forms disable submit while pending; inline validation for required fields.

## Safety

- [ ] No unguarded `JSON.parse` on backend `tags`/`metadata` fields.
- [ ] No NaN dates rendered (safe formatters used).
- [ ] No console errors on route changes, query failures, or mutation failures.
- [ ] No unhandled promise rejections from `mutateAsync` calls.

## Build gates

- [ ] `npx tsc --noEmit` passes.
- [ ] `npm run lint` passes (0 warnings).
- [ ] `npm run build` succeeds.
