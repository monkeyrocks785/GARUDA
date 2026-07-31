"""Pipeline API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from pipeline_engine.services import PipelineService

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


# ============================================================
# Pydantic Schemas
# ============================================================


class NodeConfig(BaseModel):
    name: str
    description: str | None = None
    node_type: str = "custom"
    inputs: dict = {}
    parameters: dict = {}
    depends_on: list[str] = []
    max_retries: int = 3


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_id: str | None = None
    owner: str | None = None
    nodes: list[NodeConfig] = []


class PipelineResponse(BaseModel):
    id: str
    project_id: str | None
    name: str
    description: str | None
    version: int
    status: str
    progress: float
    owner: str | None
    priority: int
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    execution_time_ms: int
    error_message: str | None
    created_at: datetime
    modified_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class NodeResponse(BaseModel):
    id: str
    pipeline_id: str
    name: str
    description: str | None
    node_type: str
    status: str
    inputs_json: str | None
    outputs_json: str | None
    parameters_json: str | None
    depends_on_json: str | None
    sort_order: int
    retry_count: int
    max_retries: int
    execution_time_ms: int
    error_message: str | None
    result_json: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    id: str
    pipeline_id: str
    node_id: str | None
    action: str
    details: str | None
    performed_by: str | None
    execution_time_ms: int
    timestamp: datetime

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    id: str
    pipeline_id: str
    node_id: str | None
    level: str
    message: str
    details: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


class QueueEntryResponse(BaseModel):
    id: str
    pipeline_id: str
    status: str
    priority: int
    position: int
    worker_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class PipelineListResponse(BaseModel):
    pipelines: list[PipelineResponse]
    total: int
    offset: int
    limit: int


class QueueStatusResponse(BaseModel):
    waiting: int
    running: int
    paused: int
    completed: int
    failed: int
    cancelled: int
    total: int


class NodeTypeResponse(BaseModel):
    type: str
    name: str
    description: str


class StatsResponse(BaseModel):
    total: int
    pending: int
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int
    paused: int


# ============================================================
# Pipeline Endpoints
# ============================================================


@router.post("", response_model=PipelineResponse, status_code=201)
async def create_pipeline(request: PipelineCreate, db: Session = Depends(get_db)):
    """Create a new pipeline."""
    service = PipelineService(db)
    nodes_config = [n.model_dump() for n in request.nodes]
    pipeline = service.create_pipeline(
        name=request.name,
        project_id=request.project_id,
        description=request.description,
        owner=request.owner,
        nodes_config=nodes_config,
    )
    return PipelineResponse.model_validate(pipeline)


@router.get("", response_model=PipelineListResponse)
async def list_pipelines(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List pipelines."""
    service = PipelineService(db)
    pipelines, total = service.list_pipelines(project_id, status, offset, limit)
    return PipelineListResponse(
        pipelines=[PipelineResponse.model_validate(p) for p in pipelines],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get pipeline statistics."""
    service = PipelineService(db)
    return StatsResponse(**service.get_pipeline_stats(project_id))


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(db: Session = Depends(get_db)):
    """Get queue status."""
    service = PipelineService(db)
    return QueueStatusResponse(**service.get_queue_status())


@router.get("/queue", response_model=list[QueueEntryResponse])
async def list_queue(db: Session = Depends(get_db)):
    """List all queue entries."""
    service = PipelineService(db)
    return [QueueEntryResponse.model_validate(e) for e in service.get_all_queued()]


@router.get("/node-types", response_model=list[NodeTypeResponse])
async def get_node_types(db: Session = Depends(get_db)):
    """Get available node types."""
    service = PipelineService(db)
    return [NodeTypeResponse(**nt) for nt in service.get_available_node_types()]


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Get a pipeline."""
    service = PipelineService(db)
    pipeline = service.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return PipelineResponse.model_validate(pipeline)


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Delete a pipeline."""
    service = PipelineService(db)
    if not service.delete_pipeline(pipeline_id):
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"success": True}


@router.post("/{pipeline_id}/start")
async def start_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Start pipeline execution."""
    service = PipelineService(db)
    result = service.start_pipeline(pipeline_id)
    return result


@router.post("/{pipeline_id}/pause")
async def pause_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Pause a running pipeline."""
    service = PipelineService(db)
    if not service.pause_pipeline(pipeline_id):
        raise HTTPException(status_code=400, detail="Cannot pause pipeline")
    return {"success": True}


@router.post("/{pipeline_id}/resume")
async def resume_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Resume a paused pipeline."""
    service = PipelineService(db)
    if not service.resume_pipeline(pipeline_id):
        raise HTTPException(status_code=400, detail="Cannot resume pipeline")
    return {"success": True}


@router.post("/{pipeline_id}/cancel")
async def cancel_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Cancel a pipeline."""
    service = PipelineService(db)
    if not service.cancel_pipeline(pipeline_id):
        raise HTTPException(status_code=400, detail="Cannot cancel pipeline")
    return {"success": True}


@router.post("/{pipeline_id}/retry")
async def retry_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Retry a failed pipeline."""
    service = PipelineService(db)
    if not service.retry_pipeline(pipeline_id):
        raise HTTPException(status_code=400, detail="Cannot retry pipeline")
    return {"success": True}


@router.post("/{pipeline_id}/enqueue")
async def enqueue_pipeline(pipeline_id: str, priority: int = Query(0), db: Session = Depends(get_db)):
    """Add pipeline to queue."""
    service = PipelineService(db)
    entry = service.enqueue_pipeline(pipeline_id, priority)
    if not entry:
        raise HTTPException(status_code=400, detail="Cannot enqueue pipeline")
    return {"success": True, "position": entry.position}


@router.delete("/{pipeline_id}/queue")
async def dequeue_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Remove pipeline from queue."""
    service = PipelineService(db)
    if not service.dequeue_pipeline(pipeline_id):
        raise HTTPException(status_code=404, detail="Not in queue")
    return {"success": True}


@router.get("/{pipeline_id}/nodes", response_model=list[NodeResponse])
async def get_pipeline_nodes(pipeline_id: str, db: Session = Depends(get_db)):
    """Get pipeline nodes."""
    service = PipelineService(db)
    nodes = service.get_pipeline_nodes(pipeline_id)
    return [NodeResponse.model_validate(n) for n in nodes]


@router.get("/{pipeline_id}/history", response_model=list[HistoryResponse])
async def get_pipeline_history(
    pipeline_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get pipeline history."""
    service = PipelineService(db)
    history = service.get_pipeline_history(pipeline_id, limit)
    return [HistoryResponse.model_validate(h) for h in history]


@router.get("/{pipeline_id}/logs", response_model=list[LogResponse])
async def get_pipeline_logs(
    pipeline_id: str,
    node_id: str | None = Query(None),
    level: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get pipeline logs."""
    service = PipelineService(db)
    logs = service.get_pipeline_logs(pipeline_id, node_id, level, limit)
    return [LogResponse.model_validate(l) for l in logs]
