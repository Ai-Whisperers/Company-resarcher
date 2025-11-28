"""Tests for the personal knowledge graph system."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.knowledge_graph import (
    Entity,
    EntityType,
    GraphPath,
    KnowledgeGraph,
    Relationship,
    RelationType,
    Triple,
    TripleExtractor,
    get_knowledge_graph,
    reset_knowledge_graph,
)


class TestEntity:
    """Tests for Entity class."""

    def test_create_entity(self):
        """Test creating an entity."""
        entity = Entity(
            entity_id="ent_1",
            name="John Doe",
            entity_type=EntityType.PERSON,
        )

        assert entity.entity_id == "ent_1"
        assert entity.name == "John Doe"
        assert entity.entity_type == EntityType.PERSON

    def test_to_dict(self):
        """Test serialization."""
        entity = Entity(
            entity_id="ent_1",
            name="Acme Corp",
            entity_type=EntityType.ORGANIZATION,
            aliases=["Acme", "ACME Inc"],
            description="A fictional company",
        )
        data = entity.to_dict()

        assert data["name"] == "Acme Corp"
        assert data["entity_type"] == "organization"
        assert len(data["aliases"]) == 2

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "entity_id": "ent_2",
            "name": "Project X",
            "entity_type": "project",
            "aliases": ["X Project"],
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }
        entity = Entity.from_dict(data)

        assert entity.entity_id == "ent_2"
        assert entity.entity_type == EntityType.PROJECT


class TestRelationship:
    """Tests for Relationship class."""

    def test_create_relationship(self):
        """Test creating a relationship."""
        rel = Relationship(
            relationship_id="rel_1",
            source_id="ent_1",
            target_id="ent_2",
            relation_type="WORKS_AT",
        )

        assert rel.relationship_id == "rel_1"
        assert rel.relation_type == "WORKS_AT"
        assert rel.weight == 1.0

    def test_to_dict(self):
        """Test serialization."""
        rel = Relationship(
            relationship_id="rel_1",
            source_id="ent_1",
            target_id="ent_2",
            relation_type="MANAGES",
            weight=2.0,
            confidence=0.9,
        )
        data = rel.to_dict()

        assert data["relation_type"] == "MANAGES"
        assert data["weight"] == 2.0
        assert data["confidence"] == 0.9


class TestTriple:
    """Tests for Triple class."""

    def test_create_triple(self):
        """Test creating a triple."""
        triple = Triple(
            subject="Alice",
            predicate="WORKS_AT",
            object="Acme Corp",
            subject_type=EntityType.PERSON,
            object_type=EntityType.ORGANIZATION,
        )

        assert triple.subject == "Alice"
        assert triple.predicate == "WORKS_AT"
        assert triple.object == "Acme Corp"


class TestTripleExtractor:
    """Tests for TripleExtractor class."""

    def setup_method(self):
        """Create extractor."""
        self.extractor = TripleExtractor()

    def test_extract_works_at(self):
        """Test extracting WORKS_AT relationship."""
        text = "John works at Microsoft."
        triples = self.extractor.extract(text)

        assert len(triples) >= 1
        assert any(t.predicate == "WORKS_AT" for t in triples)

    def test_extract_works_on(self):
        """Test extracting WORKS_ON relationship."""
        text = "Alice works on Project Alpha."
        triples = self.extractor.extract(text)

        assert len(triples) >= 1
        assert any(t.predicate == "WORKS_ON" for t in triples)

    def test_extract_manages(self):
        """Test extracting MANAGES relationship."""
        text = "Bob manages the engineering team."
        triples = self.extractor.extract(text)

        assert len(triples) >= 1
        assert any(t.predicate == "MANAGES" for t in triples)

    def test_extract_located_in(self):
        """Test extracting LOCATED_IN relationship."""
        text = "The office is located in New York."
        triples = self.extractor.extract(text)

        assert len(triples) >= 1
        assert any(t.predicate == "LOCATED_IN" for t in triples)

    def test_extract_multiple(self):
        """Test extracting multiple relationships."""
        text = "Alice works at Google. She manages the AI team."
        triples = self.extractor.extract(text)

        assert len(triples) >= 2

    def test_extract_no_match(self):
        """Test text with no relationships."""
        text = "The weather is nice today."
        triples = self.extractor.extract(text)

        assert len(triples) == 0


class TestGraphPath:
    """Tests for GraphPath class."""

    def test_path_length(self):
        """Test path length calculation."""
        entities = [
            Entity("e1", "A", EntityType.PERSON),
            Entity("e2", "B", EntityType.PERSON),
            Entity("e3", "C", EntityType.PERSON),
        ]
        rels = [
            Relationship("r1", "e1", "e2", "KNOWS"),
            Relationship("r2", "e2", "e3", "KNOWS"),
        ]
        path = GraphPath(entities=entities, relationships=rels)

        assert path.length == 2

    def test_to_dict(self):
        """Test serialization."""
        entities = [
            Entity("e1", "Alice", EntityType.PERSON),
            Entity("e2", "Bob", EntityType.PERSON),
        ]
        rels = [
            Relationship("r1", "e1", "e2", "KNOWS", weight=1.5),
        ]
        path = GraphPath(entities=entities, relationships=rels, total_weight=1.5)

        data = path.to_dict()

        assert data["entities"] == ["Alice", "Bob"]
        assert data["relationships"] == ["KNOWS"]
        assert data["length"] == 1


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = KnowledgeGraph(Path(self.temp_dir))

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_entity(self):
        """Test adding an entity."""
        entity = self.graph.add_entity(
            name="John Doe",
            entity_type=EntityType.PERSON,
            description="A test person",
        )

        assert entity.entity_id is not None
        assert entity.name == "John Doe"

    def test_add_entity_with_aliases(self):
        """Test adding entity with aliases."""
        entity = self.graph.add_entity(
            name="Microsoft Corporation",
            entity_type=EntityType.ORGANIZATION,
            aliases=["Microsoft", "MSFT"],
        )

        # Should find by alias
        found = self.graph.get_entity("Microsoft")
        assert found is not None
        assert found.entity_id == entity.entity_id

    def test_add_relationship(self):
        """Test adding a relationship."""
        rel = self.graph.add_relationship(
            source_name="Alice",
            target_name="Acme Corp",
            relation_type="WORKS_AT",
            source_type=EntityType.PERSON,
            target_type=EntityType.ORGANIZATION,
        )

        assert rel.relationship_id is not None
        assert rel.relation_type == "WORKS_AT"

        # Entities should be created
        assert self.graph.get_entity("Alice") is not None
        assert self.graph.get_entity("Acme Corp") is not None

    def test_add_triple(self):
        """Test adding a triple."""
        triple = Triple(
            subject="Bob",
            predicate="MANAGES",
            object="Project X",
            subject_type=EntityType.PERSON,
            object_type=EntityType.PROJECT,
        )

        rel = self.graph.add_triple(triple)

        assert rel.source_id is not None
        assert rel.target_id is not None

    def test_extract_and_add(self):
        """Test extracting and adding from text."""
        text = "Alice works at Google. Bob manages the team."

        relationships = self.graph.extract_and_add(text)

        assert len(relationships) >= 2

    def test_get_entity(self):
        """Test getting an entity."""
        self.graph.add_entity("Test Entity", EntityType.CUSTOM)

        entity = self.graph.get_entity("Test Entity")

        assert entity is not None
        assert entity.name == "Test Entity"

    def test_get_entity_by_id(self):
        """Test getting entity by ID."""
        added = self.graph.add_entity("Entity", EntityType.CUSTOM)

        entity = self.graph.get_entity(added.entity_id)

        assert entity is not None

    def test_get_relationships(self):
        """Test getting relationships for an entity."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")
        self.graph.add_relationship("Alice", "Carol", "WORKS_WITH")
        self.graph.add_relationship("David", "Alice", "REPORTS_TO")

        # Outgoing
        outgoing = self.graph.get_relationships("Alice", direction="outgoing")
        assert len(outgoing) == 2

        # Incoming
        incoming = self.graph.get_relationships("Alice", direction="incoming")
        assert len(incoming) == 1

        # Both
        both = self.graph.get_relationships("Alice", direction="both")
        assert len(both) == 3

    def test_get_relationships_filtered(self):
        """Test filtering relationships by type."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")
        self.graph.add_relationship("Alice", "Carol", "MANAGES")

        knows = self.graph.get_relationships("Alice", relation_type="KNOWS")
        assert len(knows) == 1
        assert knows[0][0].relation_type == "KNOWS"

    def test_find_path(self):
        """Test finding path between entities."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")
        self.graph.add_relationship("Bob", "Carol", "KNOWS")
        self.graph.add_relationship("Carol", "David", "KNOWS")

        path = self.graph.find_path("Alice", "Carol")

        assert path is not None
        assert path.length == 2

    def test_find_path_direct(self):
        """Test finding direct path."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")

        path = self.graph.find_path("Alice", "Bob")

        assert path is not None
        assert path.length == 1

    def test_find_path_no_connection(self):
        """Test no path exists."""
        self.graph.add_entity("Alice", EntityType.PERSON)
        self.graph.add_entity("Bob", EntityType.PERSON)

        path = self.graph.find_path("Alice", "Bob")

        assert path is None

    def test_search_entities(self):
        """Test searching entities."""
        self.graph.add_entity("Alice Smith", EntityType.PERSON)
        self.graph.add_entity("Alice Johnson", EntityType.PERSON)
        self.graph.add_entity("Bob Smith", EntityType.PERSON)

        results = self.graph.search_entities("Alice")

        assert len(results) == 2
        assert all("Alice" in e.name for e in results)

    def test_search_entities_by_type(self):
        """Test searching with type filter."""
        self.graph.add_entity("Apple", EntityType.ORGANIZATION)
        self.graph.add_entity("Apple Pie", EntityType.PRODUCT)

        results = self.graph.search_entities("Apple", entity_type=EntityType.ORGANIZATION)

        assert len(results) == 1
        assert results[0].entity_type == EntityType.ORGANIZATION

    def test_get_neighbors(self):
        """Test getting neighboring entities."""
        self.graph.add_relationship("A", "B", "KNOWS")
        self.graph.add_relationship("B", "C", "KNOWS")
        self.graph.add_relationship("C", "D", "KNOWS")

        neighbors = self.graph.get_neighbors("A", depth=2)

        assert 0 in neighbors
        assert 1 in neighbors
        assert 2 in neighbors
        assert neighbors[1][0].name == "B"

    def test_remove_entity(self):
        """Test removing an entity."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")

        success = self.graph.remove_entity("Alice")

        assert success
        assert self.graph.get_entity("Alice") is None

    def test_clear(self):
        """Test clearing the graph."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")
        self.graph.add_entity("Carol", EntityType.PERSON)

        self.graph.clear()

        stats = self.graph.get_statistics()
        assert stats["total_entities"] == 0
        assert stats["total_relationships"] == 0

    def test_get_statistics(self):
        """Test getting statistics."""
        self.graph.add_entity("Alice", EntityType.PERSON)
        self.graph.add_entity("Google", EntityType.ORGANIZATION)
        self.graph.add_relationship("Alice", "Google", "WORKS_AT")

        stats = self.graph.get_statistics()

        assert stats["total_entities"] == 2
        assert stats["total_relationships"] == 1
        assert "person" in stats["entities_by_type"]
        assert "WORKS_AT" in stats["relationships_by_type"]

    def test_persistence(self):
        """Test graph persists across instances."""
        self.graph.add_relationship("Alice", "Bob", "KNOWS")

        # Create new graph with same storage
        new_graph = KnowledgeGraph(Path(self.temp_dir))

        entity = new_graph.get_entity("Alice")
        assert entity is not None


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_knowledge_graph()

    def teardown_method(self):
        """Reset after each test."""
        reset_knowledge_graph()

    def test_get_knowledge_graph_singleton(self):
        """Test singleton behavior."""
        g1 = get_knowledge_graph()
        g2 = get_knowledge_graph()
        assert g1 is g2

    def test_reset_knowledge_graph(self):
        """Test resetting singleton."""
        g1 = get_knowledge_graph()
        reset_knowledge_graph()
        g2 = get_knowledge_graph()
        assert g1 is not g2


class TestEntityTypes:
    """Tests for entity type enums."""

    def test_all_entity_types(self):
        """Test all entity types exist."""
        types = [
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            EntityType.LOCATION,
            EntityType.PROJECT,
            EntityType.CONCEPT,
            EntityType.DOCUMENT,
            EntityType.EVENT,
            EntityType.PRODUCT,
            EntityType.TECHNOLOGY,
            EntityType.DATE,
            EntityType.CUSTOM,
        ]
        assert len(types) == len(EntityType)

    def test_relation_types(self):
        """Test relation types."""
        types = [
            RelationType.WORKS_AT,
            RelationType.MANAGES,
            RelationType.KNOWS,
            RelationType.LOCATED_IN,
        ]
        assert len(types) > 0
