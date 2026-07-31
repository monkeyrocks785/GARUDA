"""Knowledge Engine API.

Provides endpoints for managing entities, relationships, events,
history, and graph operations in the knowledge graph.
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from knowledge_engine.config import (
    ENTITY_TYPES,
    ENTITY_STATUSES,
    EVENT_TYPES,
    RELATIONSHIP_TYPES,
)
from knowledge_engine.services.entity_service import EntityService
from knowledge_engine.services.relationship_service import RelationshipService
from knowledge_engine.services.event_service import EventService
from knowledge_engine.services.history_service import HistoryService
from knowledge_engine.services.graph_service import GraphService
from knowledge_engine.services.search_service import SearchService

logger = logging.getLogger("garuda.knowledge.api")

router = APIRouter(prefix="/knowledge", tags=["Knowledge Engine"])


# ── Request/Response Models ──────────────────────────────────────────────────

class EntityCreateRequest(BaseModel):
    entity_type: str
    name: str
    description: str | None = None
    confidence: float = 1.0
    geometry_json: str | None = None
    bbox: list[float] | None = None
    centroid: list[float] | None = None
    attributes: dict | None = None
    tags: list[str] | None = None
    analyst_notes: str | None = None
    source_id: str | None = None
    source_type: str | None = None


class EntityUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    confidence: float | None = None
    geometry_json: str | None = None
    bbox: list[float] | None = None
    centroid: list[float] | None = None
    attributes: dict | None = None
    tags: list[str] | None = None
    analyst_notes: str | None = None
    favorite: bool | None = None
    archived: bool | None = None


class ObservationCreateRequest(BaseModel):
    observation_type: str
    source_id: str | None = None
    source_type: str | None = None
    confidence: float = 1.0
    geometry_json: str | None = None
    attributes: dict | None = None
    observed_at: str | None = None
    analyst_notes: str | None = None


class RelationshipCreateRequest(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence: float = 1.0
    attributes: dict | None = None
    description: str | None = None
    bidirectional: bool = False
    analyst_notes: str | None = None
    source_id: str | None = None
    source_type: str | None = None


class RelationshipUpdateRequest(BaseModel):
    confidence: float | None = None
    attributes: dict | None = None
    description: str | None = None
    bidirectional: bool | None = None
    analyst_notes: str | None = None


class EventCreateRequest(BaseModel):
    entity_id: str
    event_type: str
    description: str | None = None
    attributes: dict | None = None
    geometry_json: str | None = None
    confidence: float = 1.0
    source_id: str | None = None
    source_type: str | None = None
    analyst_notes: str | None = None
    event_time: str | None = None


class EventUpdateRequest(BaseModel):
    description: str | None = None
    attributes: dict | None = None
    analyst_notes: str | None = None


class SearchRequest(BaseModel):
    query: str
    entity_types: list[str] | None = None
    statuses: list[str] | None = None
    tags: list[str] | None = None
    min_confidence: float | None = None
    has_observations: bool | None = None
    has_relationships: bool | None = None
    geometry_bbox: list[float] | None = None
    limit: int = 50


class GraphRequest(BaseModel):
    entity_id: str | None = None
    depth: int = 2
    relationship_types: list[str] | None = None


class ShortestPathRequest(BaseModel):
    source_entity_id: str
    target_entity_id: str
    max_depth: int = 10
    relationship_types: list[str] | None = None


# ── Config Endpoint ──────────────────────────────────────────────────────────

@router.get("/config")
def get_config():
    """Get Knowledge Engine configuration."""
    return {
        "entity_types": ENTITY_TYPES,
        "entity_statuses": ENTITY_STATUSES,
        "event_types": EVENT_TYPES,
        "relationship_types": RELATIONSHIP_TYPES,
    }


# ── Entity Endpoints ─────────────────────────────────────────────────────────

@router.post("/project/{project_id}/entities", status_code=201)
def create_entity(
    project_id: str,
    req: EntityCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new entity."""
    try:
        entity = EntityService.create_entity(
            db,
            project_id=project_id,
            entity_type=req.entity_type,
            name=req.name,
            description=req.description,
            confidence=req.confidence,
            geometry_json=req.geometry_json,
            bbox=req.bbox,
            centroid=req.centroid,
            attributes=req.attributes,
            tags=req.tags,
            analyst_notes=req.analyst_notes,
            source_id=req.source_id,
            source_type=req.source_type,
        )
        return entity.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/entities")
def list_entities(
    project_id: str,
    entity_type: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    favorite: bool = Query(False),
    archived: bool = Query(False),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List entities with filtering and pagination."""
    entities, total = EntityService.list_entities(
        db,
        project_id=project_id,
        entity_type=entity_type,
        status=status,
        search=search,
        favorite_only=favorite,
        archived_only=archived,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [e.to_dict() for e in entities],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/entities/{entity_id}")
def get_entity(entity_id: str, db: Session = Depends(get_db)):
    """Get entity by ID."""
    entity = EntityService.get_entity(db, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity.to_dict()


@router.put("/entities/{entity_id}")
def update_entity(
    entity_id: str,
    req: EntityUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update an entity."""
    entity = EntityService.update_entity(
        db,
        entity_id=entity_id,
        name=req.name,
        description=req.description,
        status=req.status,
        confidence=req.confidence,
        geometry_json=req.geometry_json,
        bbox=req.bbox,
        centroid=req.centroid,
        attributes=req.attributes,
        tags=req.tags,
        analyst_notes=req.analyst_notes,
        favorite=req.favorite,
        archived=req.archived,
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity.to_dict()


@router.delete("/entities/{entity_id}", status_code=204)
def delete_entity(entity_id: str, db: Session = Depends(get_db)):
    """Delete an entity and all related data."""
    deleted = EntityService.delete_entity(db, entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")
    return None


# ── Observation Endpoints ────────────────────────────────────────────────────

@router.post("/entities/{entity_id}/observations", status_code=201)
def add_observation(
    entity_id: str,
    req: ObservationCreateRequest,
    db: Session = Depends(get_db),
):
    """Add an observation to an entity."""
    observed_at = None
    if req.observed_at:
        try:
            observed_at = datetime.fromisoformat(req.observed_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

    obs = EntityService.add_observation(
        db,
        entity_id=entity_id,
        observation_type=req.observation_type,
        source_id=req.source_id,
        source_type=req.source_type,
        confidence=req.confidence,
        geometry_json=req.geometry_json,
        attributes=req.attributes,
        observed_at=observed_at,
        analyst_notes=req.analyst_notes,
    )
    if obs is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return obs.to_dict()


@router.get("/entities/{entity_id}/observations")
def list_observations(
    entity_id: str,
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List observations for an entity."""
    observations, total = EntityService.get_entity_observations(
        db, entity_id, page=page, page_size=page_size,
    )
    return {
        "items": [o.to_dict() for o in observations],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── Relationship Endpoints ───────────────────────────────────────────────────

@router.post("/relationships", status_code=201)
def create_relationship(
    req: RelationshipCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a relationship between two entities."""
    try:
        rel = RelationshipService.create_relationship(
            db,
            source_entity_id=req.source_entity_id,
            target_entity_id=req.target_entity_id,
            relationship_type=req.relationship_type,
            confidence=req.confidence,
            attributes=req.attributes,
            description=req.description,
            bidirectional=req.bidirectional,
            analyst_notes=req.analyst_notes,
            source_id=req.source_id,
            source_type=req.source_type,
        )
        return rel.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/relationships")
def list_relationships(
    project_id: str,
    entity_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List relationships for a project."""
    rels, total = RelationshipService.list_relationships(
        db, project_id=project_id, entity_id=entity_id,
        relationship_type=relationship_type, page=page, page_size=page_size,
    )
    return {"items": rels, "total": total, "page": page, "page_size": page_size}


@router.get("/relationships/{relationship_id}")
def get_relationship(relationship_id: str, db: Session = Depends(get_db)):
    """Get a relationship by ID."""
    rel = RelationshipService.get_relationship(db, relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel.to_dict()


@router.put("/relationships/{relationship_id}")
def update_relationship(
    relationship_id: str,
    req: RelationshipUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update a relationship."""
    rel = RelationshipService.update_relationship(
        db, relationship_id,
        confidence=req.confidence,
        attributes=req.attributes,
        description=req.description,
        bidirectional=req.bidirectional,
        analyst_notes=req.analyst_notes,
    )
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel.to_dict()


@router.delete("/relationships/{relationship_id}", status_code=204)
def delete_relationship(relationship_id: str, db: Session = Depends(get_db)):
    """Delete a relationship."""
    deleted = RelationshipService.delete_relationship(db, relationship_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return None


@router.get("/entities/{entity_id}/neighbors")
def get_entity_neighbors(
    entity_id: str,
    relationship_type: str | None = Query(None),
    direction: str = Query("both"),
    db: Session = Depends(get_db),
):
    """Get all entities connected to a given entity."""
    return RelationshipService.get_entity_neighbors(
        db, entity_id, relationship_type=relationship_type, direction=direction,
    )


# ── Event Endpoints ──────────────────────────────────────────────────────────

@router.post("/events", status_code=201)
def create_event(
    req: EventCreateRequest,
    db: Session = Depends(get_db),
):
    """Create an event for an entity."""
    event_time = None
    if req.event_time:
        try:
            event_time = datetime.fromisoformat(req.event_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

    try:
        event = EventService.create_event(
            db,
            entity_id=req.entity_id,
            event_type=req.event_type,
            description=req.description,
            attributes=req.attributes,
            geometry_json=req.geometry_json,
            confidence=req.confidence,
            source_id=req.source_id,
            source_type=req.source_type,
            analyst_notes=req.analyst_notes,
            event_time=event_time,
        )
        return event.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities/{entity_id}/events")
def list_entity_events(
    entity_id: str,
    event_type: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List events for an entity."""
    events, total = EventService.list_entity_events(
        db, entity_id, event_type=event_type, page=page, page_size=page_size,
    )
    return {
        "items": [e.to_dict() for e in events],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Get an event by ID."""
    event = EventService.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()


@router.put("/events/{event_id}")
def update_event(
    event_id: str,
    req: EventUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update an event."""
    event = EventService.update_event(
        db, event_id,
        description=req.description,
        attributes=req.attributes,
        analyst_notes=req.analyst_notes,
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """Delete an event."""
    deleted = EventService.delete_event(db, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return None


@router.get("/project/{project_id}/events")
def list_project_events(
    project_id: str,
    event_type: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all events for a project."""
    events, total = EventService.get_project_events(
        db, project_id, event_type=event_type, page=page, page_size=page_size,
    )
    return {"items": events, "total": total, "page": page, "page_size": page_size}


# ── History Endpoints ────────────────────────────────────────────────────────

@router.get("/entities/{entity_id}/history")
def get_entity_history(
    entity_id: str,
    change_type: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get history for an entity."""
    entries, total = HistoryService.get_entity_history(
        db, entity_id, change_type=change_type, page=page, page_size=page_size,
    )
    return {
        "items": [e.to_dict() for e in entries],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/entities/{entity_id}/history/summary")
def get_history_summary(entity_id: str, db: Session = Depends(get_db)):
    """Get history summary for an entity."""
    return HistoryService.get_history_summary(db, entity_id)


# ── Graph Endpoints ──────────────────────────────────────────────────────────

@router.post("/project/{project_id}/graph")
def get_entity_graph(
    project_id: str,
    req: GraphRequest,
    db: Session = Depends(get_db),
):
    """Get the entity relationship graph."""
    return GraphService.get_entity_graph(
        db, project_id,
        entity_id=req.entity_id,
        depth=req.depth,
        relationship_types=req.relationship_types,
    )


@router.post("/graph/shortest-path")
def find_shortest_path(
    req: ShortestPathRequest,
    db: Session = Depends(get_db),
):
    """Find shortest path between two entities."""
    path = GraphService.find_shortest_path(
        db,
        source_id=req.source_entity_id,
        target_id=req.target_entity_id,
        max_depth=req.max_depth,
        relationship_types=req.relationship_types,
    )
    if path is None:
        raise HTTPException(
            status_code=404,
            detail="No path found between the specified entities",
        )
    return {"path": path}


@router.get("/project/{project_id}/graph/components")
def get_connected_components(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Get connected components in the entity graph."""
    components = GraphService.get_connected_components(db, project_id)
    return {"components": components, "count": len(components)}


@router.get("/entities/{entity_id}/graph/degree")
def get_entity_degree(entity_id: str, db: Session = Depends(get_db)):
    """Get the degree of an entity (number of connections)."""
    return GraphService.get_entity_degree(db, entity_id)


# ── Search Endpoints ─────────────────────────────────────────────────────────

@router.post("/project/{project_id}/search")
def search_entities(
    project_id: str,
    req: SearchRequest,
    db: Session = Depends(get_db),
):
    """Full-text and attribute search across entities."""
    results = SearchService.search_entities(
        db, project_id,
        query=req.query,
        entity_types=req.entity_types,
        statuses=req.statuses,
        tags=req.tags,
        min_confidence=req.min_confidence,
        has_observations=req.has_observations,
        has_relationships=req.has_relationships,
        geometry_bbox=req.geometry_bbox,
        limit=req.limit,
    )
    return {"items": results, "total": len(results)}


@router.get("/project/{project_id}/search/relationships")
def search_relationships(
    project_id: str,
    relationship_type: str | None = Query(None),
    entity_type: str | None = Query(None),
    min_confidence: float | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Search relationships with filters."""
    results = SearchService.search_relationships(
        db, project_id,
        relationship_type=relationship_type,
        entity_type=entity_type,
        min_confidence=min_confidence,
        limit=limit,
    )
    return {"items": results, "total": len(results)}


@router.get("/project/{project_id}/search/events")
def search_events(
    project_id: str,
    event_type: str | None = Query(None),
    entity_type: str | None = Query(None),
    query: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Search events across a project."""
    results = SearchService.search_events(
        db, project_id,
        event_type=event_type,
        entity_type=entity_type,
        query=query,
        limit=limit,
    )
    return {"items": results, "total": len(results)}


# ── Stats Endpoints ──────────────────────────────────────────────────────────

@router.get("/project/{project_id}/stats")
def get_project_stats(project_id: str, db: Session = Depends(get_db)):
    """Get comprehensive statistics for a project's knowledge graph."""
    return SearchService.get_statistics(db, project_id)


@router.get("/project/{project_id}/stats/entities")
def get_entity_stats(project_id: str, db: Session = Depends(get_db)):
    """Get entity statistics for a project."""
    return EntityService.get_entity_stats(db, project_id)
