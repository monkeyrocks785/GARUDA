"""Graph Service.

Provides graph-like traversal and querying of entity relationships.
Uses relational tables but exposes graph-like operations.
"""

import logging
from collections import defaultdict, deque

from sqlalchemy.orm import Session

from knowledge_engine.database.models import Entity, EntityRelationship

logger = logging.getLogger("garuda.knowledge.graph_service")


class GraphService:
    """Graph traversal and querying operations."""

    @staticmethod
    def get_entity_graph(
        db: Session,
        project_id: str,
        entity_id: str | None = None,
        depth: int = 2,
        relationship_types: list[str] | None = None,
    ) -> dict:
        """Get the entity relationship graph for a project.

        Returns nodes (entities) and edges (relationships).
        If entity_id is provided, returns only the subgraph around that entity.
        """
        # Get all entities
        entities_q = db.query(Entity).filter(Entity.project_id == project_id)
        if entity_id:
            # For subgraph, start from the given entity and expand
            return GraphService._get_subgraph(
                db, entity_id, depth, relationship_types
            )

        entities = entities_q.all()
        entity_ids = {e.id for e in entities}

        # Get all relationships within the project
        rels_q = (
            db.query(EntityRelationship)
            .join(Entity, EntityRelationship.source_entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
        )
        if relationship_types:
            rels_q = rels_q.filter(
                EntityRelationship.relationship_type.in_(relationship_types)
            )
        relationships = rels_q.all()

        nodes = [e.to_dict() for e in entities]
        edges = [r.to_dict() for r in relationships]

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def _get_subgraph(
        db: Session,
        center_entity_id: str,
        depth: int = 2,
        relationship_types: list[str] | None = None,
    ) -> dict:
        """Get subgraph around a specific entity up to N hops."""
        visited_entities: set[str] = set()
        visited_relationships: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        queue.append((center_entity_id, 0))

        while queue:
            current_id, current_depth = queue.popleft()
            if current_id in visited_entities:
                continue
            if current_depth > depth:
                continue

            visited_entities.add(current_id)

            # Get outgoing relationships
            out_q = db.query(EntityRelationship).filter(
                EntityRelationship.source_entity_id == current_id
            )
            if relationship_types:
                out_q = out_q.filter(
                    EntityRelationship.relationship_type.in_(relationship_types)
                )
            for rel in out_q.all():
                visited_relationships.add(rel.id)
                if rel.target_entity_id not in visited_entities:
                    queue.append((rel.target_entity_id, current_depth + 1))

            # Get incoming relationships
            in_q = db.query(EntityRelationship).filter(
                EntityRelationship.target_entity_id == current_id
            )
            if relationship_types:
                in_q = in_q.filter(
                    EntityRelationship.relationship_type.in_(relationship_types)
                )
            for rel in in_q.all():
                visited_relationships.add(rel.id)
                if rel.source_entity_id not in visited_entities:
                    queue.append((rel.source_entity_id, current_depth + 1))

        # Fetch full entities and relationships
        entities = []
        if visited_entities:
            entities = (
                db.query(Entity)
                .filter(Entity.id.in_(visited_entities))
                .all()
            )

        relationships = []
        if visited_relationships:
            relationships = (
                db.query(EntityRelationship)
                .filter(EntityRelationship.id.in_(visited_relationships))
                .all()
            )

        nodes = [e.to_dict() for e in entities]
        edges = [r.to_dict() for r in relationships]

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def find_shortest_path(
        db: Session,
        source_id: str,
        target_id: str,
        max_depth: int = 10,
        relationship_types: list[str] | None = None,
    ) -> list[dict] | None:
        """Find shortest path between two entities using BFS."""
        if source_id == target_id:
            return [{"entity_id": source_id, "relationship": None}]

        visited: dict[str, str | None] = {source_id: None}
        queue: deque[tuple[str, int]] = deque()
        queue.append((source_id, 0))

        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth >= max_depth:
                continue

            # Get all neighbors (both directions)
            neighbors = []

            out_q = db.query(EntityRelationship).filter(
                EntityRelationship.source_entity_id == current_id
            )
            if relationship_types:
                out_q = out_q.filter(
                    EntityRelationship.relationship_type.in_(relationship_types)
                )
            for rel in out_q.all():
                neighbors.append((rel.target_entity_id, rel))

            in_q = db.query(EntityRelationship).filter(
                EntityRelationship.target_entity_id == current_id
            )
            if relationship_types:
                in_q = in_q.filter(
                    EntityRelationship.relationship_type.in_(relationship_types)
                )
            for rel in in_q.all():
                neighbors.append((rel.source_entity_id, rel))

            for neighbor_id, rel in neighbors:
                if neighbor_id not in visited:
                    visited[neighbor_id] = current_id
                    if neighbor_id == target_id:
                        # Reconstruct path
                        path = []
                        node = target_id
                        while node is not None:
                            prev = visited[node]
                            # Find the relationship used
                            rel_used = None
                            for n_id, r in neighbors:
                                if n_id == node:
                                    rel_used = r
                                    break
                            path.append({
                                "entity_id": node,
                                "relationship": rel_used.to_dict() if rel_used and prev == current_id else None,
                            })
                            node = prev
                        path.reverse()
                        return path
                    queue.append((neighbor_id, current_depth + 1))

        return None  # No path found

    @staticmethod
    def get_connected_components(
        db: Session,
        project_id: str,
    ) -> list[list[str]]:
        """Find connected components in the entity graph."""
        # Get all entity IDs in project
        entities = db.query(Entity.id).filter(
            Entity.project_id == project_id
        ).all()
        entity_ids = [e.id for e in entities]

        if not entity_ids:
            return []

        # Build adjacency list
        adjacency: dict[str, set[str]] = defaultdict(set)
        rels = (
            db.query(EntityRelationship)
            .join(Entity, EntityRelationship.source_entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
            .all()
        )
        for rel in rels:
            adjacency[rel.source_entity_id].add(rel.target_entity_id)
            adjacency[rel.target_entity_id].add(rel.source_entity_id)

        # BFS to find components
        visited: set[str] = set()
        components: list[list[str]] = []

        for eid in entity_ids:
            if eid in visited:
                continue
            component = []
            queue = deque([eid])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                component.append(node)
                for neighbor in adjacency.get(node, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)

        return components

    @staticmethod
    def get_entity_degree(
        db: Session,
        entity_id: str,
    ) -> dict:
        """Get the degree (number of connections) of an entity."""
        outgoing = db.query(EntityRelationship).filter(
            EntityRelationship.source_entity_id == entity_id
        ).count()
        incoming = db.query(EntityRelationship).filter(
            EntityRelationship.target_entity_id == entity_id
        ).count()
        return {
            "outgoing": outgoing,
            "incoming": incoming,
            "total": outgoing + incoming,
        }
