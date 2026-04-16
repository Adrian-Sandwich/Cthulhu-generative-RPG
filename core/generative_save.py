#!/usr/bin/env python3
"""
Save/Load system for GenerativeGameEngine
Handles serialization and recovery of complete game sessions
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Optional
from dataclasses import asdict


SAVES_DIR = Path("saves/generative")


class GenerativeSave:
    """
    Manages save/load for GenerativeGameEngine.
    Serializes GameState to JSON and reconstructs it on load.
    """

    @staticmethod
    def _save_path(session_id: str) -> Path:
        """Get the file path for a save"""
        return SAVES_DIR / f"{session_id}.json"

    @staticmethod
    def save(state, session_id: str, model: str, location_state=None, sanity_system=None) -> str:
        """
        Serialize game state to JSON file.

        Args:
            state: GameState dataclass instance
            session_id: Unique session identifier
            model: LLM model used in this session
            location_state: Optional LocationStateManager for dynamic world state
            sanity_system: Optional SanitySystem (reconstructed from state on load)

        Returns:
            Path to the saved file
        """
        SAVES_DIR.mkdir(parents=True, exist_ok=True)

        # Serialize location state if available
        location_state_data = None
        if location_state:
            location_state_data = location_state.to_dict()

        save_data = {
            "metadata": {
                "session_id": session_id,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "turn": state.turn,
                "investigator": state.investigator.name,
                "location": state.location,
                "sanity": state.investigator.characteristics.get("SAN", 75),
                "phase": state.game_phase,
                "play_duration": len(state.narrative)  # Rough estimate of gameplay length
            },
            "game_state": asdict(state),
            "location_state": location_state_data
        }

        path = GenerativeSave._save_path(session_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        return str(path)

    @staticmethod
    def load(session_id: str) -> Tuple[Dict, Dict, Optional[Dict]]:
        """
        Load saved game from disk.

        Args:
            session_id: Unique session identifier

        Returns:
            Tuple of (metadata_dict, game_state_dict, location_state_dict or None)

        Raises:
            FileNotFoundError: If save file doesn't exist
        """
        path = GenerativeSave._save_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Save not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return (
            data["metadata"],
            data["game_state"],
            data.get("location_state")
        )

    @staticmethod
    def list_saves() -> List[Dict]:
        """
        List all available saves with metadata.

        Returns:
            List of metadata dicts, sorted by timestamp (newest first)
        """
        if not SAVES_DIR.exists():
            return []

        saves = []
        for path in SAVES_DIR.glob("*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                saves.append(data["metadata"])
            except Exception:
                continue

        return sorted(saves, key=lambda x: x.get("timestamp", ""), reverse=True)

    @staticmethod
    def get_session_summary(session_id: str) -> Optional[Dict]:
        """
        Get a summary of a saved session for display before resuming.

        Args:
            session_id: Session identifier

        Returns:
            Dict with session summary, or None if not found
        """
        try:
            metadata, state_dict, _ = GenerativeSave.load(session_id)

            inv = state_dict.get("investigator", {})
            sanity = inv.get("characteristics", {}).get("SAN", 75)

            # Determine status emoji based on sanity
            if sanity >= 75:
                status = "🟢"  # Stable
            elif sanity >= 50:
                status = "🟡"  # Stressed
            elif sanity >= 25:
                status = "🔴"  # Traumatized
            else:
                status = "⚫"  # Critical

            return {
                "session_id": session_id,
                "investigator": inv.get("name", "Unknown"),
                "location": metadata.get("location", "Unknown"),
                "turn": metadata.get("turn", 0),
                "sanity": sanity,
                "status": status,
                "phase": metadata.get("phase", "exploring"),
                "saved": metadata.get("timestamp", "Unknown"),
                "play_duration": metadata.get("play_duration", 0)
            }
        except Exception:
            return None

    @staticmethod
    def list_saves_with_summaries() -> List[Dict]:
        """
        List all available saves with detailed summaries.

        Returns:
            List of summary dicts, sorted by timestamp (newest first)
        """
        summaries = []
        for metadata in GenerativeSave.list_saves():
            session_id = metadata.get("session_id")
            if session_id:
                summary = GenerativeSave.get_session_summary(session_id)
                if summary:
                    summaries.append(summary)

        return summaries

    @staticmethod
    def delete(session_id: str):
        """Delete a save file"""
        path = GenerativeSave._save_path(session_id)
        if path.exists():
            path.unlink()
