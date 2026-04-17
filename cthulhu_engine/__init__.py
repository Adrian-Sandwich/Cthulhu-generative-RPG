"""Cthulhu Game Engine v1

A procedurally-generated Call of Cthulhu 7e adventure engine with LLM narration.
"""

from .state import GameState, InvestigatorState, CoC7eRulesEngine

__version__ = "1.0.0"
__all__ = ["GameState", "InvestigatorState", "CoC7eRulesEngine"]
