import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LayerManager from "./LayerManager";
import { useLayers, useProjectAssets, useRegisterAssetLayer } from "../../hooks/useGeospatial";

const mutate = vi.fn();
const mutateAsync = vi.fn();
const registerMutateAsync = vi.fn();

vi.mock("../../hooks/useGeospatial", () => ({
  useLayers: vi.fn(() => ({ data: [], isLoading: false, isError: false, error: null, refetch: vi.fn() })),
  useAOIs: vi.fn(() => ({ data: [] })),
  useProjectAssets: vi.fn(() => ({ data: [], isLoading: false })),
  useToggleLayerVisibility: vi.fn(() => ({ mutate })),
  useDeleteLayer: vi.fn(() => ({ mutate })),
  useUpdateLayer: vi.fn(() => ({ mutate })),
  useDeleteAOI: vi.fn(() => ({ mutate })),
  useImportGeoJSON: vi.fn(() => ({ mutateAsync })),
  useImportKML: vi.fn(() => ({ mutateAsync })),
  useImportShapefile: vi.fn(() => ({ mutateAsync })),
  useImportRaster: vi.fn(() => ({ mutateAsync })),
  useRegisterAssetLayer: vi.fn(() => ({ mutateAsync: registerMutateAsync })),
}));

const mockedUseLayers = vi.mocked(useLayers);
const mockedUseProjectAssets = vi.mocked(useProjectAssets);
const mockedRegister = vi.mocked(useRegisterAssetLayer);

const layer = {
  id: "layer-1",
  project_id: "proj-1",
  name: "AOI Layer",
  layer_type: "vector",
  visible: true,
  opacity: 1,
  z_index: 1,
  source_id: null,
  source_type: null,
  style: null,
  extra_metadata: null,
  created_at: "",
  updated_at: "",
  crs: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  mockedUseLayers.mockReturnValue({ data: [layer], isLoading: false, isError: false, error: null, refetch: vi.fn() } as any);
  mockedUseProjectAssets.mockReturnValue({ data: [], isLoading: false } as any);
  mockedRegister.mockReturnValue({ mutateAsync: registerMutateAsync, mutate: mutate } as any);
});

describe("LayerManager", () => {
  it("renders the imported layer with its name", () => {
    render(<LayerManager projectId="proj-1" />);
    expect(screen.getByText("Layers")).toBeInTheDocument();
    expect(screen.getByText("AOI Layer")).toBeInTheDocument();
  });

  it("shows the empty state when no layers exist", () => {
    mockedUseLayers.mockReturnValue({ data: [], isLoading: false, isError: false, error: null, refetch: vi.fn() } as any);
    render(<LayerManager projectId="proj-1" />);
    expect(screen.getByText(/No layers yet/i)).toBeInTheDocument();
  });

  it("opens the import menu with all offline import options including raster", async () => {
    const user = userEvent.setup();
    render(<LayerManager projectId="proj-1" />);
    await user.click(screen.getByTitle("Import File"));
    expect(screen.getByText("Import GeoJSON")).toBeInTheDocument();
    expect(screen.getByText("Import KML")).toBeInTheDocument();
    expect(screen.getByText("Import Shapefile (ZIP)")).toBeInTheDocument();
    expect(screen.getByText("Import Raster (GeoTIFF)")).toBeInTheDocument();
    expect(screen.getByText("Register Asset as Layer")).toBeInTheDocument();
  });

  it("registers a project asset as a layer from the asset picker", async () => {
    const user = userEvent.setup();
    mockedUseProjectAssets.mockReturnValue({
      data: [{ id: "asset-1", name: "survey.kml", display_name: "survey.kml", asset_type: "vector" }],
      isLoading: false,
    } as any);
    render(<LayerManager projectId="proj-1" />);
    await user.click(screen.getByTitle("Import File"));
    await user.click(screen.getByText("Register Asset as Layer"));
    expect(screen.getByText("Register Asset as Layer", { selector: "h4" })).toBeInTheDocument();
    expect(screen.getByText("survey.kml")).toBeInTheDocument();
    await user.click(screen.getByText("survey.kml"));
    expect(registerMutateAsync).toHaveBeenCalledWith({ projectId: "proj-1", assetId: "asset-1", name: "survey.kml" });
  });
});
