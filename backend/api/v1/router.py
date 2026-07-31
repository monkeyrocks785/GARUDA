from fastapi import APIRouter

from api.v1.aoi import router as aoi_router
from api.v1.health import router as health_router
from api.v1.import_export import router as import_export_router
from api.v1.layers import router as layers_router
from api.v1.map_state import router as map_state_router
from api.v1.projects import router as projects_router
from api.v1.workspace import router as workspace_router
from assets.api import router as assets_router
from comparison_engine.api import router as comparisons_router
from data_engine.api import router as datasets_router
from growth_engine.api import router as growth_router
from intelligence_engine.api import router as intelligence_router
from knowledge_engine.api import router as knowledge_router
from query_engine.api import router as queries_router
from rules_engine.api import router as rules_router
from mission_engine.api import router as missions_router
from pipeline_engine.api import router as pipelines_router
from raster_engine.api import router as rasters_router
from registration_engine.api import router as registrations_router
from temporal_engine.api import router as timelines_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(aoi_router)
api_router.include_router(layers_router)
api_router.include_router(import_export_router)
api_router.include_router(map_state_router)
api_router.include_router(workspace_router)
api_router.include_router(datasets_router)
api_router.include_router(assets_router)
api_router.include_router(pipelines_router)
api_router.include_router(missions_router)
api_router.include_router(timelines_router)
api_router.include_router(rasters_router)
api_router.include_router(registrations_router)
api_router.include_router(comparisons_router)
api_router.include_router(growth_router)
api_router.include_router(intelligence_router)
api_router.include_router(knowledge_router)
api_router.include_router(queries_router)
api_router.include_router(rules_router)
