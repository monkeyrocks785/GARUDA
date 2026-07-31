# GARUDA v0.5 — S3 GIS Workspace Stabilization Report

Scope: complete the GIS workspace (offline-first) and integrate the Offline Map layer.
The full S3 sprint was executed; the goal was a stable, offline-only map experience with
no online providers, backed by tested APIs.

## Summary

GARUDA's GIS workspace is now a complete offline-first map surface. It renders raster and
vector layers, AOIs, drawings, and measurements against a blank grid or locally-sourced
basemaps. Rasters are displayed through a backend tile proxy (original file stays
authoritative). All 20 backend tests in `tests/test_gis_engine.py` pass, the extended
backend run (44 tests) passes, the frontend builds and lints clean, and a live HTTP smoke
test confirmed the full pipeline (import → tile → basemap → features) against a running
server.

## What changed

### Backend

- **Raster import & display**
  - `raster_engine/services/import_service.py` — `import_raster_upload` stores uploads per
    project (`{PROJECTS_DIR}/{projectId}/rasters/`), validates with rasterio, creates the
    `Dataset` row (FK constraint), `RasterMetadata`, and a `Layer` with `crs`.
  - `raster_engine/services/tile_server.py` — on-demand EPSG:3857 tile renderer for
    rasters in any CRS (windowed read ≤ 1024² px, pyproj transform, warp reproject,
    percentile stretch, RGBA PNG) with an on-disk tile cache.
  - `POST /api/v1/rasters/{projectId}/import` (201), `GET .../tiles/{z}/{x}/{y}.png`
    (z≤24, 400 invalid coords, 404 no data, `Cache-Control: max-age=86400`).
- **Offline basemaps** (`gis_engine/`)
  - `basemap_service.py` — blank grid + auto-discovered local XYZ tile folders
    (`storage/tiles/`, slug-matched ids) + registered GeoTIFFs; path-traversal-safe tile
    serving.
  - `POST /api/v1/gis/basemaps/geotiff` (201), `DELETE` (204/404), tile GET, basemap list.
  - `gis_basemaps` table (migration `018_gis_workspace`).
- **Vector features**
  - `geo/layer_features_service.py` — resolves layer sources (aoi/imported_file/asset),
    reprojects to EPSG:4326, simplifies (extent/2000), caps to `max_features`.
  - `POST /api/v1/projects/{projectId}/layers/from-asset` (201), `GET .../features`.
- **Path security** — `geo/secure_paths.py` centralizes `allowed_roots()` /
  `is_allowed_location()` and is applied to basemap registration, asset storage, and
  feature path resolution. Root cause of the earlier false 400s was a relative
  `STORAGE_DIR` vs absolute `TILES_DIR`/`BASEMAPS_DIR` mismatch; the fix is in code, not
  `.env`.
- **Layer model** — `layers.crs` column; Layer/Create/Update/Response schemas updated.

### Frontend

- Offline-first types/data layer: `types/gis.ts`, global GeoJSON types (`geojson.d.ts`),
  `basemapApi`, `rasterApi.importRaster`, `useBasemaps`, extended `useGeospatial` hooks.
- `MapCanvas` rewrite (OpenLayers 10): offline basemap resolution (XYZ backend tiles or
  blank grid), per-layer raster (tile proxy) / vector (features) layers, styled AOI layer,
  drawing + measurement (dedicated measure source), pointer lat/lng, selection, zoom-to,
  view sync.
- `WorkspaceLayout` rewrite: basemap selector, navigation toolbar, resizable panels,
  autosave/restore (view, panels, basemap, visibility, drawings), drag-drop import,
  keyboard shortcuts.
- `LayerManager`: raster import, "Register Asset as Layer" asset picker, server-truth
  visibility + toggle-all.
- Routing: `/projects/:id/gis` alias route; ProjectDashboard "Open Map" → gis; TopNav.
- Vitest + React Testing Library installed; 8 frontend tests (basemap resolution + layer
  manager) pass; `npm run build` (tsc + vite) and `npm run lint` pass.

## Verification

| Gate | Result |
| --- | --- |
| `tests/test_gis_engine.py` (20 tests) | Pass (≈61 s) |
| Extended: + `test_geospatial.py` + `test_projects.py` (44 tests) | Pass (≈120 s) |
| `alembic upgrade head` on fresh DB | Pass (018 head) |
| `npm run test` | 8/8 pass |
| `npm run build` | Pass (460 modules; >500 kB chunk warning pre-existing) |
| `npm run lint` | Pass (0 warnings) |
| Live smoke (running server) | Import 201, tile PNG 200 + cache hit, features 400 on raster, GeoTIFF basemap 201 + tile, list |

Dev DB note: the local `storage/garuda.db` was already schema-synced by `create_all()`
(crs column + `gis_basemaps` present) while `alembic_version` sat at 017, so it was
stamped to `018_gis_workspace`; fresh DBs apply the migration normally.

## Remaining known issues

- Main JS bundle exceeds 500 kB (OpenLayers + app); code-splitting is a future
  optimization, not a defect.
- Raster tile proxy re-reads source windows without cached overviews; acceptable for the
  current scale, worth revisiting for very large mosaics.
- Backend `test_gis_engine.py` runtime is ~60 s (real raster reprojection); split hot
  path tests from slow ones if CI becomes sensitive.
- No automated E2E test for the OpenLayers canvas in jsdom (canvas not implemented); the
  map is covered by build/lint + manual QA.

## Do-not-implement compliance

No online map providers, cloud services, new databases, or third-party integrations were
added. All online OSM/CARTO/Esri basemap entries were removed. No AI models, change
detection, forecasting, threat scoring, or satellite downloading were introduced. No dummy
data was added. The existing dark GARUDA visual identity was preserved.
