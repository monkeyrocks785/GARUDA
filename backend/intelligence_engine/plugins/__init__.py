"""Plugin loader for AI model modules.

Discovers and loads model plugins from the detectors/, classifiers/, segmenters/ directories.
Each plugin module must expose a class that inherits from BaseDetector, BaseClassifier, or BaseSegmenter.
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Type

from intelligence_engine.modules.base import (
    BaseClassifier,
    BaseDetector,
    BaseFeatureExtractor,
    BaseModule,
    BaseSegmenter,
    BaseSimilaritySearch,
)

logger = logging.getLogger("garuda.intelligence.plugins")

# Plugin discovery paths
_PLUGIN_PACKAGES = [
    "intelligence_engine.detectors",
    "intelligence_engine.classifiers",
    "intelligence_engine.segmenters",
]

# Discovered plugins
_discovered_plugins: dict[str, Type[BaseModule]] = {}


def discover_plugins() -> dict[str, Type[BaseModule]]:
    """Discover all available plugins by scanning package directories."""
    global _discovered_plugins

    for package_name in _PLUGIN_PACKAGES:
        try:
            package = importlib.import_module(package_name)
            package_path = Path(package.__file__).parent

            for module_info in pkgutil.iter_modules([str(package_path)]):
                if module_info.name.startswith("_"):
                    continue
                try:
                    full_name = f"{package_name}.{module_info.name}"
                    module = importlib.import_module(full_name)

                    # Look for classes that inherit from BaseModule subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseModule)
                            and attr is not BaseModule
                            and not attr.__name__.startswith("Base")
                        ):
                            plugin_name = f"{package_name.split('.')[-1]}.{attr_name}"
                            _discovered_plugins[plugin_name] = attr
                            logger.info(f"Discovered plugin: {plugin_name}")

                except Exception as e:
                    logger.warning(
                        f"Failed to load plugin module {module_info.name}: {e}"
                    )
        except ImportError as e:
            logger.warning(f"Failed to import plugin package {package_name}: {e}")

    return _discovered_plugins


def get_plugin(name: str) -> Type[BaseModule] | None:
    """Get a specific plugin by name."""
    if not _discovered_plugins:
        discover_plugins()
    return _discovered_plugins.get(name)


def get_all_plugins() -> dict[str, Type[BaseModule]]:
    """Get all discovered plugins."""
    if not _discovered_plugins:
        discover_plugins()
    return dict(_discovered_plugins)


def list_plugin_names() -> list[str]:
    """List all available plugin names."""
    return list(get_all_plugins().keys())


def load_plugin(name: str, config: dict | None = None) -> BaseModule | None:
    """Instantiate a plugin by name."""
    plugin_class = get_plugin(name)
    if plugin_class is None:
        logger.error(f"Plugin not found: {name}")
        return None
    try:
        return plugin_class(config=config)
    except Exception as e:
        logger.error(f"Failed to instantiate plugin {name}: {e}")
        return None
