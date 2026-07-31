"""File export service for KML and GeoJSON."""

import json

from loguru import logger
from shapely.geometry import shape

from geo.geometry_service import GeometryService


class FileExportService:
    """Service for exporting geospatial files."""

    def __init__(self):
        self.geometry_service = GeometryService()

    def export_geojson(
        self,
        geometries: list[dict],
        names: list[str] | None = None,
    ) -> str:
        """Export geometries to GeoJSON.

        Args:
            geometries: List of GeoJSON geometry dictionaries.
            names: Optional list of feature names.

        Returns:
            GeoJSON string.
        """
        features = []
        for i, geom in enumerate(geometries):
            feature = {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "name": names[i] if names and i < len(names) else f"Feature {i + 1}",
                },
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        logger.info("Exported GeoJSON", feature_count=len(features))

        return json.dumps(geojson, indent=2)

    def export_kml(
        self,
        geometries: list[dict],
        names: list[str] | None = None,
        document_name: str = "GARUDA Export",
    ) -> str:
        """Export geometries to KML.

        Args:
            geometries: List of GeoJSON geometry dictionaries.
            names: Optional list of feature names.
            document_name: KML document name.

        Returns:
            KML string.
        """
        try:
            from lxml import etree

            # Create KML namespace
            kml_ns = "http://www.opengis.net/kml/2.2"
            nsmap = {None: kml_ns}

            kml = etree.Element("kml", nsmap=nsmap)
            document = etree.SubElement(kml, "Document")
            etree.SubElement(document, "name").text = document_name

            for i, geom in enumerate(geometries):
                name = names[i] if names and i < len(names) else f"Feature {i + 1}"

                placemark = etree.SubElement(document, "Placemark")
                etree.SubElement(placemark, "name").text = name

                # Convert GeoJSON geometry to KML geometry
                geom_obj = shape(geom)
                geom_type = geom_obj.geom_type

                if geom_type == "Point":
                    point = etree.SubElement(placemark, "Point")
                    coords = etree.SubElement(point, "coordinates")
                    coords.text = f"{geom_obj.x},{geom_obj.y},0"

                elif geom_type == "LineString":
                    line = etree.SubElement(placemark, "LineString")
                    coords = etree.SubElement(line, "coordinates")
                    coords.text = " ".join(
                        [f"{x},{y},0" for x, y in geom_obj.coords]
                    )

                elif geom_type in ["Polygon", "MultiPolygon"]:
                    polygon = etree.SubElement(placemark, "Polygon")
                    outer = etree.SubElement(polygon, "outerBoundaryIs")
                    ring = etree.SubElement(outer, "LinearRing")
                    coords = etree.SubElement(ring, "coordinates")

                    if geom_type == "Polygon":
                        rings = [geom_obj.exterior] + list(geom_obj.interiors)
                    else:
                        rings = []
                        for poly in geom_obj.geoms:
                            rings.append(poly.exterior)
                            rings.extend(poly.interiors)

                    all_coords = []
                    for ring in rings:
                        all_coords.extend(
                            [f"{x},{y},0" for x, y in ring.coords]
                        )
                    coords.text = " ".join(all_coords)

            kml_string = etree.tostring(kml, pretty_print=True, xml_declaration=True, encoding="UTF-8")

            logger.info("Exported KML", feature_count=len(geometries))

            return kml_string.decode("utf-8")

        except Exception as e:
            raise ValueError(f"Failed to export KML: {str(e)}")
