# GARUDA v0.5 — GIS Data Flow

This document describes how data flows through the GIS workspace: upload → storage →
layer → tile/feature serving → map rendering.

## 1. Raster import

```
Upload (.tif/.tiff)
   │ POST /api/v1/rasters/{projectId}/import   (multipart)
   ▼
import_raster_upload (raster_engine/services/import_service.py)
   ├─ validates extension (RASTER_EXTENSIONS)
   ├─ saves bytes to {PROJECTS_DIR}/{projectId}/rasters/{uuid}{ext}
   ├─ rasterio metadata check
   ├─ creates an assets.Dataset row (FK: raster_metadata.dataset_id NOT NULL)
   ├─ creates RasterMetadata (crs, width, height, band_count, size)
   └─ creates a Layer { layer_type: "raster", source_type: "raster",
                       source_id: <raster_id>, crs }
   ▼
201 RasterImportResponse { layer_id, raster_id, crs, tile_url_template, ... }
```

The original raster file remains the authority. The browser never receives the file —
only 256×256 PNG tiles rendered on demand.

## 2. Raster display (tile proxy)

```
OpenLayers TileLayer (XYZ source)
   │ GET /api/v1/rasters/{projectId}/{rasterId}/tiles/{z}/{x}/{y}.png
   ▼
raster_engine/services/tile_server.py serve_tile(path, z, x, y)
   ├─ tile_bounds(z,x,y) in EPSG:3857
   ├─ transform tile bounds → source CRS (pyproj)
   ├─ clip to raster footprint
   ├─ read window (≤ 1024² pixels, bilinear downsample)
   ├─ rasterio.warp.reproject → EPSG:3857 256×256
   └─ percentile stretch (2–98 %) → RGBA PNG (MemoryFile)
   ▼
writes/reads {CACHE_DIR}/raster_tiles/{rasterId}/{z}/{x}/{y}.png
   └─ Cache-Control: public, max-age=86400
```

GeoTIFF basemaps use the same proxy via `serve_registered_tile`. Raster layers return
`400` from the vector-features endpoint (`"Raster layers have no vector features"`).

## 3. Vector layers

A vector layer is backed by an `ImportedFile` (GeoJSON/KML/shapefile upload) or by a
registered GARUDA **asset** (`POST /api/v1/projects/{projectId}/layers/from-asset`,
`source_type: "asset"`). Drawing an AOI creates `source_type: "aoi"`.

```
MapCanvas VectorLayer
   │ GET /api/v1/projects/{projectId}/layers/{layerId}/features?max_features=2000&simplify=true
   ▼
geo/layer_features_service.py LayerFeaturesService
   ├─ resolve source path (aoi → AOI row; imported_file → storage_path;
   │    asset → asset.storage_path)  [all paths validated by is_allowed_location]
   ├─ gpd.read_file(path)
   ├─ reproject → EPSG:4326 (if crs differs)
   ├─ simplify (tolerance = extent / 2000, preserve_topology)
   ├─ cap to max_features (1–100000) by striding
   └─ __geo_interface__ FeatureCollection
       { features, crs: "EPSG:4326", simplified, returned_count }
```

AOI layers synthesize a single Feature from the AOI record (including `fill_color`).

## 4. Drawings and measurements

- Drawing features live in the workspace store as `GeoJSON.Feature[]`, persisted to the
  server workspace `drawing_features` field. On load they are replayed into a dedicated
  VectorSource; on `drawend` they are persisted back.
- Measurement features are drawn into a separate `measureSource` so they never touch the
  persisted drawing source; new measurements clear only the previous measurement.

## 5. Workspace persistence

`WorkspaceLayout` autosaves (2 s debounce) the view, panel layout, active basemap id,
visible layer ids, and drawings to the project workspace state. Restore falls back to
`blank_grid` when a saved basemap id no longer resolves.

## 6. Layers table additions

Migration `018_gis_workspace` added `layers.crs` (`VARCHAR(50)`, nullable) and the
`gis_basemaps` table. The CRS is captured at import/registration time (e.g.
`EPSG:4326`) and echoed in the layer list/properties.

```
Layer
 ├─ layer_type: raster | vector | aoi
 ├─ source_type: raster | imported_file | asset | aoi
 ├─ source_id   → raster_metadata.id | imported_files.id | assets.id | aois.id
 ├─ crs
 └─ visible / opacity / z_index / style
```

## Error semantics

| Case | Status |
| --- | --- |
| Invalid upload extension / corrupt raster | `400` |
| Unsupported source type / missing source | `400` |
| Raster features requested | `400` |
| Unknown layer / raster / basemap | `404` |
| Path outside allowed locations | `400` |
| Tile outside `z 0..24` or raster footprint | `400` / `404` |
