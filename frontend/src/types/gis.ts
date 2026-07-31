// ============================================================
// GIS Types - offline basemaps, raster import, layer features
// ============================================================

export interface GisBasemap {
  id: string;
  name: string;
  basemap_type: "blank" | "xyz_dir" | "geotiff";
  crs: string | null;
  tile_url_template: string;
}

export interface RasterImportResponse {
  layer_id: string;
  raster_id: string;
  project_id: string;
  name: string;
  file_path: string;
  crs: string | null;
  width: number;
  height: number;
  band_count: number;
  file_size: number;
  tile_url_template: string;
}

export interface LayerFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSON.Feature[];
  crs?: string;
  simplified?: boolean;
  returned_count?: number;
}

export interface FromAssetRequest {
  asset_id: string;
  name?: string;
}

export const BLANK_GRID_ID = "blank_grid";
