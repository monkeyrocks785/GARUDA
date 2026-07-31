"""Pipeline Nodes for Intelligence Analysis Engine.

Integrates with the existing Pipeline Engine.
"""

import json
import logging
import time

from pipeline_engine.nodes import BaseNode, register_node

logger = logging.getLogger("garuda.intelligence.pipeline_nodes")


class IntelligenceRunAnalysisNode(BaseNode):
    """Pipeline node: run AI analysis on input data."""

    node_type = "intelligence_run_analysis"

    def validate_inputs(self) -> bool:
        return "model_id" in self.inputs and "input_path" in self.inputs

    def execute(self) -> dict:
        from intelligence_engine.services.analysis_service import AnalysisService

        model_id = self.inputs["model_id"]
        input_path = self.inputs["input_path"]
        project_id = self.inputs.get("project_id", "")
        name = self.parameters.get("name", "Pipeline Analysis")
        confidence = self.parameters.get("confidence_threshold", 0.5)
        iou = self.parameters.get("iou_threshold", 0.45)
        device = self.parameters.get("device", "cpu")

        logger.info(f"Running analysis: model={model_id}, input={input_path}")

        job = AnalysisService.create_job(
            db=self.db,
            project_id=project_id,
            model_id=model_id,
            name=name,
            input_path=input_path,
            confidence_threshold=confidence,
            iou_threshold=iou,
            device=device,
        )

        job = AnalysisService.run_job(db=self.db, job_id=job.id)

        return {
            "job_id": job.id,
            "status": job.status,
            "detection_count": job.detection_count,
            "output_path": job.output_path,
            "execution_time_ms": job.execution_time_ms,
        }


class IntelligenceLoadModelNode(BaseNode):
    """Pipeline node: load an AI model."""

    node_type = "intelligence_load_model"

    def validate_inputs(self) -> bool:
        return "model_id" in self.inputs

    def execute(self) -> dict:
        from intelligence_engine.services.model_registry import ModelRegistry

        model_id = self.inputs["model_id"]
        logger.info(f"Loading model: {model_id}")

        model = ModelRegistry.load_model(self.db, model_id)

        return {
            "model_id": model.id,
            "model_name": model.name,
            "status": model.status,
            "is_loaded": model.is_loaded,
        }


class IntelligenceUnloadModelNode(BaseNode):
    """Pipeline node: unload an AI model."""

    node_type = "intelligence_unload_model"

    def validate_inputs(self) -> bool:
        return "model_id" in self.inputs

    def execute(self) -> dict:
        from intelligence_engine.services.model_registry import ModelRegistry

        model_id = self.inputs["model_id"]
        logger.info(f"Unloading model: {model_id}")

        model = ModelRegistry.unload_model(self.db, model_id)

        return {
            "model_id": model.id,
            "status": model.status,
            "is_loaded": model.is_loaded,
        }


class IntelligenceGetResultsNode(BaseNode):
    """Pipeline node: retrieve detection results."""

    node_type = "intelligence_get_results"

    def validate_inputs(self) -> bool:
        return "job_id" in self.inputs

    def execute(self) -> dict:
        from intelligence_engine.services.analysis_service import AnalysisService

        job_id = self.inputs["job_id"]
        class_filter = self.parameters.get("class_name")
        min_confidence = self.parameters.get("min_confidence")

        logger.info(f"Getting results for job: {job_id}")

        detections = AnalysisService.get_job_detections(
            self.db, job_id,
            class_name=class_filter,
            min_confidence=min_confidence,
        )

        return {
            "job_id": job_id,
            "detection_count": len(detections),
            "detections": [d.to_dict() for d in detections],
        }


# Register all intelligence nodes
register_node("intelligence_run_analysis", IntelligenceRunAnalysisNode)
register_node("intelligence_load_model", IntelligenceLoadModelNode)
register_node("intelligence_unload_model", IntelligenceUnloadModelNode)
register_node("intelligence_get_results", IntelligenceGetResultsNode)

logger.info("Intelligence pipeline nodes registered")
