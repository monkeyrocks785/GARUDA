import { useEffect, useRef, useCallback } from "react";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import XYZ from "ol/source/XYZ";
import { fromLonLat, toLonLat } from "ol/proj";
import { Draw, Modify, Snap } from "ol/interaction";
import { createBox } from "ol/interaction/Draw";
import { Circle as CircleStyle, Fill, Stroke, Style } from "ol/style";
import { ScaleLine } from "ol/control";
import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import { BASEMAP_URLS } from "../../types/workspace";

interface MapCanvasProps {
  projectId: string | undefined;
}

function createBlankGridSource(): XYZ {
  return new XYZ({
    url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQABNjN9GQAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAAA0lEQVQI12P4z8BQDwAEgAF/QualzQAAAABJRU5ErkJggg==",
    crossOrigin: "anonymous",
    maxZoom: 0,
  });
}

function createStyleFunction() {
  return (feature: any) => {
    const geomType = feature.getGeometry().getType();
    const fillColor = "rgba(66, 153, 225, 0.2)";
    const strokeColor = "#4299e1";
    const styles: Style[] = [];

    if (geomType === "Point") {
      styles.push(
        new Style({
          image: new CircleStyle({
            radius: 6,
            fill: new Fill({ color: strokeColor }),
            stroke: new Stroke({ color: "#ffffff", width: 2 }),
          }),
        })
      );
    } else {
      styles.push(
        new Style({
          fill: new Fill({ color: fillColor }),
          stroke: new Stroke({ color: strokeColor, width: 2 }),
        })
      );
    }
    return styles;
  };
}

export default function MapCanvas({ projectId: _projectId }: MapCanvasProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<Map | null>(null);
  const drawInteractionRef = useRef<Draw | null>(null);
  const modifyInteractionRef = useRef<Modify | null>(null);
  const snapInteractionRef = useRef<Snap | null>(null);
  const vectorSourceRef = useRef<VectorSource | null>(null);

  const {
    zoom,
    center,
    mapRotation,
    basemap,
    activeTool,
    setZoom,
    setCenter,
    setMousePosition,
    setMeasurementResult,
    pushUndo,
    setSelectedObjectId,
    setSelectedObjectType,
  } = useWorkspaceStore();

  const handlePointerMove = useCallback(
    (evt: any) => {
      if (evt.coordinate) {
        const lonLat = toLonLat(evt.coordinate);
        setMousePosition([lonLat[1], lonLat[0]]);
      }
    },
    [setMousePosition]
  );

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const vectorSource = new VectorSource();
    vectorSourceRef.current = vectorSource;

    const vectorLayer = new VectorLayer({
      source: vectorSource,
      style: createStyleFunction(),
    });

    let tileSource: any;
    const basemapUrl = BASEMAP_URLS[basemap];
    if (!basemapUrl) {
      tileSource = createBlankGridSource();
    } else {
      tileSource = new XYZ({ url: basemapUrl });
    }

    const tileLayer = new TileLayer({ source: tileSource });

    const scaleLine = new ScaleLine({ units: "metric" });

    const map = new Map({
      target: mapRef.current,
      layers: [tileLayer, vectorLayer],
      view: new View({
        center: fromLonLat(center),
        zoom: zoom,
        rotation: mapRotation,
        minZoom: 0,
        maxZoom: 24,
      }),
      controls: [scaleLine],
    });

    map.on("pointermove", handlePointerMove);

    map.on("click", (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature) {
        setSelectedObjectId(feature.get("id") || null);
        setSelectedObjectType(feature.get("type") || "feature");
      } else {
        setSelectedObjectId(null);
        setSelectedObjectType(null);
      }
    });

    map.on("moveend", () => {
      const view = map.getView();
      const c = toLonLat(view.getCenter() || [0, 0]);
      setZoom(view.getZoom() || 2);
      setCenter([c[1], c[0]]);
    });

    const modify = new Modify({ source: vectorSource });
    map.addInteraction(modify);
    modifyInteractionRef.current = modify;

    const snap = new Snap({ source: vectorSource });
    map.addInteraction(snap);
    snapInteractionRef.current = snap;

    mapInstanceRef.current = map;

    return () => {
      map.setTarget(undefined);
      mapInstanceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const layers = map.getLayers().getArray();
    const tileLayer = layers[0] as TileLayer<XYZ>;
    if (!tileLayer) return;

    let newSource: any;
    const basemapUrl = BASEMAP_URLS[basemap];
    if (!basemapUrl) {
      newSource = createBlankGridSource();
    } else {
      newSource = new XYZ({ url: basemapUrl });
    }
    tileLayer.setSource(newSource);
  }, [basemap]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (drawInteractionRef.current) {
      map.removeInteraction(drawInteractionRef.current);
      drawInteractionRef.current = null;
    }

    const source = vectorSourceRef.current;
    if (!source) return;

    if (activeTool === "draw_polygon") {
      const draw = new Draw({ source, type: "Polygon" });
      draw.on("drawend", (evt) => {
        const feature = evt.feature;
        feature.set("type", "drawing");
        feature.set("id", crypto.randomUUID());
        pushUndo({ type: "add", feature: feature.getProperties() });
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "draw_rectangle") {
      const draw = new Draw({
        source,
        type: "Circle",
        geometryFunction: createBox(),
      });
      draw.on("drawend", (evt) => {
        const feature = evt.feature;
        feature.set("type", "drawing");
        feature.set("id", crypto.randomUUID());
        pushUndo({ type: "add", feature: feature.getProperties() });
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "draw_circle") {
      const draw = new Draw({ source, type: "Circle" });
      draw.on("drawend", (evt) => {
        const feature = evt.feature;
        feature.set("type", "drawing");
        feature.set("id", crypto.randomUUID());
        pushUndo({ type: "add", feature: feature.getProperties() });
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "draw_line") {
      const draw = new Draw({ source, type: "LineString" });
      draw.on("drawend", (evt) => {
        const feature = evt.feature;
        feature.set("type", "drawing");
        feature.set("id", crypto.randomUUID());
        pushUndo({ type: "add", feature: feature.getProperties() });
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "draw_point") {
      const draw = new Draw({ source, type: "Point" });
      draw.on("drawend", (evt) => {
        const feature = evt.feature;
        feature.set("type", "drawing");
        feature.set("id", crypto.randomUUID());
        pushUndo({ type: "add", feature: feature.getProperties() });
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "measure_distance") {
      const draw = new Draw({ source, type: "LineString" });
      draw.on("drawstart", () => {
        source.clear();
      });
      draw.on("drawend", (evt) => {
        const geom = evt.feature.getGeometry() as any;
        const length = geom.getLength();
        let display = "";
        if (length > 1000) {
          display = `${(length / 1000).toFixed(2)} km`;
        } else {
          display = `${length.toFixed(1)} m`;
        }
        setMeasurementResult(display);
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "measure_area") {
      const draw = new Draw({
        source,
        type: "Polygon",
      });
      draw.on("drawstart", () => {
        source.clear();
      });
      draw.on("drawend", (evt) => {
        const geom = evt.feature.getGeometry() as any;
        const area = geom.getArea();
        let display = "";
        if (area > 1000000) {
          display = `${(area / 1000000).toFixed(2)} km²`;
        } else {
          display = `${area.toFixed(1)} m²`;
        }
        setMeasurementResult(display);
      });
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (activeTool === "measure_bearing") {
      const draw = new Draw({ source, type: "LineString" });
      draw.on("drawstart", () => {
        source.clear();
      });
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
      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    }
  }, [activeTool, pushUndo, setMeasurementResult]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    map.getView().setRotation(mapRotation);
  }, [mapRotation]);

  return (
    <div ref={mapRef} className="w-full h-full" style={{ background: "#1e293b" }} />
  );
}
