#!/usr/bin/env python3
"""
Graphics Engine v1 - Standalone
Independent visual adventure engine (no dependencies on game engine)
"""

__version__ = "1.0.0"
__author__ = "Cthulhu Graphics Team"

from .snapshot import Snapshot, GameStateSnapshot
from .storage import SnapshotStorage

__all__ = ["Snapshot", "GameStateSnapshot", "SnapshotStorage"]
