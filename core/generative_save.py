#!/usr/bin/env python3
"""
Save/Load system for GenerativeGameEngine
Handles serialization and recovery of complete game sessions
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Optional
from dataclasses import asdict


# DATA_DIR lets a PaaS deploy point all persistence at a mounted volume
# (ephemeral container FS otherwise loses saves on every restart).
SAVES_DIR = Path(os.environ.get("DATA_DIR", ".")) / "saves" / "generative"
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_-]")
_MAX_ID_LEN = 128


class GenerativeSave:
    """
    Manages save/load for GenerativeGameEngine.
    Serializes GameState to JSON and reconstructs it on load.
    """

    @staticmethod
    def _safe_id(session_id: str) -> str:
        """
        Sanitize a session id for use as a filename.

        Strips anything outside [A-Za-z0-9_-] (defeating path traversal like
        ``../../etc``) and bounds the length. Raises ValueError if nothing
        usable remains.
        """
        if not session_id:
            raise ValueError("session_id is empty")
        cleaned = _SAFE_ID_RE.sub("", str(session_id))[:_MAX_ID_LEN]
        if not cleaned:
            raise ValueError(f"session_id has no filename-safe characters: {session_id!r}")
        return cleaned

    @staticmethod
    def _save_path(session_id: str) -> Path:
        """Get the file path for a save, sanitized and confined to SAVES_DIR."""
        path = (SAVES_DIR / f"{GenerativeSave._safe_id(session_id)}.json")
        # Defense in depth: ensure the resolved path stays inside SAVES_DIR.
        resolved = path.resolve()
        root = SAVES_DIR.resolve()
        if not (resolved == root / resolved.name and resolved.parent == root):
            raise ValueError(f"save path escapes SAVES_DIR: {resolved}")
        return path

    @staticmethod
    def save(state, session_id: str, model: str, location_state=None, sanity_system=None,
             app_state: Optional[Dict] = None, adventure: Optional[str] = None,
             language: str = "en", companions=None) -> str:
        """
        Serialize game state to JSON file.

        Args:
            state: GameState dataclass instance
            session_id: Unique session identifier
            model: LLM model used in this session
            location_state: Optional LocationStateManager for dynamic world state
            sanity_system: Optional SanitySystem (disorders, breaking points)

        Returns:
            Path to the saved file
        """
        SAVES_DIR.mkdir(parents=True, exist_ok=True)

        # Serialize location state if available
        location_state_data = None
        if location_state:
            location_state_data = location_state.to_dict()

        # Serialize sanity state if available
        sanity_state_data = None
        if sanity_system:
            sanity_state_data = sanity_system.to_dict()

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
                "adventure": adventure,  # which adventure config to rebuild with on load
                "language": language,    # narration language to resume in
                "play_duration": len(state.narrative)  # Rough estimate of gameplay length
            },
            "game_state": asdict(state),
            "location_state": location_state_data,
            "sanity_state": sanity_state_data,
            "companions_state": companions.to_dict() if companions else None,
            "app_state": app_state  # app-layer state (e.g. web pending_roll) not in GameState
        }

        path = GenerativeSave._save_path(session_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        return str(path)

    @staticmethod
    def load(session_id: str) -> Tuple[Dict, Dict, Optional[Dict], Optional[Dict]]:
        """
        Load saved game from disk.

        Args:
            session_id: Unique session identifier

        Returns:
            Tuple of (metadata_dict, game_state_dict,
            location_state_dict or None, sanity_state_dict or None)

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
            data.get("location_state"),
            data.get("sanity_state")
        )

    @staticmethod
    def load_companions_state(session_id: str) -> Optional[Dict]:
        """Return the serialized CompanionManager stored with a save, or None."""
        path = GenerativeSave._save_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("companions_state")
        except Exception:
            return None

    @staticmethod
    def load_app_state(session_id: str) -> Optional[Dict]:
        """
        Return the app-layer state stored alongside a save (e.g. the web
        pending_roll), or None if the save or the field is absent.
        """
        path = GenerativeSave._save_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("app_state")
        except Exception:
            return None

    @staticmethod
    def exists(session_id: str) -> bool:
        """True if a save file exists for this session id."""
        try:
            return GenerativeSave._save_path(session_id).exists()
        except ValueError:
            return False

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
            metadata, state_dict, _, _ = GenerativeSave.load(session_id)

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
