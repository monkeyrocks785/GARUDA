"""Comparison pipeline nodes for the GARUDA pipeline engine."""

import json
import os

from comparison_engine.config import DEFAULT_COMPARISON_MODE, DEFAULT_DIFFERENCE_TYPE
from comparison_engine.services.difference_service import DifferenceService
from comparison_engine.services.export_service import ExportService
from comparison_engine.services.session_service import SessionService
from pipeline_engine.nodes import BaseNode, register_node


@register_node(
    node_id="comparison_create_session",
    name="Create Comparison Session",
    description="Create a new temporal comparison session with aligned datasets",
    category="comparison",
    inputs=["dataset_paths", "name"],
    outputs=["session_id", "session"],
)
class ComparisonCreateSessionNode(BaseNode):
    """Create a comparison session as a pipeline step."""

    def execute(self, inputs, config, context):
        dataset_paths = inputs.get("dataset_paths", [])
        name = inputs.get("name", "Pipeline Comparison")
        mode = config.get("mode", DEFAULT_COMPARISON_MODE)

        db = context.get("db")
        project_id = config.get("project_id", "")

        session = SessionService.create_session(
            db=db,
            project_id=project_id,
            name=name,
            dataset_paths=dataset_paths,
            mode=mode,
        )

        return {
            "session_id": session.id,
            "session": SessionService.to_dict(session),
        }


@register_node(
    node_id="comparison_generate_difference",
    name="Generate Difference Layer",
    description="Generate a difference visualization between two aligned datasets",
    category="comparison",
    inputs=["file_a", "file_b"],
    outputs=["difference_path", "statistics"],
)
class ComparisonGenerateDifferenceNode(BaseNode):
    """Generate difference visualization as a pipeline step."""

    def execute(self, inputs, config, context):
        file_a = inputs.get("file_a")
        file_b = inputs.get("file_b")

        if not file_a or not os.path.exists(file_a):
            raise ValueError(f"File A not found: {file_a}")
        if not file_b or not os.path.exists(file_b):
            raise ValueError(f"File B not found: {file_b}")

        diff_type = config.get("difference_type", DEFAULT_DIFFERENCE_TYPE)
        threshold = config.get("threshold", 0.1)
        output_dir = config.get("output_dir")

        result = DifferenceService.generate_difference_preview(
            file_a=file_a,
            file_b=file_b,
            diff_type=diff_type,
            output_dir=output_dir,
            threshold=threshold,
        )

        return {
            "difference_path": result.get("output_path"),
            "statistics": result,
        }


@register_node(
    node_id="comparison_export_session",
    name="Export Comparison",
    description="Export a comparison session to file",
    category="comparison",
    inputs=["session_id"],
    outputs=["export_path", "export_data"],
)
class ComparisonExportSessionNode(BaseNode):
    """Export a comparison session as a pipeline step."""

    def execute(self, inputs, config, context):
        session_id = inputs.get("session_id")
        if not session_id:
            raise ValueError("session_id is required")

        export_format = config.get("format", "json")
        export_scope = config.get("scope", "current_view")
        output_dir = config.get("output_dir")

        db = context.get("db")

        if export_format == "json":
            data = ExportService.export_session_json(
                db=db,
                session_id=session_id,
                output_dir=output_dir,
            )
            return {
                "export_path": data.get("output_path"),
                "export_data": data,
            }
        else:
            export = ExportService.create_export(
                db=db,
                session_id=session_id,
                name=config.get("name", "Pipeline Export"),
                export_format=export_format,
                export_scope=export_scope,
            )
            return {
                "export_path": export.output_path,
                "export_data": ExportService.to_dict(export),
            }


@register_node(
    node_id="comparison_analyze_histograms",
    name="Histogram Comparison",
    description="Compare histograms of two aligned datasets",
    category="comparison",
    inputs=["file_a", "file_b"],
    outputs=["histogram_data"],
)
class ComparisonAnalyzeHistogramsNode(BaseNode):
    """Compare histograms as a pipeline step."""

    def execute(self, inputs, config, context):
        file_a = inputs.get("file_a")
        file_b = inputs.get("file_b")

        if not file_a or not os.path.exists(file_a):
            raise ValueError(f"File A not found: {file_a}")
        if not file_b or not os.path.exists(file_b):
            raise ValueError(f"File B not found: {file_b}")

        bins = config.get("bins", 256)

        result = DifferenceService.compute_histogram_comparison(
            file_a, file_b, bins
        )

        return {"histogram_data": result}
