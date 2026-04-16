#!/usr/bin/env python3
"""
Entity Relationship Graph using Neo4j for Cthulhu AI Game.
Tracks NPC relationships, factions, locations, and knowledge connections
to inform DM narrative and detect conspiracies.
"""

from typing import Dict, List, Optional, Tuple

try:
    from neo4j import GraphDatabase, Session
except ImportError:
    GraphDatabase = None
    Session = None


class EntityGraph:
    """
    Neo4j-based entity relationship graph.
    Tracks NPCs, locations, factions, artifacts, and their interconnections.
    """

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = None
        self.session: Optional[Session] = None
        self.enabled = False

        if GraphDatabase is None:
            print("  [neo4j package not installed - entity relationships disabled (graceful degradation)]")
            return

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))

            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")

            self.enabled = True
            print("  ✓ Neo4j entity graph ready")
        except Exception as e:
            print(f"  [Neo4j unavailable: {e} - entity relationships disabled (graceful degradation)]")
            self.driver = None
            self.enabled = False

    def _get_session(self) -> Optional[Session]:
        """Get or create session"""
        if not self.enabled or not self.driver:
            return None
        return self.driver.session()

    def add_npc(self, key: str, name: str, role: str, faction_key: Optional[str] = None, metadata: Dict = None) -> bool:
        """
        Add NPC node to graph.

        Args:
            key: Unique identifier (e.g., 'warner')
            name: Display name (e.g., 'Lt. William Warner')
            role: Occupation/role
            faction_key: Optional faction identifier
            metadata: Additional properties

        Returns:
            True if successful, False if Neo4j unavailable
        """
        if not self.enabled:
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            meta = metadata or {}
            query = """
            MERGE (npc:NPC {key: $key})
            SET npc.name = $name, npc.role = $role, npc.properties = $meta
            RETURN npc
            """
            session.run(query, key=key, name=name, role=role, meta=meta)

            # Assign to faction if provided
            if faction_key:
                self.add_relationship(key, "WORKS_FOR", faction_key)

            session.close()
            return True
        except Exception:
            return False

    def add_location(self, key: str, name: str, description: str = "") -> bool:
        """
        Add location node to graph.

        Args:
            key: Unique identifier (e.g., 'lighthouse_exterior')
            name: Display name
            description: Location description

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            query = """
            MERGE (loc:Location {key: $key})
            SET loc.name = $name, loc.description = $description
            RETURN loc
            """
            session.run(query, key=key, name=name, description=description)
            session.close()
            return True
        except Exception:
            return False

    def add_faction(self, key: str, name: str, alignment: str = "neutral") -> bool:
        """
        Add faction node.

        Args:
            key: Unique identifier
            name: Faction name
            alignment: Alignment description (e.g., 'hostile', 'neutral', 'allied')

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            query = """
            MERGE (f:Faction {key: $key})
            SET f.name = $name, f.alignment = $alignment
            RETURN f
            """
            session.run(query, key=key, name=name, alignment=alignment)
            session.close()
            return True
        except Exception:
            return False

    def add_relationship(self, from_key: str, rel_type: str, to_key: str, metadata: Dict = None) -> bool:
        """
        Add relationship between entities.

        Args:
            from_key: Source entity key
            rel_type: Relationship type (KNOWS, WORKS_FOR, FEARS, PROTECTS, etc.)
            to_key: Target entity key
            metadata: Additional properties on relationship

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            meta = metadata or {}
            query = f"""
            MATCH (a {{key: $from_key}}), (b {{key: $to_key}})
            MERGE (a)-[r:{rel_type}]-(b)
            SET r.properties = $meta
            RETURN r
            """
            session.run(query, from_key=from_key, to_key=to_key, meta=meta)
            session.close()
            return True
        except Exception:
            return False

    def get_npc_relationships(self, npc_key: str) -> Dict[str, List[str]]:
        """
        Get all relationships for an NPC.

        Args:
            npc_key: NPC identifier

        Returns:
            Dict with relationship types as keys and entity lists as values
        """
        if not self.enabled:
            return {}

        try:
            session = self._get_session()
            if not session:
                return {}

            query = """
            MATCH (npc:NPC {key: $key})-[r]-(other)
            RETURN type(r) as rel_type, collect(other.key) as targets
            """
            result = session.run(query, key=npc_key)

            relationships = {}
            for record in result:
                rel_type = record["rel_type"].lower()
                targets = record["targets"]
                relationships[rel_type] = targets

            session.close()
            return relationships
        except Exception:
            return {}

    def get_npc_context(self, npc_key: str) -> str:
        """
        Generate narrative context about an NPC's relationships.

        Args:
            npc_key: NPC identifier

        Returns:
            Formatted text suitable for DM prompt injection
        """
        if not self.enabled:
            return ""

        try:
            relationships = self.get_npc_relationships(npc_key)
            if not relationships:
                return ""

            context_parts = []

            if "knows" in relationships and relationships["knows"]:
                known = ", ".join(relationships["knows"][:3])
                context_parts.append(f"Knows: {known}")

            if "works_for" in relationships and relationships["works_for"]:
                faction = relationships["works_for"][0] if relationships["works_for"] else None
                if faction:
                    context_parts.append(f"Works for: {faction}")

            if "fears" in relationships and relationships["fears"]:
                feared = ", ".join(relationships["fears"][:2])
                context_parts.append(f"Fears: {feared}")

            if "protects" in relationships and relationships["protects"]:
                protected = relationships["protects"][0] if relationships["protects"] else None
                if protected:
                    context_parts.append(f"Protects: {protected}")

            return " | ".join(context_parts) if context_parts else ""
        except Exception:
            return ""

    def find_connection_path(self, from_key: str, to_key: str, max_depth: int = 3) -> Optional[List[Tuple[str, str]]]:
        """
        Find relationship path between two entities (conspiracy detection).

        Args:
            from_key: Source entity
            to_key: Target entity
            max_depth: Maximum relationship steps to traverse

        Returns:
            List of (entity_key, relationship_type) tuples, or None if no path
        """
        if not self.enabled:
            return None

        try:
            session = self._get_session()
            if not session:
                return None

            query = f"""
            MATCH path = shortestPath(
                (a {{key: $from_key}})-[*1..{max_depth}]-(b {{key: $to_key}})
            )
            RETURN path
            LIMIT 1
            """
            result = session.run(query, from_key=from_key, to_key=to_key)

            for record in result:
                path = record["path"]
                # Convert path to list of steps
                steps = []
                for rel in path.relationships:
                    steps.append((rel.start_node["key"], type(rel).__name__))
                session.close()
                return steps

            session.close()
            return None
        except Exception:
            return None

    def get_faction_members(self, faction_key: str) -> List[str]:
        """
        Get all NPC members of a faction.

        Args:
            faction_key: Faction identifier

        Returns:
            List of NPC keys
        """
        if not self.enabled:
            return []

        try:
            session = self._get_session()
            if not session:
                return []

            query = """
            MATCH (npc:NPC)-[:WORKS_FOR]-(f:Faction {key: $faction_key})
            RETURN collect(npc.key) as members
            """
            result = session.run(query, faction_key=faction_key)

            for record in result:
                session.close()
                return record["members"] or []

            session.close()
            return []
        except Exception:
            return []

    def get_graph_stats(self) -> Dict[str, int]:
        """
        Get statistics about the graph.

        Returns:
            Dict with node and relationship counts
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            session = self._get_session()
            if not session:
                return {"enabled": False}

            query = """
            MATCH (n)
            RETURN
              COUNT(DISTINCT n {.*}) as nodes,
              SIZE(relationships(n)) as relationships
            LIMIT 1
            """
            result = session.run(query)

            stats = {"enabled": True}
            for record in result:
                stats["nodes"] = record["nodes"]
                stats["relationships"] = record["relationships"]

            session.close()
            return stats
        except Exception:
            return {"enabled": False}

    def clear(self) -> bool:
        """
        Clear all nodes and relationships from graph.

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            session.run("MATCH (n) DETACH DELETE n")
            session.close()
            return True
        except Exception:
            return False

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
