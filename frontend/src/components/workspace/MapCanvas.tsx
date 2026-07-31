import { useEffect, useRef, useCallback } from "react";
import OlMap from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import XYZ from "ol/source/XYZ";
import GeoJSONFormat from "ol/format/GeoJSON";
import { fromLonLat, toLonLat } from "ol/proj";
import { Draw, Modify, Snap } from "ol/interaction";
import { createBox } from "ol/interaction/Draw";
import { Circle as CircleStyle, Fill, Stroke, Style } from "ol/style";
import { asArray, toString as colorToString } from "ol/color";
import { FullScreen, ScaleLine } from "ol/control";
import { isEmpty } from "ol/extent";
import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import { useLayers, useAOIs } from "../../hooks/useGeospatial";
import { layerApi } from "../../services/api";
import { resolveBasemap } from "../../hooks/useBasemaps";
import type { GisBasemap } from "../../types/gis";
import type { Layer, AOI } from "../../types";

interface MapCanvasProps {
  projectId: string | undefined;
  basemaps?: GisBasemap[];
}

const BLANK_GRID_TILE =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQABNjN9GQAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAAA0lEQVQI12P4z8BQDwAEgAF/QualzQAAAABJRU5ErkJggg==";

function createBlankGridSource(): XYZ {
  return new XYZ({
    url: BLANK_GRID_TILE,
    crossOrigin: "anonymous",
    maxZoom: 0,
  });
}

function hashColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 60%, 50%)`;
}

function createLayerStyle(layer: Layer) {
  const color = hashColor(layer.id);
  return (feature: any) => {
    const geomType = feature.getGeometry()?.getType();
    const styles: Style[] = [];
    if (geomType === "Point") {
      styles.push(
        new Style({
          image: new CircleStyle({
            radius: 5,
            fill: new Fill({ color }),
            stroke: new Stroke({ color: "#ffffff", width: 1.5 }),
          }),
        })
      );
    } else {
      styles.push(
        new Style({
          fill: new Fill({ color: `${color}33` }),
          stroke: new Stroke({ color, width: 2 }),
        })
      );
    }
    return styles;
  };
}

function withOpacity(color: string, alpha: number): string {
  try {
    const arr = asArray(color);
    arr[3] = Math.min(1, Math.max(0, alpha));
    return colorToString(arr);
  } catch {
    return color;
  }
}

function createAOIStyle(aoi: AOI) {
  const opacity = Math.min(1, Math.max(0, aoi.fill_opacity ?? 0.2));
  return new Style({
    fill: new Fill({ color: withOpacity(aoi.fill_color, opacity) }),
    stroke: new Stroke({ color: aoi.stroke_color, width: aoi.stroke_width || 2 }),
  });
}

export default function MapCanvas({ projectId, basemaps }: MapCanvasProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<OlMap | null>(null);
  const drawInteractionRef = useRef<Draw | null>(null);
  const modifyInteractionRef = useRef<Modify | null>(null);
  const snapInteractionRef = useRef<Snap | null>(null);
  const drawingSourceRef = useRef<VectorSource | null>(null);
  const measureSourceRef = useRef<VectorSource | null>(null);
  const aoiSourceRef = useRef<VectorSource | null>(null);
  const aoiLayerRef = useRef<VectorLayer | null>(null);
  const basemapLayerRef = useRef<TileLayer<XYZ> | null>(null);
  const layerObjectsRef = useRef<Map<string, TileLayer<XYZ> | VectorLayer>>(
    new Map()
  );

  const {
    zoom,
    center,
    mapRotation,
    basemap,
    activeTool,
    selectedLayerId,
    selectedObjectId,
    selectedObjectType,
    drawingFeatures,
    setZoom,
    setCenter,
    setMousePosition,
    setMeasurementResult,
    pushUndo,
  } = useWorkspaceStore();

  const { data: layers = [] } = useLayers(projectId || null);
  const { data: aois = [] } = useAOIs(projectId || null);

  const handlePointerMove = useCallback(
    (evt: any) => {
      if (evt.coordinate) {
        const lonLat = toLonLat(evt.coordinate);
        setMousePosition([lonLat[1], lonLat[0]]);
      }
    },
    [setMousePosition]
  );

  // ============================================================
  // Map init (once)
  // ============================================================

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const drawingSource = new VectorSource();
    drawingSourceRef.current = drawingSource;

    const measureSource = new VectorSource();
    measureSourceRef.current = measureSource;

    const aoiSource = new VectorSource();
    aoiSourceRef.current = aoiSource;

    const drawingLayer = new VectorLayer({
      source: drawingSource,
      style: createLayerStyle({ id: "drawing" } as Layer),
      zIndex: 200,
    });

    const measureLayer = new VectorLayer({
      source: measureSource,
      style: createLayerStyle({ id: "measure" } as Layer),
      zIndex: 210,
    });

    const aoiLayer = new VectorLayer({
      source: aoiSource,
      zIndex: 100,
    });
    aoiLayerRef.current = aoiLayer;

    const basemapLayer = new TileLayer({ source: createBlankGridSource(), zIndex: 0 });
    basemapLayerRef.current = basemapLayer;

    const scaleLine = new ScaleLine({ units: "metric" });
    const fullScreen = new FullScreen();

    const map = new OlMap({
      target: mapRef.current,
      layers: [basemapLayer, aoiLayer, drawingLayer, measureLayer],
      view: new View({
        center: fromLonLat(center),
        zoom: zoom,
        rotation: mapRotation,
        minZoom: 0,
        maxZoom: 24,
      }),
      controls: [scaleLine, fullScreen],
    });

    map.on("pointermove", handlePointerMove);

    map.on("click", (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature) {
        useWorkspaceStore.setState({
          selectedObjectId: feature.get("id") || null,
          selectedObjectType: feature.get("type") || "feature",
        });
      } else {
        useWorkspaceStore.setState({ selectedObjectId: null, selectedObjectType: null });
      }
    });

    map.on("moveend", () => {
      const view = map.getView();
      const c = toLonLat(view.getCenter() || [0, 0]);
      setZoom(view.getZoom() || 2);
      setCenter([c[1], c[0]]);
    });

    const modify = new Modify({ source: drawingSource });
    map.addInteraction(modify);
    modifyInteractionRef.current = modify;

    const snap = new Snap({ source: drawingSource });
    map.addInteraction(snap);
    snapInteractionRef.current = snap;

    mapInstanceRef.current = map;

    return () => {
      map.setTarget(undefined);
      mapInstanceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ============================================================
  // View sync
  // ============================================================

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const view = map.getView();
    const currentCenter = toLonLat(view.getCenter() || [0, 0]);
    const currentZoom = view.getZoom() || 2;

    if (Math.abs(currentZoom - zoom) > 0.01) {
      view.setZoom(zoom);
    }
    if (
      Math.abs(currentCenter[0] - center[1]) > 0.0001 ||
      Math.abs(currentCenter[1] - center[0]) > 0.0001
    ) {
      view.setCenter(fromLonLat(center));
    }
    if (Math.abs(view.getRotation() - mapRotation) > 0.001) {
      view.setRotation(mapRotation);
    }
  }, [zoom, center, mapRotation]);

  // ============================================================
  // Basemap (offline only)
  // ============================================================

  useEffect(() => {
    const basemapLayer = basemapLayerRef.current;
    if (!basemapLayer) return;

    const resolved = resolveBasemap(basemap, basemaps);
    if (resolved && resolved.tile_url_template) {
      basemapLayer.setSource(
        new XYZ({ url: resolved.tile_url_template, crossOrigin: "anonymous" })
      );
    } else {
      basemapLayer.setSource(createBlankGridSource());
    }
  }, [basemap, basemaps]);

  // ============================================================
  // Layer objects (raster tiles + vector features)
  // ============================================================

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !projectId) return;

    const layerObjects = layerObjectsRef.current;
    const mapLayers = map.getLayers();
    const currentIds = new Set(layers.map((l) => l.id));

    for (const [id, olLayer] of layerObjects) {
      if (!currentIds.has(id)) {
        mapLayers.remove(olLayer);
        layerObjects.delete(id);
      }
    }

    for (const layer of layers) {
      const visible = layer.visible !== false;
      const existing = layerObjects.get(layer.id);

      if (!existing) {
        let olLayer: TileLayer<XYZ> | VectorLayer;
        if (layer.layer_type === "raster") {
          const url = `/api/v1/rasters/${projectId}/${layer.source_id}/tiles/{z}/{x}/{y}.png`;
          olLayer = new TileLayer({
            source: new XYZ({ url, crossOrigin: "anonymous" }),
            opacity: layer.opacity,
            visible,
            zIndex: 10 + layer.z_index,
          });
        } else {
          const source = new VectorSource();
          olLayer = new VectorLayer({
            source,
            opacity: layer.opacity,
            visible,
            style: createLayerStyle(layer),
            zIndex: 10 + layer.z_index,
          });
        }
        mapLayers.insertAt(mapLayers.getLength() - 2, olLayer);
        layerObjects.set(layer.id, olLayer);
      } else {
        existing.setVisible(visible);
        existing.setOpacity(layer.opacity);
        existing.setZIndex(10 + layer.z_index);
      }
    }
  }, [layers, projectId]);

  // ============================================================
  // Vector feature loading
  // ============================================================

  useEffect(() => {
    if (!projectId) return;
    const controllers: AbortController[] = [];

    for (const layer of layers) {
      if (layer.layer_type === "raster" || layer.visible === false) continue;
      const olLayer = layerObjectsRef.current.get(layer.id);
      if (!(olLayer instanceof VectorLayer)) continue;
      const source = olLayer.getSource();
      if (!source) continue;

      const ctrl = new AbortController();
      controllers.push(ctrl);
      layerApi
        .getFeatures(projectId, layer.id, { max_features: 2000, simplify: true })
        .then((res) => {
          if (ctrl.signal.aborted) return;
          const features = new GeoJSONFormat().readFeatures(res.data, {
            featureProjection: "EPSG:3857",
            dataProjection: "EPSG:4326",
          });
          source.clear();
          source.addFeatures(features);
        })
        .catch((err) => {
          if (!ctrl.signal.aborted) {
            console.error(`Failed to load features for layer ${layer.id}`, err);
          }
        });
    }

    return () => controllers.forEach((c) => c.abort());
  }, [layers, projectId]);

  // ============================================================
  // AOI rendering
  // ============================================================

  useEffect(() => {
    const source = aoiSourceRef.current;
    if (!source) return;

    source.clear();
    const styleCache = new Map<string, Style>();
    for (const aoi of aois) {
      try {
        const geometry = JSON.parse(aoi.geometry) as GeoJSON.Geometry;
        const feature = new GeoJSONFormat().readFeature(
          { type: "Feature", geometry, properties: { id: aoi.id, name: aoi.name, type: "aoi" } },
          { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" }
        ) as import("ol").Feature;
        styleCache.set(aoi.id, createAOIStyle(aoi));
        source.addFeature(feature);
      } catch (e) {
        console.warn(`Invalid AOI geometry for ${aoi.id}`, e);
      }
    }
    aoiLayerRef.current?.setStyle((feature) => {
      const style = styleCache.get(feature.get("id"));
      return style || createLayerStyle({ id: "aoi" } as Layer)(feature);
    });
  }, [aois]);

  // ============================================================
  // Drawing persistence (restore + keep in sync)
  // ============================================================

  useEffect(() => {
    const source = drawingSourceRef.current;
    if (!source) return;

    source.clear();
    for (const feature of drawingFeatures) {
      if (!feature?.geometry) continue;
      try {
        const olFeature = new GeoJSONFormat().readFeature(feature, {
          featureProjection: "EPSG:3857",
          dataProjection: "EPSG:4326",
        }) as import("ol").Feature;
        source.addFeature(olFeature);
      } catch (e) {
        console.warn("Skipping invalid drawing feature", e);
      }
    }
  }, [drawingFeatures]);

  const handleDrawEnd = useCallback(
    (feature: any) => {
      feature.set("type", "drawing");
      feature.set("id", crypto.randomUUID());
      pushUndo({ type: "add", feature: feature.getProperties() });
      const geojson = new GeoJSONFormat().writeFeatureObject(feature);
      const state = useWorkspaceStore.getState();
      state.setDrawingFeatures([...state.drawingFeatures, geojson]);
    },
    [pushUndo]
  );

  // ============================================================
  // Drawing / measurement tools
  // ============================================================

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (drawInteractionRef.current) {
      map.removeInteraction(drawInteractionRef.current);
      drawInteractionRef.current = null;
    }

    const source = drawingSourceRef.current;
    if (!source) return;

    let draw: Draw | null = null;

    const startPolygon = () => {
      draw = new Draw({ source, type: "Polygon" });
      draw.on("drawend", (evt) => handleDrawEnd(evt.feature));
    };
    const startRectangle = () => {
      draw = new Draw({ source, type: "Circle", geometryFunction: createBox() });
      draw.on("drawend", (evt) => handleDrawEnd(evt.feature));
    };
    const startCircle = () => {
      draw = new Draw({ source, type: "Circle" });
      draw.on("drawend", (evt) => handleDrawEnd(evt.feature));
    };
    const startLine = () => {
      draw = new Draw({ source, type: "LineString" });
      draw.on("drawend", (evt) => handleDrawEnd(evt.feature));
    };
    const startPoint = () => {
      draw = new Draw({ source, type: "Point" });
      draw.on("drawend", (evt) => handleDrawEnd(evt.feature));
    };
    const startDistance = () => {
      const measureSource = measureSourceRef.current;
      draw = new Draw({ source: measureSource || source, type: "LineString" });
      draw.on("drawstart", () => measureSource?.clear());
      draw.on("drawend", (evt) => {
        const geom = evt.feature.getGeometry() as any;
        const length = geom.getLength();
        let display = "";
        if (length > 1000) display = `${(length / 1000).toFixed(2)} km`;
        else display = `${length.toFixed(1)} m`;
        setMeasurementResult(display);
      });
    };
    const startArea = () => {
      const measureSource = measureSourceRef.current;
      draw = new Draw({ source: measureSource || source, type: "Polygon" });
      draw.on("drawstart", () => measureSource?.clear());
      draw.on("drawend", (evt) => {
        const geom = evt.feature.getGeometry() as any;
        const area = geom.getArea();
        let display = "";
        if (area > 1000000) display = `${(area / 1000000).toFixed(2)} km²`;
        else display = `${area.toFixed(1)} m²`;
        setMeasurementResult(display);
      });
    };
    const startBearing = () => {
      const measureSource = measureSourceRef.current;
      draw = new Draw({ source: measureSource || source, type: "LineString" });
      draw.on("drawstart", () => measureSource?.clear());
      draw.on("drawend", (evt) => {
        const coords = (evt.feature.getGeometry() as any).getCoordinates();
        if (coords.length >= 2) {
          const start = toLonLat(coords[0]);
          const end = toLonLat(coords[coords.length - 1]);
          const dx = end[0] - start[0];
          const dy = end[1] - start[1];
          let bearing = (Math.atan2(dx, dy) * 180) / Math.PI;
          if (bearing < 0) bearing += 360;
          setMeasurementResult(`${bearing.toFixed(1)}°`);
        }
      });
    };

    switch (activeTool) {
      case "draw_polygon":
        startPolygon();
        break;
      case "draw_rectangle":
        startRectangle();
        break;
      case "draw_circle":
        startCircle();
        break;
      case "draw_line":
        startLine();
        break;
      case "draw_point":
        startPoint();
        break;
      case "measure_distance":
        startDistance();
        break;
      case "measure_area":
        startArea();
        break;
      case "measure_bearing":
        startBearing();
        break;
      default:
        return;
    }

    if (!draw) return;
    map.addInteraction(draw);
    drawInteractionRef.current = draw;
  }, [activeTool, handleDrawEnd, setMeasurementResult]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    map.getView().setRotation(mapRotation);
  }, [mapRotation]);

  // ============================================================
  // Zoom-to selected layer / AOI
  // ============================================================

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (selectedLayerId) {
      const olLayer = layerObjectsRef.current.get(selectedLayerId);
      if (olLayer instanceof VectorLayer) {
        const extent = olLayer.getSource()?.getExtent();
        if (extent && !isEmpty(extent)) {
          map.getView().fit(extent, { duration: 400, maxZoom: 16 });
          return;
        }
      }
    }

    if (selectedObjectId && selectedObjectType === "aoi") {
      const aoi = aois.find((a) => a.id === selectedObjectId);
      if (aoi) {
        try {
          const geometry = new GeoJSONFormat().readGeometry(JSON.parse(aoi.geometry), {
            featureProjection: "EPSG:3857",
            dataProjection: "EPSG:4326",
          });
          const extent = geometry.getExtent();
          if (extent && !isEmpty(extent)) {
            map.getView().fit(extent, { duration: 400, maxZoom: 16 });
          }
        } catch (e) {
          console.warn("Zoom-to AOI failed", e);
        }
      }
    }
  }, [selectedLayerId, selectedObjectId, selectedObjectType, aois]);

  return (
    <div
      ref={mapRef}
      className="w-full h-full"
      style={{ background: "#1e293b" }}
    />
  );
}
