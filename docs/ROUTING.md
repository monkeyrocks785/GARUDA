# GARUDA Frontend Routing

All routes live under the authenticated shell in `src/App.tsx` (single `<Route path="/">`
with `MainLayout`).

## Route table

| Path | Page | Notes |
| --- | --- | --- |
| `/` | `Dashboard` | Landing: project stats + recent projects + quick actions |
| `/projects` | `Projects` | Project list + create modal |
| `/projects/:id` | `ProjectDashboard` | Project overview; seeds dataset/AOI/pipeline/asset stores |
| `/projects/:id/map` | `MapPage` → `WorkspaceLayout` | OpenLayers map workspace |
| `/projects/:id/datasets` | `DatasetManager` | Dataset import/filter/list/details |
| `/projects/:id/assets` | `AssetLibrary` | Asset import/filter/list/details/collections |
| `/projects/:id/pipelines` | `PipelineManager` | Pipeline list/details + queue |
| `/projects/:id/queries` | `QueryBuilderPage` | Saved query builder + history |
| `/missions` | `MissionManager` | Missions list/details + timeline |
| `/timelines` | `TimelineManager` | Temporal timelines list/details |
| `/rules` | `RuleManager` | Rules engine |
| `/alerts` | `AlertDashboard` | Alerts with status actions |
| `/settings` | `Settings` | Backend health + config pages (empty states) |
| `/about` | `About` | Version/environment from health endpoint |

## Navigation

- `Sidebar` (`src/components/Sidebar.tsx`) provides the persistent nav. Items: Dashboard,
  Projects, Missions, Timelines, Rules, Alerts, Settings, About.
- `TopNav` (`src/components/TopNav.tsx`) derives the page title from the matched route and
  shows the active project id on project-scoped routes. It also renders a live health
  indicator from the `/health` endpoint.
- Project-scoped pages render `Breadcrumbs` (Projects → Project → Section) for context and to
  support back-navigation.

## Project context

Project id is carried by the URL. On mount, each manager page calls its store's
`setProjectId(id)`, and guards against a missing id by rendering an `EmptyState` with a
"Go to Projects" action (see `DatasetManager`, `AssetLibrary`, `PipelineManager`).
