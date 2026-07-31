"""Model Registry Service.

Manages registration, loading, and lifecycle of AI models.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from config.settings import settings
from intelligence_engine.config import MODEL_STATUS, TASK_TYPES
from intelligence_engine.database.models import RegisteredModel
from intelligence_engine.plugins import discover_plugins, get_all_plugins, load_plugin
from intelligence_engine.modules.base import BaseModule
from intelligence_engine.utils import compute_file_checksum

logger = logging.getLogger("garuda.intelligence.model_registry")

# In-memory loaded model cache: {model_id: BaseModule}
_loaded_models: dict[str, BaseModule] = {}


class ModelRegistry:
    """Manages the lifecycle of AI models."""

    @staticmethod
    def register_model(
        db: Session,
        name: str,
        task: str,
        version: str = "1.0.0",
        description: str | None = None,
        author: str | None = None,
        license: str | None = None,
        framework: str = "pytorch",
        input_type: str = "raster",
        output_type: str = "detections",
        weights_path: str | None = None,
        class_names: list[str] | None = None,
        default_params: dict | None = None,
        config: dict | None = None,
        gpu_required: bool = False,
    ) -> RegisteredModel:
        """Register a new AI model in the system."""
        if task not in TASK_TYPES:
            raise ValueError(f"Invalid task type: {task}. Must be one of {TASK_TYPES}")

        model_id = str(uuid.uuid4())
        weights_checksum = None
        if weights_path and Path(weights_path).exists():
            weights_checksum = compute_file_checksum(weights_path)

        model = RegisteredModel(
            id=model_id,
            name=name,
            version=version,
            task=task,
            description=description,
            author=author,
            license=license,
            framework=framework,
            input_type=input_type,
            output_type=output_type,
            weights_path=weights_path,
            weights_checksum=weights_checksum,
            config_json=json.dumps(config) if config else None,
            class_names_json=json.dumps(class_names) if class_names else None,
            default_params_json=json.dumps(default_params) if default_params else None,
            gpu_required=gpu_required,
            status="registered",
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        logger.info(f"Registered model: {name} v{version} (task={task})")
        return model

    @staticmethod
    def load_model(db: Session, model_id: str) -> RegisteredModel:
        """Load a model into memory."""
        model = db.query(RegisteredModel).get(model_id)
        if model is None:
            raise ValueError(f"Model not found: {model_id}")

        if model.is_loaded and model_id in _loaded_models:
            logger.info(f"Model already loaded: {model.name}")
            return model

        try:
            # Discover plugins if not done
            discover_plugins()

            # Try to load via plugin system (exact name match first)
            plugin = load_plugin(
                f"{model.task}.{model.name}",
                config=json.loads(model.config_json) if model.config_json else None,
            )

            if plugin is None:
                # Fallback: find any plugin matching this task type
                all_plugins = get_all_plugins()
                for plugin_name, plugin_class in all_plugins.items():
                    if hasattr(plugin_class, "TASK_TYPE") and plugin_class.TASK_TYPE == model.task:
                        logger.info(f"Matched model {model.name} to plugin {plugin_name} by task type")
                        try:
                            plugin = plugin_class(
                                config=json.loads(model.config_json) if model.config_json else None,
                            )
                            break
                        except Exception:
                            continue

            if plugin is None:
                # Create a stub module for models without a real plugin
                plugin = _create_stub_module(model)

            if model.weights_path and Path(model.weights_path).exists():
                plugin.load(model.weights_path)
            else:
                plugin.initialize()

            _loaded_models[model_id] = plugin
            model.is_loaded = True
            model.status = "ready"
            model.last_loaded_at = datetime.utcnow()
            model.error_message = None
            db.commit()
            db.refresh(model)
            logger.info(f"Loaded model: {model.name} v{model.version}")
            return model

        except Exception as e:
            model.status = "error"
            model.error_message = str(e)
            db.commit()
            db.refresh(model)
            logger.error(f"Failed to load model {model.name}: {e}")
            raise ValueError(f"Failed to load model: {e}")

    @staticmethod
    def unload_model(db: Session, model_id: str) -> RegisteredModel:
        """Unload a model from memory."""
        model = db.query(RegisteredModel).get(model_id)
        if model is None:
            raise ValueError(f"Model not found: {model_id}")

        if model_id in _loaded_models:
            try:
                _loaded_models[model_id].shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down model: {e}")
            del _loaded_models[model_id]

        model.is_loaded = False
        model.status = "registered"
        db.commit()
        db.refresh(model)
        logger.info(f"Unloaded model: {model.name}")
        return model

    @staticmethod
    def get_model(db: Session, model_id: str) -> RegisteredModel | None:
        return db.query(RegisteredModel).get(model_id)

    @staticmethod
    def list_models(
        db: Session,
        task: str | None = None,
        status: str | None = None,
        loaded_only: bool = False,
    ) -> list[RegisteredModel]:
        q = db.query(RegisteredModel)
        if task:
            q = q.filter(RegisteredModel.task == task)
        if status:
            q = q.filter(RegisteredModel.status == status)
        if loaded_only:
            q = q.filter(RegisteredModel.is_loaded == True)
        return q.order_by(RegisteredModel.name).all()

    @staticmethod
    def delete_model(db: Session, model_id: str) -> None:
        """Delete a model registration."""
        model = db.query(RegisteredModel).get(model_id)
        if model is None:
            raise ValueError(f"Model not found: {model_id}")

        # Unload first
        if model_id in _loaded_models:
            ModelRegistry.unload_model(db, model_id)

        db.delete(model)
        db.commit()
        logger.info(f"Deleted model: {model.name}")

    @staticmethod
    def get_loaded_model(model_id: str) -> BaseModule | None:
        """Get a loaded model instance from the cache."""
        return _loaded_models.get(model_id)

    @staticmethod
    def to_dict(model: RegisteredModel) -> dict:
        return model.to_dict()


def _create_stub_module(model: RegisteredModel) -> BaseModule:
    """Create a stub module for models without a real plugin.

    This allows the system to track model metadata even without
    a concrete implementation. When predict() is called, it returns
    empty results.
    """
    from intelligence_engine.modules.base import BaseDetector

    class StubDetector(BaseDetector):
        def initialize(self):
            self._is_initialized = True

        def load(self, weights_path: str, **kwargs):
            self._is_initialized = True

        def predict(self, input_data, **kwargs):
            logger.warning(f"Stub model '{model.name}' predict() called - returning empty results")
            return []

        def detect(self, image, confidence_threshold=0.5, max_detections=1000, **kwargs):
            return []

        def postprocess(self, raw_output, **kwargs):
            return raw_output if isinstance(raw_output, list) else []

        def export(self, results, output_path, **kwargs):
            import json
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
            return output_path

        def metadata(self):
            return model.to_dict()

        def shutdown(self):
            self._is_initialized = False

    stub = StubDetector(config={"model_id": model.id, "model_name": model.name})
    stub.initialize()
    return stub
