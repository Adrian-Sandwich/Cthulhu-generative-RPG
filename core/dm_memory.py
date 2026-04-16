#!/usr/bin/env python3
"""
DM Memory System - Semantic memory for the AI Dungeon Master
Uses ChromaDB for persistent vector storage of narrative fragments and NPC interactions
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

# Cthulhu-specific fact extraction prompt for mem0ai
CTHULHU_FACT_PROMPT = """
Extract key facts from this Call of Cthulhu investigation.
Focus on:
- Events: What happened, where, when, sequence of actions
- Discoveries: Clues, documents, evidence found, their significance
- Horror: Sanity losses, what caused them, investigator's mental state
- NPCs: Who they are, what they revealed, their attitudes, their secrets or warnings
- Items: What was found, used, lost, or discovered - especially artifacts and clues
- Location: Where the investigator is, what they found there, environmental details
- Danger: Threats encountered (creatures, cultists, phenomena), their nature, status (alive/dead/escaped)
- Relationships: How people/creatures relate to each other, connections to the mystery
- Mysteries: What questions remain unanswered, what patterns are emerging

Ignore generic descriptions, failed actions with no consequence, or repeated information.
Output as bullet points of key facts only.
"""


class DMMemory:
    """
    Semantic memory system for the DM using ChromaDB.
    Stores narrative fragments and NPC interactions for context-aware retrieval.
    Gracefully degrades if ChromaDB is unavailable.
    """

    def __init__(self, session_id: str, persist_dir: str = "saves/chroma"):
        """
        Initialize memory system.

        Args:
            session_id: Unique session identifier
            persist_dir: Base directory for persistent storage
        """
        self.session_id = session_id
        self.persist_dir = Path(persist_dir) / session_id
        self.enabled = False
        self.client = None
        self.narrative_collection = None
        self.npc_collection = None
        self.mem0 = None  # mem0ai client for fact extraction
        self.mem0_enabled = False

        try:
            import chromadb
            self.persist_dir.mkdir(parents=True, exist_ok=True)

            print(f"  [Initializing semantic memory... (this may take a moment on first run)]")

            self.client = chromadb.PersistentClient(path=str(self.persist_dir))

            # Get or create collections
            self.narrative_collection = self.client.get_or_create_collection(
                name=f"narrative_{session_id}",
                metadata={"hnsw:space": "cosine"}
            )

            self.npc_collection = self.client.get_or_create_collection(
                name=f"npcs_{session_id}",
                metadata={"hnsw:space": "cosine"}
            )

            self.enabled = True
            print(f"  ✓ Semantic memory ready")

        except ImportError:
            print("  [ChromaDB not available - memory disabled (graceful degradation)]")
            self.enabled = False
        except Exception as e:
            print(f"  [Memory initialization error: {e} - continuing without semantic memory]")
            self.enabled = False

        # Initialize mem0ai for fact extraction (optional, complementary to ChromaDB)
        try:
            from mem0 import Memory

            # mem0ai configuration with local Ollama
            mem0_config = {
                "llm": {
                    "provider": "ollama",
                    "config": {
                        "model": "mistral",
                        "ollama_base_url": "http://localhost:11434",
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    }
                },
                "embedder": {
                    "provider": "ollama",
                    "config": {
                        "model": "nomic-embed-text",
                        "ollama_base_url": "http://localhost:11434"
                    }
                },
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": f"mem0_facts_{session_id}",
                        "path": str(self.persist_dir / "mem0")
                    }
                }
            }

            self.mem0 = Memory.from_config(mem0_config)
            self.mem0_enabled = True
            print(f"  ✓ Fact extraction (mem0ai) ready")

        except ImportError:
            # mem0ai not installed - that's ok, fall back to ChromaDB
            pass
        except Exception as e:
            # mem0ai initialization failed - gracefully degrade
            self.mem0_enabled = False

    def add_narrative(self, text: str, turn: int, metadata: Optional[Dict] = None) -> bool:
        """
        Add a narrative fragment (Player action or DM response) to semantic memory.

        Args:
            text: Fragment of narrative
            turn: Turn number
            metadata: Additional metadata (location, phase, speaker, etc.)

        Returns:
            True if successfully stored, False otherwise
        """
        if not self.enabled or not self.narrative_collection:
            return False

        try:
            # Create deterministic ID based on content
            doc_id = f"turn_{turn}_{hashlib.md5(text[:100].encode()).hexdigest()[:8]}"

            # Prepare metadata
            meta = metadata or {}
            meta['turn'] = turn
            meta['speaker'] = meta.get('speaker', 'Unknown')

            # Add to collection (embeddings computed automatically)
            self.narrative_collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            # Graceful failure - don't interrupt game
            return False

    def query_relevant(self, query: str, n_results: int = 5) -> List[str]:
        """
        Search for semantically relevant narrative fragments.

        Args:
            query: Search query (usually the player's current action)
            n_results: Number of results to return

        Returns:
            List of relevant narrative fragments, or empty list if memory unavailable
        """
        if not self.enabled or not self.narrative_collection:
            return []

        try:
            # Query by semantic similarity
            results = self.narrative_collection.query(
                query_texts=[query],
                n_results=min(n_results, 10),  # Cap at 10
                include=["documents", "distances"]
            )

            # Return documents with reasonable distance threshold (> 0.3 similarity)
            if results and results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                distances = results['distances'][0]

                # Filter by similarity score (distance < 1.0 means some similarity)
                relevant = [doc for doc, dist in zip(docs, distances) if dist < 1.0]
                return relevant

            return []
        except Exception as e:
            # Graceful failure
            return []

    def add_npc_interaction(self, npc_key: str, question: str, response: str, turn: int) -> bool:
        """
        Store an NPC interaction for future context retrieval.

        Args:
            npc_key: Identifier for the NPC (e.g., 'warner', 'armitage')
            question: Question asked by the player
            response: Response from the NPC
            turn: Turn number when interaction occurred

        Returns:
            True if successfully stored, False otherwise
        """
        if not self.enabled or not self.npc_collection:
            return False

        try:
            doc_id = f"npc_{npc_key}_{turn}"
            document = f"Q: {question}\nA: {response}"
            metadata = {
                'npc_key': npc_key,
                'turn': turn,
                'type': 'interaction'
            }

            self.npc_collection.add(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata]
            )
            return True
        except Exception:
            return False

    def query_npc_history(self, npc_key: str, current_question: str, n_results: int = 3) -> List[str]:
        """
        Retrieve relevant past interactions with a specific NPC.

        Args:
            npc_key: NPC identifier
            current_question: Current question to find similar topics
            n_results: Number of past interactions to retrieve

        Returns:
            List of relevant past interactions, or empty list if none found
        """
        if not self.enabled or not self.npc_collection:
            return []

        try:
            # Query with where filter for specific NPC
            results = self.npc_collection.query(
                query_texts=[current_question],
                n_results=min(n_results, 10),
                where={'npc_key': npc_key},
                include=["documents", "distances"]
            )

            if results and results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                distances = results['distances'][0]

                # Filter by similarity (distance < 1.2 for NPC queries)
                relevant = [doc for doc, dist in zip(docs, distances) if dist < 1.2]
                return relevant

            return []
        except Exception:
            return []

    def extract_and_store(self, text: str, turn: int, metadata: Optional[Dict] = None) -> bool:
        """
        Extract facts using mem0ai and store in semantic memory.
        Falls back to add_narrative() if mem0ai unavailable.

        Args:
            text: Narrative text to extract facts from
            turn: Turn number
            metadata: Additional metadata

        Returns:
            True if successfully stored, False otherwise
        """
        if self.mem0_enabled and self.mem0:
            try:
                # Use mem0ai to extract and store facts
                self.mem0.add(
                    text,
                    user_id=self.session_id,
                    metadata={"turn": turn, **(metadata or {})}
                )
                return True
            except Exception:
                # Fall back to ChromaDB if mem0ai fails
                return self.add_narrative(text, turn, metadata)
        else:
            # Fall back to ChromaDB if mem0ai not available
            return self.add_narrative(text, turn, metadata)

    def query_relevant_facts(self, query: str, n: int = 5) -> List[str]:
        """
        Search for facts using mem0ai semantic search.
        Falls back to existing query_relevant() if mem0ai unavailable.

        Args:
            query: Search query
            n: Number of results to return

        Returns:
            List of relevant facts or narrative fragments
        """
        if self.mem0_enabled and self.mem0:
            try:
                # Search using mem0ai
                results = self.mem0.search(
                    query=query,
                    user_id=self.session_id,
                    limit=n
                )
                if results and 'results' in results:
                    # Extract memory content from results
                    return [r.get('memory', '') for r in results.get('results', [])
                            if r.get('memory')]
            except Exception:
                pass

        # Fall back to ChromaDB search
        return self.query_relevant(query, n)

    def persist(self):
        """
        Explicitly persist collections to disk.
        In newer ChromaDB versions with PersistentClient, this is automatic,
        but we call it for compatibility and to ensure flush.
        Also persists mem0ai memory if available.
        """
        if not self.enabled or not self.client:
            return

        try:
            # ChromaDB >= 0.4 with PersistentClient handles persistence automatically
            # This is a no-op for newer versions, but kept for API consistency
            if hasattr(self.client, 'persist'):
                self.client.persist()
        except Exception:
            pass

        # Persist mem0ai memory if available
        if self.mem0_enabled and self.mem0:
            try:
                if hasattr(self.mem0, 'persist'):
                    self.mem0.persist()
            except Exception:
                pass

    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about stored collections.

        Returns:
            Dictionary with collection sizes and metadata
        """
        if not self.enabled:
            return {"narrative_count": 0, "npc_count": 0, "enabled": False}

        try:
            narrative_count = self.narrative_collection.count() if self.narrative_collection else 0
            npc_count = self.npc_collection.count() if self.npc_collection else 0

            return {
                "narrative_count": narrative_count,
                "npc_count": npc_count,
                "enabled": True,
                "session_id": self.session_id
            }
        except Exception:
            return {"enabled": False, "error": "Could not retrieve stats"}
