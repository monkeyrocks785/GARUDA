# GARUDA Frontend UI Architecture

## Overview

GARUDA's frontend is a React 18 single-page application (Vite + TypeScript + Tailwind). It is a
desktop-focused geospatial analytics workbench backed by a FastAPI service (`/api/v1`). This
document describes the UI layer established during Stabilization Sprint S2.

## Stack

- **React 18** + **TypeScript 5.5**
- **Vite 5** (dev server proxies `/api` → `http://localhost:8000`)
- **Tailwind CSS** with the GARUDA dark slate palette (`primary` accent, `slate` neutrals)
- **TanStack Query v5** for server state (defaults: `staleTime` 5 min, `retry` 1,
  `refetchOnWindowFocus` disabled; mutations `retry` 0)
- **Zustand** for client/UI state (selections, workspace view state, toasts)
- **react-router-dom v6** for routing
- **OpenLayers** for the map workspace

## Layout

- `App.tsx` defines one top-level `MainLayout` route containing all pages.
- `MainLayout` renders the persistent application shell: `Sidebar` (navigation) and `TopNav`
  (page title, project context, live health indicator).
- Each page renders its own workspace. Project-scoped manager pages use a shared three-pane
  pattern (import/controls sidebar + list + details) topped with `Breadcrumbs`.
- `ToastContainer` is mounted once in `main.tsx`, above the router, and renders toasts from the
  global `useToastStore`.
- `ErrorBoundary` wraps the app in `main.tsx` and offers "Try Again" / "Reload".

## Shared UI components (`src/components/ui`)

| Component | Purpose |
| --- | --- |
| `Button` | Styled button with `variant`/`size`/`isLoading` props, `forwardRef` |
| `Card`, `CardHeader`, `CardBody` | Panel primitives |
| `Badge` | Status-aware tone mapping |
| `LoadingState` | Skeleton/spinner with optional `compact` and `label` |
| `ErrorState` | Error message with optional `compact` and `onRetry` |
| `EmptyState` | Empty content state with optional `compact`, `icon`, `action` |
| `ConfirmDialog` | Accessible confirm modal (`role="alertdialog"`, Escape, backdrop, focus) |
| `PageHeader` | Title + subtitle + actions header |
| `Breadcrumbs` | Link-aware breadcrumb trail |

## State handling pattern

Every data-backed view follows the same contract:

1. **Loading** — query pending → `LoadingState` (or `compact` variant inside panels).
2. **Error** — query failed → `ErrorState` with a human-readable message from
   `utils/getErrorMessage` (maps axios status codes) and a **Retry** that calls `refetch()`.
3. **Empty** — query succeeded with no rows → `EmptyState` with guidance (and a call-to-action
   where applicable). No fabricated or placeholder data is shown.
4. **Mutation feedback** — mutations surface results via `useToastStore` (`success` / `error`).
5. **Destructive actions** — delete/archive operations require `ConfirmDialog` (or an inline
   confirm where the original UI used one).

## Utilities

- `utils/format.ts` — NaN-safe `formatDate` / `formatShortDate` / `formatUptime`.
- `utils/json.ts` — `parseTagArray` / `parseJsonField` for crash-proof parsing of backend JSON
  columns (e.g. `tags`).
- `utils/errorMessage.ts` — `getErrorMessage(error)` → localized friendly string.

## Data flow

- TanStack Query hooks (`src/hooks/use*.ts`) call axios services (`src/services/*Api.ts`).
- Backend is the single source of truth. Pages never invent values; when the backend returns
  nothing, pages show an empty state.
- Project identity flows through the URL (`/projects/:id/...`). Each manager page seeds its
  Zustand store with `id` on mount, and the map workspace restores/persists view state through
  `/workspace` endpoints.

## Theme

GARUDA is dark-only. The Tailwind config defines the `primary` accent and `slate` neutrals.
Per S2 scope, no theme subsystem was introduced.

## Do not

- Do not introduce a new UI framework or rebuild the frontend from scratch.
- Do not add dummy data or fabricated values; use empty states instead.
- Do not add new intelligence features (AI, forecasting, threat scoring, cloud, third-party
  integrations).
