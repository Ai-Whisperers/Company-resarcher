"""
Personal Knowledge Graph for semantic entity relationships.

Provides infrastructure for building, querying, and traversing
a graph of entities and their relationships extracted from documents.
"""

import json
import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..logging import setup_logger

logger = setup_logger("knowledge_graph")


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    PROJECT = "project"
    CONCEPT = "concept"
    DOCUMENT = "document"
    EVENT = "event"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    DATE = "date"
    CUSTOM = "custom"


class RelationType(str, Enum):
    """Common relationship types."""

    WORKS_AT = "WORKS_AT"
    WORKS_ON = "WORKS_ON"
    MANAGES = "MANAGES"
    REPORTS_TO = "REPORTS_TO"
    KNOWS = "KNOWS"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    LOCATED_IN = "LOCATED_IN"
    PART_OF = "PART_OF"
    OWNS = "OWNS"
    FOUNDED = "FOUNDED"
    CREATED = "CREATED"
    USES = "USES"
    RELATED_TO = "RELATED_TO"
    MENTIONED_IN = "MENTIONED_IN"
    OCCURRED_ON = "OCCURRED_ON"
    CUSTOM = "CUSTOM"


@dataclass
class Entity:
    """An entity in the knowledge graph."""

    entity_id: str
    name: str
    entity_type: EntityType

    # Additional info
    aliases: List[str] = field(default_factory=list)
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    # Source tracking
    source_documents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "aliases": self.aliases,
            "description": self.description,
            "properties": self.properties,
            "source_documents": self.source_documents,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            name=data["name"],
            entity_type=EntityType(data.get("entity_type", "custom")),
            aliases=data.get("aliases", []),
            description=data.get("description"),
            properties=data.get("properties", {}),
            source_documents=data.get("source_documents", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )


@dataclass
class Relationship:
    """A relationship between two entities."""

    relationship_id: str
    source_id: str
    target_id: str
    relation_type: str

    # Additional info
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    confidence: float = 1.0

    # Source tracking
    source_documents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "relationship_id": self.relationship_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "properties": self.properties,
            "weight": self.weight,
            "confidence": self.confidence,
            "source_documents": self.source_documents,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """Create from dictionary."""
        return cls(
            relationship_id=data["relationship_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=data["relation_type"],
            properties=data.get("properties", {}),
            weight=data.get("weight", 1.0),
            confidence=data.get("confidence", 1.0),
            source_documents=data.get("source_documents", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


@dataclass
class Triple:
    """A subject-predicate-object triple."""

    subject: str
    predicate: str
    object: str

    subject_type: Optional[EntityType] = None
    object_type: Optional[EntityType] = None

    confidence: float = 1.0
    source: Optional[str] = None


@dataclass
class GraphPath:
    """A path through the knowledge graph."""

    entities: List[Entity]
    relationships: List[Relationship]
    total_weight: float = 0.0

    @property
    def length(self) -> int:
        """Get path length (number of hops)."""
        return len(self.relationships)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entities": [e.name for e in self.entities],
            "relationships": [r.relation_type for r in self.relationships],
            "length": self.length,
            "total_weight": self.total_weight,
        }


class TripleExtractor:
    """
    Extracts entity-relationship triples from text.

    Uses pattern matching for basic extraction. For production,
    integrate with LLM for more sophisticated extraction.
    """

    # Common relationship patterns
    PATTERNS = [
        # Person works at/for Organization
        (r"(\w+(?:\s+\w+)?)\s+(?:works\s+(?:at|for)|is\s+employed\s+by)\s+(\w+(?:\s+\w+)?)",
         RelationType.WORKS_AT, EntityType.PERSON, EntityType.ORGANIZATION),

        # Person works on Project
        (r"(\w+(?:\s+\w+)?)\s+(?:works\s+on|is\s+working\s+on)\s+(\w+(?:\s+\w+)?)",
         RelationType.WORKS_ON, EntityType.PERSON, EntityType.PROJECT),

        # Person manages Person/Project
        (r"(\w+(?:\s+\w+)?)\s+(?:manages|leads|directs)\s+(\w+(?:\s+\w+)?)",
         RelationType.MANAGES, EntityType.PERSON, EntityType.CUSTOM),

        # Person knows Person
        (r"(\w+(?:\s+\w+)?)\s+(?:knows|met|is\s+friends\s+with)\s+(\w+(?:\s+\w+)?)",
         RelationType.KNOWS, EntityType.PERSON, EntityType.PERSON),

        # Entity is located in Location
        (r"(\w+(?:\s+\w+)?)\s+(?:is\s+located\s+in|is\s+based\s+in|is\s+in)\s+(\w+(?:\s+\w+)?)",
         RelationType.LOCATED_IN, EntityType.CUSTOM, EntityType.LOCATION),

        # Entity is part of Entity
        (r"(\w+(?:\s+\w+)?)\s+(?:is\s+part\s+of|belongs\s+to)\s+(\w+(?:\s+\w+)?)",
         RelationType.PART_OF, EntityType.CUSTOM, EntityType.CUSTOM),

        # Person founded Organization
        (r"(\w+(?:\s+\w+)?)\s+(?:founded|started|created)\s+(\w+(?:\s+\w+)?)",
         RelationType.FOUNDED, EntityType.PERSON, EntityType.ORGANIZATION),

        # Entity uses Technology
        (r"(\w+(?:\s+\w+)?)\s+(?:uses|utilizes|employs)\s+(\w+(?:\s+\w+)?)",
         RelationType.USES, EntityType.CUSTOM, EntityType.TECHNOLOGY),
    ]

    def extract(self, text: str, source: Optional[str] = None) -> List[Triple]:
        """
        Extract triples from text.

        Args:
            text: Input text.
            source: Optional source identifier.

        Returns:
            List of extracted triples.
        """
        triples = []

        for pattern, relation, subj_type, obj_type in self.PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                subject = match.group(1).strip()
                obj = match.group(2).strip()

                # Skip if too short or generic
                if len(subject) < 2 or len(obj) < 2:
                    continue

                triples.append(Triple(
                    subject=subject,
                    predicate=relation.value,
                    object=obj,
                    subject_type=subj_type,
                    object_type=obj_type,
                    source=source,
                ))

        return triples

    def extract_with_llm(
        self,
        text: str,
        llm_callback: Callable[[str], str],
        source: Optional[str] = None,
    ) -> List[Triple]:
        """
        Extract triples using an LLM.

        Args:
            text: Input text.
            llm_callback: Function to call LLM.
            source: Optional source identifier.

        Returns:
            List of extracted triples.
        """
        prompt = f"""Extract entity relationships from the following text.
Return as JSON array of objects with: subject, predicate, object, subject_type, object_type.

Entity types: person, organization, location, project, concept, event, product, technology
Common predicates: WORKS_AT, WORKS_ON, MANAGES, KNOWS, LOCATED_IN, PART_OF, FOUNDED, USES, RELATED_TO

Text:
{text}

JSON:"""

        try:
            response = llm_callback(prompt)

            # Parse JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return [
                    Triple(
                        subject=item["subject"],
                        predicate=item["predicate"],
                        object=item["object"],
                        subject_type=EntityType(item.get("subject_type", "custom")),
                        object_type=EntityType(item.get("object_type", "custom")),
                        source=source,
                    )
                    for item in data
                ]
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")

        return []


class KnowledgeGraph:
    """
    Personal knowledge graph for entity relationships.

    Stores entities and their relationships, supporting queries
    and traversal operations.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the knowledge graph.

        Args:
            storage_path: Path to persist the graph.
        """
        self.storage_path = storage_path
        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)

        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}

        # Indexes for efficient lookup
        self._name_to_entity: Dict[str, str] = {}  # name -> entity_id
        self._outgoing: Dict[str, List[str]] = defaultdict(list)  # entity_id -> [rel_ids]
        self._incoming: Dict[str, List[str]] = defaultdict(list)  # entity_id -> [rel_ids]

        self._lock = threading.Lock()
        self._extractor = TripleExtractor()

        self._load()

    def _load(self) -> None:
        """Load graph from storage."""
        if not self.storage_path:
            return

        entities_file = self.storage_path / "entities.json"
        rels_file = self.storage_path / "relationships.json"

        if entities_file.exists():
            try:
                data = json.loads(entities_file.read_text())
                for item in data:
                    entity = Entity.from_dict(item)
                    self._entities[entity.entity_id] = entity
                    self._name_to_entity[entity.name.lower()] = entity.entity_id
                    for alias in entity.aliases:
                        self._name_to_entity[alias.lower()] = entity.entity_id
            except Exception as e:
                logger.warning(f"Failed to load entities: {e}")

        if rels_file.exists():
            try:
                data = json.loads(rels_file.read_text())
                for item in data:
                    rel = Relationship.from_dict(item)
                    self._relationships[rel.relationship_id] = rel
                    self._outgoing[rel.source_id].append(rel.relationship_id)
                    self._incoming[rel.target_id].append(rel.relationship_id)
            except Exception as e:
                logger.warning(f"Failed to load relationships: {e}")

        logger.info(f"Loaded graph: {len(self._entities)} entities, {len(self._relationships)} relationships")

    def _save(self) -> None:
        """Save graph to storage."""
        if not self.storage_path:
            return

        entities_file = self.storage_path / "entities.json"
        rels_file = self.storage_path / "relationships.json"

        entities_data = [e.to_dict() for e in self._entities.values()]
        entities_file.write_text(json.dumps(entities_data, indent=2))

        rels_data = [r.to_dict() for r in self._relationships.values()]
        rels_file.write_text(json.dumps(rels_data, indent=2))

    def _generate_id(self, prefix: str, name: str) -> str:
        """Generate a unique ID."""
        import hashlib
        hash_input = f"{prefix}:{name}:{datetime.now().isoformat()}"
        return f"{prefix}_{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        source_document: Optional[str] = None,
    ) -> Entity:
        """
        Add an entity to the graph.

        Args:
            name: Entity name.
            entity_type: Type of entity.
            aliases: Alternative names.
            description: Entity description.
            properties: Additional properties.
            source_document: Source document ID.

        Returns:
            The created or updated Entity.
        """
        name_lower = name.lower()

        with self._lock:
            # Check if entity exists
            existing_id = self._name_to_entity.get(name_lower)
            if existing_id:
                entity = self._entities[existing_id]
                entity.updated_at = datetime.now()
                if source_document and source_document not in entity.source_documents:
                    entity.source_documents.append(source_document)
                self._save()
                return entity

            # Create new entity
            entity_id = self._generate_id("ent", name)
            entity = Entity(
                entity_id=entity_id,
                name=name,
                entity_type=entity_type,
                aliases=aliases or [],
                description=description,
                properties=properties or {},
                source_documents=[source_document] if source_document else [],
            )

            self._entities[entity_id] = entity
            self._name_to_entity[name_lower] = entity_id
            for alias in entity.aliases:
                self._name_to_entity[alias.lower()] = entity_id

            self._save()
            logger.debug(f"Added entity: {name} ({entity_type.value})")
            return entity

    def add_relationship(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        source_type: EntityType = EntityType.CUSTOM,
        target_type: EntityType = EntityType.CUSTOM,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
        confidence: float = 1.0,
        source_document: Optional[str] = None,
    ) -> Relationship:
        """
        Add a relationship between two entities.

        Creates entities if they don't exist.

        Args:
            source_name: Source entity name.
            target_name: Target entity name.
            relation_type: Type of relationship.
            source_type: Type for source entity if created.
            target_type: Type for target entity if created.
            properties: Additional properties.
            weight: Relationship weight.
            confidence: Confidence score.
            source_document: Source document ID.

        Returns:
            The created Relationship.
        """
        # Ensure entities exist
        source = self.add_entity(source_name, source_type, source_document=source_document)
        target = self.add_entity(target_name, target_type, source_document=source_document)

        with self._lock:
            # Check for existing relationship
            for rel_id in self._outgoing.get(source.entity_id, []):
                rel = self._relationships.get(rel_id)
                if rel and rel.target_id == target.entity_id and rel.relation_type == relation_type:
                    # Update existing
                    rel.weight = max(rel.weight, weight)
                    if source_document and source_document not in rel.source_documents:
                        rel.source_documents.append(source_document)
                    self._save()
                    return rel

            # Create new relationship
            rel_id = self._generate_id("rel", f"{source_name}_{target_name}")
            relationship = Relationship(
                relationship_id=rel_id,
                source_id=source.entity_id,
                target_id=target.entity_id,
                relation_type=relation_type,
                properties=properties or {},
                weight=weight,
                confidence=confidence,
                source_documents=[source_document] if source_document else [],
            )

            self._relationships[rel_id] = relationship
            self._outgoing[source.entity_id].append(rel_id)
            self._incoming[target.entity_id].append(rel_id)

            self._save()
            logger.debug(f"Added relationship: {source_name} -{relation_type}-> {target_name}")
            return relationship

    def add_triple(self, triple: Triple, source_document: Optional[str] = None) -> Relationship:
        """Add a triple to the graph."""
        return self.add_relationship(
            source_name=triple.subject,
            target_name=triple.object,
            relation_type=triple.predicate,
            source_type=triple.subject_type or EntityType.CUSTOM,
            target_type=triple.object_type or EntityType.CUSTOM,
            confidence=triple.confidence,
            source_document=source_document or triple.source,
        )

    def extract_and_add(
        self,
        text: str,
        source_document: Optional[str] = None,
    ) -> List[Relationship]:
        """
        Extract triples from text and add to graph.

        Args:
            text: Input text.
            source_document: Source document ID.

        Returns:
            List of created relationships.
        """
        triples = self._extractor.extract(text, source_document)
        relationships = []

        for triple in triples:
            rel = self.add_triple(triple, source_document)
            relationships.append(rel)

        return relationships

    def get_entity(self, name_or_id: str) -> Optional[Entity]:
        """Get an entity by name or ID."""
        with self._lock:
            # Try by ID first
            if name_or_id in self._entities:
                return self._entities[name_or_id]

            # Try by name
            entity_id = self._name_to_entity.get(name_or_id.lower())
            if entity_id:
                return self._entities.get(entity_id)

        return None

    def get_relationships(
        self,
        entity_name: str,
        direction: str = "both",
        relation_type: Optional[str] = None,
    ) -> List[Tuple[Relationship, Entity]]:
        """
        Get relationships for an entity.

        Args:
            entity_name: Entity name or ID.
            direction: "outgoing", "incoming", or "both".
            relation_type: Filter by relation type.

        Returns:
            List of (relationship, connected_entity) tuples.
        """
        entity = self.get_entity(entity_name)
        if not entity:
            return []

        results = []

        with self._lock:
            if direction in ("outgoing", "both"):
                for rel_id in self._outgoing.get(entity.entity_id, []):
                    rel = self._relationships.get(rel_id)
                    if rel and (not relation_type or rel.relation_type == relation_type):
                        target = self._entities.get(rel.target_id)
                        if target:
                            results.append((rel, target))

            if direction in ("incoming", "both"):
                for rel_id in self._incoming.get(entity.entity_id, []):
                    rel = self._relationships.get(rel_id)
                    if rel and (not relation_type or rel.relation_type == relation_type):
                        source = self._entities.get(rel.source_id)
                        if source:
                            results.append((rel, source))

        return results

    def find_path(
        self,
        start_name: str,
        end_name: str,
        max_depth: int = 5,
    ) -> Optional[GraphPath]:
        """
        Find a path between two entities.

        Args:
            start_name: Starting entity name.
            end_name: Target entity name.
            max_depth: Maximum path length.

        Returns:
            GraphPath if found, None otherwise.
        """
        start = self.get_entity(start_name)
        end = self.get_entity(end_name)

        if not start or not end:
            return None

        # BFS to find shortest path
        from collections import deque

        visited: Set[str] = {start.entity_id}
        queue: deque = deque([(start, [], [])])  # (entity, entities, relationships)

        while queue:
            current, entities, rels = queue.popleft()

            if len(rels) >= max_depth:
                continue

            for rel_id in self._outgoing.get(current.entity_id, []):
                rel = self._relationships.get(rel_id)
                if not rel:
                    continue

                target = self._entities.get(rel.target_id)
                if not target:
                    continue

                if target.entity_id == end.entity_id:
                    # Found path
                    path_entities = entities + [current, target]
                    path_rels = rels + [rel]
                    return GraphPath(
                        entities=path_entities,
                        relationships=path_rels,
                        total_weight=sum(r.weight for r in path_rels),
                    )

                if target.entity_id not in visited:
                    visited.add(target.entity_id)
                    queue.append((target, entities + [current], rels + [rel]))

        return None

    def search_entities(
        self,
        query: str,
        entity_type: Optional[EntityType] = None,
        limit: int = 10,
    ) -> List[Entity]:
        """
        Search for entities by name.

        Args:
            query: Search query.
            entity_type: Filter by type.
            limit: Maximum results.

        Returns:
            List of matching entities.
        """
        query_lower = query.lower()
        results: List[Tuple[float, Entity]] = []

        for entity in self._entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue

            score = 0.0

            # Exact match
            if entity.name.lower() == query_lower:
                score += 3.0
            # Starts with
            elif entity.name.lower().startswith(query_lower):
                score += 2.0
            # Contains
            elif query_lower in entity.name.lower():
                score += 1.0
            # Alias match
            else:
                for alias in entity.aliases:
                    if query_lower in alias.lower():
                        score += 0.5
                        break

            if score > 0:
                results.append((score, entity))

        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:limit]]

    def get_neighbors(
        self,
        entity_name: str,
        depth: int = 1,
    ) -> Dict[str, List[Entity]]:
        """
        Get neighboring entities at various depths.

        Args:
            entity_name: Starting entity.
            depth: Maximum depth to explore.

        Returns:
            Dict mapping depth to list of entities.
        """
        start = self.get_entity(entity_name)
        if not start:
            return {}

        result: Dict[int, List[Entity]] = {0: [start]}
        visited = {start.entity_id}

        for d in range(1, depth + 1):
            current_level = result.get(d - 1, [])
            next_level = []

            for entity in current_level:
                for rel_id in self._outgoing.get(entity.entity_id, []):
                    rel = self._relationships.get(rel_id)
                    if rel and rel.target_id not in visited:
                        target = self._entities.get(rel.target_id)
                        if target:
                            next_level.append(target)
                            visited.add(rel.target_id)

                for rel_id in self._incoming.get(entity.entity_id, []):
                    rel = self._relationships.get(rel_id)
                    if rel and rel.source_id not in visited:
                        source = self._entities.get(rel.source_id)
                        if source:
                            next_level.append(source)
                            visited.add(rel.source_id)

            if next_level:
                result[d] = next_level

        return result

    def remove_entity(self, name_or_id: str) -> bool:
        """Remove an entity and its relationships."""
        entity = self.get_entity(name_or_id)
        if not entity:
            return False

        with self._lock:
            # Remove relationships
            rel_ids_to_remove = (
                self._outgoing.get(entity.entity_id, []) +
                self._incoming.get(entity.entity_id, [])
            )

            for rel_id in rel_ids_to_remove:
                if rel_id in self._relationships:
                    del self._relationships[rel_id]

            # Clear indexes
            self._outgoing.pop(entity.entity_id, None)
            self._incoming.pop(entity.entity_id, None)

            # Remove entity
            del self._entities[entity.entity_id]
            self._name_to_entity.pop(entity.name.lower(), None)
            for alias in entity.aliases:
                self._name_to_entity.pop(alias.lower(), None)

            self._save()

        return True

    def clear(self) -> None:
        """Clear the entire graph."""
        with self._lock:
            self._entities.clear()
            self._relationships.clear()
            self._name_to_entity.clear()
            self._outgoing.clear()
            self._incoming.clear()
            self._save()

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        by_type: Dict[str, int] = {}
        by_relation: Dict[str, int] = {}

        for entity in self._entities.values():
            by_type[entity.entity_type.value] = by_type.get(entity.entity_type.value, 0) + 1

        for rel in self._relationships.values():
            by_relation[rel.relation_type] = by_relation.get(rel.relation_type, 0) + 1

        return {
            "total_entities": len(self._entities),
            "total_relationships": len(self._relationships),
            "entities_by_type": by_type,
            "relationships_by_type": by_relation,
        }


# Global instance
_graph: Optional[KnowledgeGraph] = None
_global_lock = threading.Lock()


def get_knowledge_graph(storage_path: Optional[Path] = None) -> KnowledgeGraph:
    """Get or create the global knowledge graph."""
    global _graph
    with _global_lock:
        if _graph is None:
            _graph = KnowledgeGraph(storage_path)
        return _graph


def reset_knowledge_graph() -> None:
    """Reset the global graph (for testing)."""
    global _graph
    with _global_lock:
        _graph = None
