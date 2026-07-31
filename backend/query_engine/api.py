"""Intelligence Query Engine API.

Provides endpoints for structured querying over the GARUDA knowledge base.
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from query_engine.config import (
    ENTITY_TYPES,
    EVENT_TYPES,
    EXPORT_FORMATS,
    RELATIONSHIP_TYPES,
    RESULT_VIEW_MODES,
    REVIEW_STATUSES,
    SORT_DIRECTIONS,
    SPATIAL_OPERATORS,
    TEMPORAL_OPERATORS,
)
from query_engine.services.export_service import ExportService
from query_engine.services.history_service import QueryHistoryService
from query_engine.services.query_builder import QueryBuilder
from query_engine.services.query_executor import QueryExecutor

logger = logging.getLogger("garuda.query.api")

router = APIRouter(prefix="/queries", tags=["Intelligence Query Engine"])


# ── Request/Response Models ──────────────────────────────────────────────────


class SpatialFilterRequest(BaseModel):
    operator: str
    geometry: dict | None = None
    aoi_id: str | None = None
    buffer_meters: float | None = None
    distance_meters: float | None = None
    nearest_count: int | None = None
    bbox: list[float] | None = None


class TemporalFilterRequest(BaseModel):
    operator: str
    date: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    min_observations: int | None = None
    max_observations: int | None = None
    min_duration_days: int | None = None
    max_duration_days: int | None = None


class RelationshipFilterRequest(BaseModel):
    relationship_type: str
    target_entity_id: str | None = None
    target_entity_type: str | None = None
    bidirectional: bool = False


class QueryRequest(BaseModel):
    project_id: str
    entity_types: list[str] | None = None
    entity_name: str | None = None
    mission: str | None = None
    aoi: str | None = None
    event_type: str | None = None
    relationship: RelationshipFilterRequest | None = None
    confidence_min: float | None = None
    confidence_max: float | None = None
    review_status: str | None = None
    tags: list[str] | None = None
    classification: str | None = None
    analyst: str | None = None
    spatial: SpatialFilterRequest | None = None
    temporal: TemporalFilterRequest | None = None
    sort_by: str | None = None
    sort_direction: str | None = None
    max_results: int = 500
    page: int = 0
    page_size: int = 50
    enrich: bool = False


class SaveQueryRequest(BaseModel):
    project_id: str
    name: str
    description: str | None = None
    filters_json: str
    sort_by: str | None = None
    sort_direction: str = "asc"
    max_results: int = 500
    tags_json: str | None = None
    created_by: str | None = None


class UpdateQueryRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    filters_json: str | None = None
    sort_by: str | None = None
    sort_direction: str | None = None
    max_results: int | None = None
    favorite: bool | None = None
    pinned: bool | None = None
    tags_json: str | None = None


class ExportRequest(BaseModel):
    project_id: str
    format: str = "csv"
    filters: dict | None = None
    query_ids: list[str] | None = None


# ── Config Endpoint ──────────────────────────────────────────────────────────


@router.get("/config")
def get_config():
    """Get Intelligence Query Engine configuration."""
    return {
        "entity_types": ENTITY_TYPES,
        "event_types": EVENT_TYPES,
        "relationship_types": RELATIONSHIP_TYPES,
        "spatial_operators": SPATIAL_OPERATORS,
        "temporal_operators": TEMPORAL_OPERATORS,
        "review_statuses": REVIEW_STATUSES,
        "sort_directions": SORT_DIRECTIONS,
        "export_formats": EXPORT_FORMATS,
        "result_view_modes": RESULT_VIEW_MODES,
    }


# ── Query Execution ─────────────────────────────────────────────────────────


@router.post("/execute")
def execute_query(
    req: QueryRequest,
    use_cache: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Execute a structured query against the knowledge base."""
    try:
        query = QueryBuilder.build_base_query(
            project_id=req.project_id,
            entity_types=req.entity_types,
            entity_name=req.entity_name,
            mission=req.mission,
            aoi=req.aoi,
            event_type=req.event_type,
            confidence_min=req.confidence_min,
            confidence_max=req.confidence_max,
            review_status=req.review_status,
            tags=req.tags,
            classification=req.classification,
            analyst=req.analyst,
            page=req.page,
            page_size=req.page_size,
            max_results=req.max_results,
            sort_by=req.sort_by,
            sort_direction=req.sort_direction,
        )

        if req.relationship:
            QueryBuilder.add_relationship_filter(
                query,
                relationship_type=req.relationship.relationship_type,
                target_entity_id=req.relationship.target_entity_id,
                target_entity_type=req.relationship.target_entity_type,
                bidirectional=req.relationship.bidirectional,
            )

        if req.spatial:
            QueryBuilder.add_spatial_filter(
                query,
                operator=req.spatial.operator,
                geometry=req.spatial.geometry,
                aoi_id=req.spatial.aoi_id,
                buffer_meters=req.spatial.buffer_meters,
                distance_meters=req.spatial.distance_meters,
                nearest_count=req.spatial.nearest_count,
                bbox=req.spatial.bbox,
            )

        if req.temporal:
            QueryBuilder.add_temporal_filter(
                query,
                operator=req.temporal.operator,
                date=req.temporal.date,
                date_from=req.temporal.date_from,
                date_to=req.temporal.date_to,
                min_observations=req.temporal.min_observations,
                max_observations=req.temporal.max_observations,
                min_duration_days=req.temporal.min_duration_days,
                max_duration_days=req.temporal.max_duration_days,
            )

        query_hash = QueryBuilder.compute_query_hash(query)

        # Check cache
        if use_cache:
            cached = QueryHistoryService.get_cached_result(
                db, query_hash, req.project_id
            )
            if cached:
                return {
                    "items": json.loads(cached["results_json"]),
                    "total": cached["total_count"],
                    "page": req.page,
                    "page_size": req.page_size,
                    "execution_time_ms": cached["execution_time_ms"],
                    "cached": True,
                    "query_hash": query_hash,
                }

        # Execute
        if req.enrich:
            result = QueryExecutor.execute_and_enrich(db, query)
        else:
            result = QueryExecutor.execute_query(db, query)

        result["cached"] = False
        result["query_hash"] = query_hash

        # Cache results
        try:
            results_json = json.dumps(
                result["items"], default=str
            )
            QueryHistoryService.cache_result(
                db, query_hash, req.project_id,
                results_json, result["total"],
                result["execution_time_ms"],
            )
        except Exception as cache_err:
            logger.warning(f"Failed to cache result: {cache_err}")

        # Record history
        try:
            QueryHistoryService.record_execution(
                db, req.project_id,
                QueryBuilder.serialize_query(query),
                result["total"],
                result["execution_time_ms"],
            )
        except Exception as hist_err:
            logger.warning(f"Failed to record history: {hist_err}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute/raw")
def execute_raw_query(
    filters: dict,
    project_id: str = Query(...),
    page: int = Query(0),
    page_size: int = Query(50),
    enrich: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Execute a raw filter dict query."""
    try:
        filters["project_id"] = project_id
        filters["page"] = page
        filters["page_size"] = page_size

        if enrich:
            result = QueryExecutor.execute_and_enrich(db, filters)
        else:
            result = QueryExecutor.execute_query(db, filters)

        QueryHistoryService.record_execution(
            db, project_id,
            QueryBuilder.serialize_query(filters),
            result["total"],
            result["execution_time_ms"],
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Saved Queries ────────────────────────────────────────────────────────────


@router.post("/saved")
def save_query(
    req: SaveQueryRequest,
    db: Session = Depends(get_db),
):
    """Save a query for later re-execution."""
    try:
        sq = QueryHistoryService.save_query(
            db,
            project_id=req.project_id,
            name=req.name,
            filters_json=req.filters_json,
            description=req.description,
            sort_by=req.sort_by,
            sort_direction=req.sort_direction,
            max_results=req.max_results,
            tags_json=req.tags_json,
            created_by=req.created_by,
        )
        return sq.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/saved")
def list_saved_queries(
    project_id: str = Query(...),
    favorite_only: bool = Query(False),
    pinned_only: bool = Query(False),
    search: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List saved queries for a project."""
    items, total = QueryHistoryService.list_saved_queries(
        db, project_id, favorite_only, pinned_only,
        search, page, page_size,
    )
    return {
        "items": [sq.to_dict() for sq in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/saved/{query_id}")
def get_saved_query(
    query_id: str,
    db: Session = Depends(get_db),
):
    """Get a saved query by ID."""
    sq = QueryHistoryService.get_saved_query(db, query_id)
    if sq is None:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return sq.to_dict()


@router.put("/saved/{query_id}")
def update_saved_query(
    query_id: str,
    req: UpdateQueryRequest,
    db: Session = Depends(get_db),
):
    """Update a saved query."""
    sq = QueryHistoryService.update_saved_query(
        db, query_id,
        name=req.name,
        description=req.description,
        filters_json=req.filters_json,
        sort_by=req.sort_by,
        sort_direction=req.sort_direction,
        max_results=req.max_results,
        favorite=req.favorite,
        pinned=req.pinned,
        tags_json=req.tags_json,
    )
    if sq is None:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return sq.to_dict()


@router.delete("/saved/{query_id}", status_code=204)
def delete_saved_query(
    query_id: str,
    db: Session = Depends(get_db),
):
    """Delete a saved query."""
    if not QueryHistoryService.delete_saved_query(db, query_id):
        raise HTTPException(status_code=404, detail="Saved query not found")


@router.post("/saved/{query_id}/favorite")
def toggle_query_favorite(
    query_id: str,
    db: Session = Depends(get_db),
):
    """Toggle favorite status of a saved query."""
    sq = QueryHistoryService.toggle_favorite(db, query_id)
    if sq is None:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return sq.to_dict()


@router.post("/saved/{query_id}/pin")
def toggle_query_pinned(
    query_id: str,
    db: Session = Depends(get_db),
):
    """Toggle pinned status of a saved query."""
    sq = QueryHistoryService.toggle_pinned(db, query_id)
    if sq is None:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return sq.to_dict()


@router.post("/saved/{query_id}/rerun")
def rerun_saved_query(
    query_id: str,
    page: int = Query(0),
    page_size: int = Query(50),
    enrich: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Re-run a saved query."""
    sq = QueryHistoryService.get_saved_query(db, query_id)
    if sq is None:
        raise HTTPException(status_code=404, detail="Saved query not found")

    try:
        query = QueryBuilder.deserialize_query(sq.filters_json)
        query["project_id"] = sq.project_id
        query["page"] = page
        query["page_size"] = page_size

        if enrich:
            result = QueryExecutor.execute_and_enrich(db, query)
        else:
            result = QueryExecutor.execute_query(db, query)

        QueryHistoryService.record_execution(
            db, sq.project_id,
            sq.filters_json,
            result["total"],
            result["execution_time_ms"],
            saved_query_id=query_id,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Query History ────────────────────────────────────────────────────────────


@router.get("/history")
def list_query_history(
    project_id: str = Query(...),
    saved_query_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List query execution history."""
    items, total = QueryHistoryService.list_history(
        db, project_id, saved_query_id, status, page, page_size,
    )
    return {
        "items": [h.to_dict() for h in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/history/{history_id}")
def get_history_entry(
    history_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific history entry."""
    entry = QueryHistoryService.get_history_entry(db, history_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found")
    return entry.to_dict()


@router.delete("/history/{history_id}", status_code=204)
def delete_history_entry(
    history_id: str,
    db: Session = Depends(get_db),
):
    """Delete a history entry."""
    if not QueryHistoryService.delete_history_entry(db, history_id):
        raise HTTPException(status_code=404, detail="History entry not found")


@router.delete("/history", status_code=204)
def clear_query_history(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Clear all query history for a project."""
    QueryHistoryService.clear_history(db, project_id)


# ── Export ───────────────────────────────────────────────────────────────────


@router.post("/export")
def export_results(
    req: ExportRequest,
    db: Session = Depends(get_db),
):
    """Export query results in the specified format."""
    if req.format not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {req.format}. "
                   f"Supported: {EXPORT_FORMATS}",
        )

    items: list[dict] = []

    if req.filters is not None:
        filters = dict(req.filters)
        filters["project_id"] = req.project_id
        result = QueryExecutor.execute_query(db, filters)
        items = result["items"]
    elif req.query_ids:
        from knowledge_engine.database.models import Entity
        for eid in req.query_ids:
            entity = (
                db.query(Entity).filter(Entity.id == eid).first()
            )
            if entity:
                items.append(entity.to_dict())

    if not items:
        raise HTTPException(status_code=404, detail="No results to export")

    try:
        content = ExportService.export(items, req.format)
        return {
            "format": req.format,
            "filename": f"garuda_query_export.{req.format}",
            "content": content,
            "count": len(items),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Cache ───────────────────────────────────────────────────────────────────


@router.delete("/cache", status_code=204)
def clear_query_cache(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Clear cached query results."""
    QueryHistoryService.clear_cache(db, project_id)
