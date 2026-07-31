# GARUDA v0.5 — GIS Workspace

The GIS workspace is GARUDA's offline-first map surface. It renders project layers
(raster and vector), areas of interest (AOIs), drawings, and measurements on a blank
grid or on locally-sourced basemaps. There are **no online map providers**: everything
displayed comes from files on disk and the backend tile proxy.

## Routes

| Route | Purpose |
| --- | --- |
| `/projects/:projectId/gis` | GIS workspace (primary route) |
| `/projects/:projectId/map` | Alias of the GIS workspace (both are kept working) |

The "Open Map" action on `ProjectDashboard` navigates to `/projects/:id/gis`.

## Panels

- **Layers** (`LayerManager`) — list, reorder (by z-index), rename, toggle visibility,
  adjust opacity, delete, import files, register an asset as a layer. Raster layers are
  shown with a `🖼️` icon, AOIs with `🎯`, vectors with `📍`.
- **Properties** (`PropertiesPanel`) — details of the selected layer (including its CRS)
  or AOI.
- **Layers / AOI split** — AOIs render in their own section under the layer list.

## Importing data

All imports are local files; nothing is downloaded.

| Source | Format | Notes |
| --- | --- | --- |
| Raster | `.tif`, `.tiff` | Stored per project under `storage/projects/{projectId}/rasters/`; displayed through the on-demand tile proxy |
| Vector | `.geojson`, `.json` | Stored as an imported file; features served via the features endpoint |
| Vector | `.kml` | Same as GeoJSON |
| Vector (zipped shapefile) | `.zip` | Same as GeoJSON |
| Existing asset | any GARUDA asset | "Register Asset as Layer" — adds `source_type=asset` |

Drag-and-drop onto the map dispatches to the same import paths (GeoTIFF, GeoJSON, KML,
ZIP) with toast feedback.

## Drawing and measuring

- Draw tools: polygon, rectangle, circle, line, point. Drawings are stored as
  GeoJSON features in the workspace state and persisted to the server
  (`drawing_features`); they survive reload.
- Measure tools: distance (m/km), area (m²/km²), and bearing. Measurements render on a
  dedicated measurement source and are **not** persisted; drawing a new measurement
  clears the previous one.
- Undo/redo (Ctrl+Z / Ctrl+Y) applies to drawing actions.

## AOIs

AOIs created in the project are drawn on the map with their per-AOI fill/stroke colors.
Selecting an AOI (in the layer manager or on the map) shows its properties. AOI geometry
is stored on the server; drawing polygons is separate from AOI management.

## Basemaps

- The default is a **Blank Grid** (EPSG:3857 grid overlay) — always available.
- Additional offline basemaps (local XYZ tile folders, registered GeoTIFFs) are listed
  in the basemap selector at the top of the workspace. See `OFFLINE_GIS.md`.

## View and layout state

The map view (center, zoom, rotation), panel visibility/sizes, the active basemap, layer
visibility, and drawings are autosaved (2 s debounce) per project and restored on reload.
If a saved basemap id no longer resolves, the workspace falls back to the blank grid.

## Keyboard shortcuts

`H` home/zoom reset · `P` pan · `L` line · `G` polygon · `R` rectangle · `C` circle ·
`D` point · `A` distance · `B` area · `E` bearing · `X` deselect · `Ctrl+Z` undo ·
`Ctrl+Y` redo.

## Backend endpoints used by the workspace

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/gis/basemaps` | List available basemaps |
| `POST /api/v1/gis/basemaps/geotiff` | Register a GeoTIFF basemap |
| `DELETE /api/v1/gis/basemaps/{id}` | Unregister a basemap |
| `GET /api/v1/gis/basemaps/{id}/tiles/{z}/{x}/{y}.png` | Serve a basemap tile |
| `POST /api/v1/rasters/{projectId}/import` | Import an uploaded raster |
| `GET /api/v1/rasters/{projectId}/{rasterId}/tiles/{z}/{x}/{y}.png` | Serve a raster tile |
| `POST /api/v1/projects/{projectId}/layers/from-asset` | Add an asset as a layer |
| `GET /api/v1/projects/{projectId}/layers/{layerId}/features` | Vector features (EPSG:4326, simplified) |
