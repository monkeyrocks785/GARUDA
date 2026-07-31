"""Export Service.

Exports query results in various formats: CSV, GeoJSON, KML, PDF (summary).
"""

import csv
import io
import json
import logging
from datetime import datetime

logger = logging.getLogger("garuda.query.export")


class ExportService:
    """Exports query results to various formats."""

    @staticmethod
    def export_csv(items: list[dict]) -> str:
        """Export results as CSV string."""
        output = io.StringIO()
        if not items:
            return ""

        field_names = [
            "id", "entity_type", "name", "description", "status",
            "confidence", "observation_count", "first_observed_at",
            "last_observed_at", "favorite", "archived", "created_at",
            "modified_at", "analyst_notes",
        ]
        present_fields = [f for f in field_names if f in items[0]]

        writer = csv.DictWriter(output, fieldnames=present_fields, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow(item)

        result = output.getvalue()
        output.close()
        return result

    @staticmethod
    def export_geojson(items: list[dict]) -> str:
        """Export results as GeoJSON FeatureCollection."""
        features = []
        for item in items:
            geometry = None
            geom_str = item.get("geometry_json")
            if geom_str:
                try:
                    geometry = json.loads(geom_str)
                except (json.JSONDecodeError, TypeError):
                    pass

            if geometry is None:
                cx = item.get("centroid_x")
                cy = item.get("centroid_y")
                if cx is not None and cy is not None:
                    geometry = {
                        "type": "Point",
                        "coordinates": [cx, cy],
                    }

            properties = {k: v for k, v in item.items()
                          if k not in ("geometry_json", "centroid_x", "centroid_y",
                                       "bbox_min_x", "bbox_min_y",
                                       "bbox_max_x", "bbox_max_y")}

            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            }
            if item.get("bbox_min_x") is not None:
                feature["bbox"] = [
                    item["bbox_min_x"], item["bbox_min_y"],
                    item["bbox_max_x"], item["bbox_max_y"],
                ]
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }
        return json.dumps(geojson, indent=2, default=str)

    @staticmethod
    def export_kml(items: list[dict]) -> str:
        """Export results as KML string."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            "  <Document>",
            f"    <name>GARUDA Query Results</name>",
            f"    <description>Exported {len(items)} entities</description>",
        ]

        for item in items:
            name = item.get("name", "Unknown")
            etype = item.get("entity_type", "")
            desc = item.get("description", "") or ""

            fold_parts = []
            coord_str = ""
            geom_str = item.get("geometry_json")
            if geom_str:
                try:
                    geom = json.loads(geom_str)
                    if geom.get("type") == "Point":
                        coords = geom["coordinates"]
                        coord_str = f"{coords[0]},{coords[1]},0"
                except (json.JSONDecodeError, TypeError):
                    pass

            if not coord_str:
                cx = item.get("centroid_x")
                cy = item.get("centroid_y")
                if cx is not None and cy is not None:
                    coord_str = f"{cx},{cy},0"

            lines.append("    <Placemark>")
            lines.append(f"      <name>{name}</name>")
            lines.append(f"      <description>{desc}</description>")
            if coord_str:
                lines.append("      <Point>")
                lines.append(f"        <coordinates>{coord_str}</coordinates>")
                lines.append("      </Point>")
            lines.append("    </Placemark>")

        lines.append("  </Document>")
        lines.append("</kml>")
        return "\n".join(lines)

    @staticmethod
    def export_pdf_summary(items: list[dict]) -> str:
        """Export a plain-text summary report (PDF placeholder).
        
        In a production environment, this would generate an actual PDF
        using a library like reportlab or weasyprint.
        """
        lines = [
            "=" * 60,
            "GARUDA Query Results Summary",
            "=" * 60,
            f"Generated: {datetime.utcnow().isoformat()}",
            f"Total Results: {len(items)}",
            "",
            "-" * 60,
            "Entity Summary",
            "-" * 60,
        ]

        type_counts: dict[str, int] = {}
        for item in items:
            etype = item.get("entity_type", "unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1

        for etype, count in sorted(type_counts.items()):
            lines.append(f"  {etype}: {count}")

        lines.extend([
            "",
            "-" * 60,
            "Entity Details",
            "-" * 60,
        ])

        for item in items:
            lines.extend([
                "",
                f"  Name: {item.get('name', 'N/A')}",
                f"  Type: {item.get('entity_type', 'N/A')}",
                f"  Confidence: {item.get('confidence', 'N/A')}",
                f"  Status: {item.get('status', 'N/A')}",
                f"  Observations: {item.get('observation_count', 0)}",
            ])
            desc = item.get("description")
            if desc:
                lines.append(f"  Description: {desc}")

        return "\n".join(lines)

    @staticmethod
    def export(
        items: list[dict],
        format: str = "csv",
    ) -> str:
        """Export results in the specified format."""
        fmt = format.lower().strip()
        if fmt == "csv":
            return ExportService.export_csv(items)
        elif fmt == "geojson":
            return ExportService.export_geojson(items)
        elif fmt == "kml":
            return ExportService.export_kml(items)
        elif fmt == "pdf":
            return ExportService.export_pdf_summary(items)
        else:
            raise ValueError(f"Unsupported export format: {format}. "
                             f"Supported: csv, geojson, kml, pdf")
