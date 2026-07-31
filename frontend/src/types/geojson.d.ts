export {};

declare global {
  namespace GeoJSON {
    interface Geometry {
      type: string;
      coordinates: number[] | number[][] | number[][][] | number[][][][];
    }
    interface Feature {
      type: "Feature";
      geometry: Geometry;
      properties: Record<string, unknown> | null;
    }
    interface FeatureCollection {
      type: "FeatureCollection";
      features: Feature[];
    }
  }
}
