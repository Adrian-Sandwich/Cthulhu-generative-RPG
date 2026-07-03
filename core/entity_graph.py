#!/usr/bin/env python3
"""
Entity Relationship Graph using Neo4j for Cthulhu AI Game.
Tracks NPC relationships, factions, locations, and knowledge connections
to inform DM narrative and detect conspiracies.
"""

import logging
from typing import Dict, List, Optional, Tuple

try:
    from neo4j import GraphDatabase, Session
except ImportError:
    GraphDatabase = None
    Session = None

logger = logging.getLogger(__name__)


class EntityGraph:
    """
    Neo4j-based entity relationship graph.
    Tracks NPCs, locations, factions, artifacts, and their interconnections.

    All nodes are scoped by ``session_id`` so that concurrent games share a
    single Neo4j instance without colliding, and a game can wipe only its own
    nodes on re-initialization.
    """

    # Relationship types the engine is allowed to write. The rel type cannot be
    # parameterized in Cypher, so it is interpolated into the query string —
    # validating against this fixed set keeps that interpolation injection-safe.
    ALLOWED_RELS = {"WORKS_FOR", "KNOWS", "FEARS", "PROTECTS"}

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j",
                 password: str = "password", session_id: str = "default"):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            session_id: Scopes every node this instance creates/reads/deletes.
        """
        self.driver = None
        self.session: Optional[Session] = None
        self.session_id = session_id
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

            with session:
                meta = metadata or {}
                query = """
                MERGE (npc:NPC {key: $key, session_id: $sid})
                SET npc.name = $name, npc.role = $role, npc.properties = $meta
                RETURN npc
                """
                session.run(query, key=key, name=name, role=role, meta=meta, sid=self.session_id)

                # Assign to faction if provided
                if faction_key:
                    self.add_relationship(key, "WORKS_FOR", faction_key)

            return True
        except Exception:
            logger.warning("add_npc failed for key=%s", key, exc_info=True)
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

            with session:
                query = """
                MERGE (loc:Location {key: $key, session_id: $sid})
                SET loc.name = $name, loc.description = $description
                RETURN loc
                """
                session.run(query, key=key, name=name, description=description, sid=self.session_id)
            return True
        except Exception:
            logger.warning("add_location failed for key=%s", key, exc_info=True)
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

            with session:
                query = """
                MERGE (f:Faction {key: $key, session_id: $sid})
                SET f.name = $name, f.alignment = $alignment
                RETURN f
                """
                session.run(query, key=key, name=name, alignment=alignment, sid=self.session_id)
            return True
        except Exception:
            logger.warning("add_faction failed for key=%s", key, exc_info=True)
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

        # rel_type is interpolated into the query (Cypher can't parameterize it),
        # so reject anything outside the known-safe set to prevent injection.
        if rel_type not in self.ALLOWED_RELS:
            logger.warning("add_relationship rejected unknown rel_type=%r", rel_type)
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            with session:
                meta = metadata or {}
                query = f"""
                MATCH (a {{key: $from_key, session_id: $sid}}), (b {{key: $to_key, session_id: $sid}})
                MERGE (a)-[r:{rel_type}]-(b)
                SET r.properties = $meta
                RETURN r
                """
                session.run(query, from_key=from_key, to_key=to_key, meta=meta, sid=self.session_id)
            return True
        except Exception:
            logger.warning("add_relationship failed %s-[%s]-%s", from_key, rel_type, to_key, exc_info=True)
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

            with session:
                query = """
                MATCH (npc:NPC {key: $key, session_id: $sid})-[r]-(other {session_id: $sid})
                RETURN type(r) as rel_type, collect(other.key) as targets
                """
                result = session.run(query, key=npc_key, sid=self.session_id)

                relationships = {}
                for record in result:
                    rel_type = record["rel_type"].lower()
                    targets = record["targets"]
                    relationships[rel_type] = targets

            return relationships
        except Exception:
            logger.warning("get_npc_relationships failed for key=%s", npc_key, exc_info=True)
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
            logger.warning("get_npc_context failed for key=%s", npc_key, exc_info=True)
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

            with session:
                query = f"""
                MATCH path = shortestPath(
                    (a {{key: $from_key, session_id: $sid}})-[*1..{max_depth}]-(b {{key: $to_key, session_id: $sid}})
                )
                RETURN path
                LIMIT 1
                """
                result = session.run(query, from_key=from_key, to_key=to_key, sid=self.session_id)

                for record in result:
                    path = record["path"]
                    # Convert path to list of steps
                    steps = []
                    for rel in path.relationships:
                        steps.append((rel.start_node["key"], type(rel).__name__))
                    return steps

            return None
        except Exception:
            logger.warning("find_connection_path failed %s->%s", from_key, to_key, exc_info=True)
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

            with session:
                query = """
                MATCH (npc:NPC {session_id: $sid})-[:WORKS_FOR]-(f:Faction {key: $faction_key, session_id: $sid})
                RETURN collect(npc.key) as members
                """
                result = session.run(query, faction_key=faction_key, sid=self.session_id)

                for record in result:
                    return record["members"] or []

            return []
        except Exception:
            logger.warning("get_faction_members failed for faction=%s", faction_key, exc_info=True)
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

            with session:
                query = """
                MATCH (n {session_id: $sid})
                OPTIONAL MATCH (n)-[r {}]-(m {session_id: $sid})
                RETURN count(DISTINCT n) as nodes, count(DISTINCT r) as relationships
                """
                result = session.run(query, sid=self.session_id)

                stats = {"enabled": True}
                for record in result:
                    stats["nodes"] = record["nodes"]
                    stats["relationships"] = record["relationships"]

            return stats
        except Exception:
            logger.warning("get_graph_stats failed", exc_info=True)
            return {"enabled": False}

    def clear(self) -> bool:
        """
        Clear only THIS session's nodes and relationships.

        Scoped by ``session_id`` — never touches other games' data on a shared
        Neo4j instance.

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            session = self._get_session()
            if not session:
                return False

            with session:
                session.run("MATCH (n {session_id: $sid}) DETACH DELETE n", sid=self.session_id)
            return True
        except Exception:
            logger.warning("clear failed for session_id=%s", self.session_id, exc_info=True)
            return False

    # Explicit alias — makes the session-scoped intent obvious at call sites.
    clear_session = clear

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
