# GARUDA v0.5 — Offline GIS Basemaps

GARUDA is **offline-first**. It does not contact OSM, CARTO, Esri, or any other online
tile provider. Basemaps come from two local sources plus a built-in blank grid.

## Basemap sources

| `basemap_type` | Source | Backing store |
| --- | --- | --- |
| `blank` | Built-in blank EPSG:3857 grid (`blank_grid`) | code |
| `xyz_dir` | Auto-discovered local XYZ tile folders | `storage/tiles/` |
| `geotiff` | Registered raster files | anywhere inside configured data locations (path-validated) |

### Local XYZ tile folders

Any subfolder of the configured `TILES_DIR` (default `backend/storage/tiles/`) that
contains a `{z}/{x}/{y}.png` pyramid (probe: `1/0/0.png`) is auto-discovered. A folder
named `map_abc` is exposed as basemap id `xyz-map-abc` (slugified), so ids remain stable
and are resilient to naming changes. Tiles are served directly from disk with no
processing:

```
GET /api/v1/gis/basemaps/xyz-map-abc/tiles/{z}/{x}/{y}.png
```

### Registered GeoTIFFs

Register a local raster as a basemap:

```
POST /api/v1/gis/basemaps/geotiff
{ "name": "Local Imagery", "path": "F:\\...\\storage\\basemaps\\ortho.tif" }
```

Registration requires the path to resolve **inside one of the configured GARUDA data
locations** (`STORAGE_DIR`, `PROJECTS_DIR`, `TILES_DIR`, `BASEMAPS_DIR`, `MODELS_DIR`,
`EXPORT_DIR` — see `geo/secure_paths.py`). Paths outside these roots are rejected with
`400 "Basemap path must be inside the configured storage directory"`, and the file must
open as a valid raster via rasterio. Duplicate registrations (same resolved path) are
idempotent. Unregister with `DELETE /api/v1/gis/basemaps/{id}` (204, or 404 if unknown).

Registered basemap tiles are rendered on demand through the shared raster tile proxy
(`raster_engine/services/tile_server.py`), so any CRS is reprojected to web-mercator.

## Blank grid

`blank_grid` is always the first entry in `GET /api/v1/gis/basemaps` and is synthesized
client-side if it ever disappears. The frontend renders it with a `createBlankGridSource()`
so the workspace always has a tiled, interactive surface even with no local basemap.

## Tile serving

All basemap tile routes share the same contract:

```
GET /api/v1/gis/basemaps/{basemap_id}/tiles/{z}/{x}/{y}.png
```

- `z` must be `0..24`; `x`/`y` must be within `0..2^z-1`; otherwise `400`.
- Missing data returns `404`.
- Responses are `image/png` with `Cache-Control: public, max-age=86400`.

## Security

- **XYZ folders**: the requested basemap id is matched by slug to a folder, then every
  resolved path (folder and tile) is re-checked to stay inside `TILES_DIR`; `..`
  traversal cannot escape.
- **GeoTIFF registration**: paths are `Path.resolve()`d and checked with
  `is_allowed_location()` before opening — no arbitrary filesystem reads.
- **Tile rendering** reads only the raster window needed for the requested tile, capped
  at `1024²` source pixels per tile (`MAX_READ_PIXELS`).

## Layout

```
storage/
  tiles/            # drop XYZ tile folders here (auto-discovered)
  basemaps/         # GeoTIFF basemap files can live here
  cache/raster_tiles/  # on-disk tile cache (rendered GeoTIFF tiles)
```
