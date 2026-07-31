import { describe, it, expect } from "vitest";
import { resolveBasemap } from "./useBasemaps";
import { BLANK_GRID_ID } from "../types/gis";
import type { GisBasemap } from "../types/gis";

const xyz: GisBasemap = {
  id: "xyz-map-abc",
  name: "Local Tiles",
  basemap_type: "xyz_dir",
  crs: "EPSG:3857",
  tile_url_template: "/api/v1/gis/basemaps/xyz-map-abc/tiles/{z}/{x}/{y}.png",
};

describe("resolveBasemap", () => {
  it("returns the matching registered basemap when id is present", () => {
    expect(resolveBasemap("xyz-map-abc", [xyz])).toEqual(xyz);
  });

  it("synthesizes a blank grid basemap for the blank_grid id", () => {
    const resolved = resolveBasemap(BLANK_GRID_ID, []);
    expect(resolved).toBeDefined();
    expect(resolved?.id).toBe(BLANK_GRID_ID);
    expect(resolved?.basemap_type).toBe("blank");
    expect(resolved?.tile_url_template).toBe("");
  });

  it("returns undefined when the id is unknown and not blank grid", () => {
    expect(resolveBasemap("does-not-exist", [xyz])).toBeUndefined();
  });

  it("returns undefined for nullish ids", () => {
    expect(resolveBasemap(null, [xyz])).toBeUndefined();
    expect(resolveBasemap(undefined, [xyz])).toBeUndefined();
  });
});
