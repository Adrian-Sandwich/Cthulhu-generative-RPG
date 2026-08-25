#!/usr/bin/env python3
"""Combat mechanics for the generative game engine."""

import random
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .game_generative import GenerativeGameEngine


class CombatSystem:
    """Manages enemy definitions and combat resolution."""

    # Enemy definitions
    ENEMIES = {
        "deep_one_hybrid": {"name": "Deep One Hybrid", "hp": 12, "skill": 45, "damage": 6},
        "animated_corpse": {"name": "Animated Corpse", "hp": 8, "skill": 30, "damage": 4},
        "shadow_thing": {"name": "Shadow Entity", "hp": 20, "skill": 60, "damage": 8}
    }

    def __init__(self, engine: "GenerativeGameEngine") -> None:
        self.engine = engine

    def start_combat(self, enemy_key: str) -> Dict:
        """Start combat with an enemy"""
        state = self.engine.state
        if not state:
            return {"error": "No active game"}
        if enemy_key not in self.ENEMIES:
            return {"error": f"Enemy '{enemy_key}' not found"}

        enemy = self.ENEMIES[enemy_key].copy()
        state.active_combat = enemy
        state.game_phase = "combat"

        return {
            "enemy": enemy["name"],
            "message": f"Combat started: {enemy['name']} (HP: {enemy['hp']})"
        }

    def infer_enemy(self, text: str) -> str:
        """Best-guess enemy key from scene text (for synthesized combat).

        Cues must be SPECIFIC: "lurking in the shadows" is everyday horror
        phrasing and must not summon the deadliest enemy in the roster —
        only an explicitly shadow-natured creature does.
        """
        t = text.lower()
        if any(w in t for w in ("deep one", "fish", "amphib", "scaled", "gill", "seaweed")):
            return "deep_one_hybrid"
        if any(w in t for w in ("corpse", "dead body", "cadaver", "cadáver", "rotting", "zombie")):
            return "animated_corpse"
        if any(w in t for w in ("shadow entity", "shadow thing", "living shadow",
                                "made of shadow", "sombra viviente", "criatura de sombra")):
            return "shadow_thing"
        return "deep_one_hybrid"

    def attempt_flee(self) -> Dict:
        """Break off combat. The enemy gets one free swing as you turn to run."""
        state = self.engine.state
        if not state or not state.active_combat:
            return {"error": "Not in combat"}
        enemy = state.active_combat
        lines = ["You break away and flee into the dark."]
        roll = self.engine.rules.roll_d100()
        if roll <= enemy["skill"]:
            dmg = random.randint(1, enemy.get("damage", 4))
            hp_res = self.engine.apply_hp_damage(dmg)
            lines.insert(0, f"{enemy['name']} rakes you as you turn — {dmg} damage.")
            if hp_res.get("state") == "DEAD":
                state.active_combat = None
                return {"fled": True, "player_dead": True, "narrative": " ".join(lines)}
        state.active_combat = None
        state.game_phase = "exploring"
        return {"fled": True, "narrative": " ".join(lines)}

    def combat_attack_roll(self) -> Dict:
        """Build the pending attack check for the current combat round.

        Picks the firearm if one is loaded, otherwise brawling. Flagged
        ``combat`` so the roll endpoint resolves it as a combat round.
        """
        state = self.engine.state
        if not state:
            return {"error": "No active game"}
        inv = state.investigator
        has_gun = state.ammo > 0 and any(
            "revolver" in i.lower() or "pistol" in i.lower() for i in inv.inventory
        )
        skill = "firearms_revolver" if has_gun else "brawl"
        pending = self.engine.prepare_skill_check(skill, "Normal")
        pending["combat"] = True
        return pending

    def resolve_combat_round(self, player_roll_success: bool,
                             critical: Optional[str] = None) -> Dict:
        """Resolve one round of combat: player attack, then enemy counter.

        Crits matter: a CRITICAL SUCCESS (d100 <= 5) deals double damage and
        the staggered enemy loses its counter-attack; a CRITICAL FAILURE
        (>= 96) leaves an opening — the enemy's counter hits automatically.
        """
        state = self.engine.state
        if not state or not state.active_combat:
            return {"error": "Not in combat"}

        enemy = state.active_combat
        result = {"player_hit": False, "enemy_hit": False, "critical": critical}
        lines = []
        crit_success = critical == "CRITICAL SUCCESS"
        crit_failure = critical == "CRITICAL FAILURE"

        # Firearms consume a round when used as the attack.
        # (Ammo already spent in execute_skill_check before we get here.)

        # Player attacks
        if player_roll_success:
            damage = random.randint(2, 6) * (2 if crit_success else 1)
            enemy["hp"] -= damage
            result["player_hit"] = True
            result["player_damage"] = damage
            if crit_success:
                lines.append(f"CRITICAL! A devastating blow — {enemy['name']} takes {damage} damage.")
            else:
                lines.append(f"You strike — {enemy['name']} takes {damage} damage.")

            if enemy["hp"] <= 0:
                state.active_combat = None
                state.game_phase = "exploring"
                lines.append(f"{enemy['name']} shudders and collapses. The threat is over.")
                return {
                    **result, "combat_over": True, "enemy_dead": True,
                    "enemy_hp": 0, "narrative": " ".join(lines),
                }
        else:
            lines.append("Your attack goes wide." if not crit_failure
                         else "FUMBLE! You stumble, wide open.")

        # Enemy counter-attacks — skipped when staggered by a critical hit;
        # automatic when the player fumbled.
        if crit_success:
            lines.append(f"{enemy['name']} reels, too staggered to strike back.")
        else:
            enemy_roll = 0 if crit_failure else self.engine.rules.roll_d100()
            if enemy_roll <= enemy["skill"]:
                damage = random.randint(1, enemy.get("damage", 4))
                hp_res = self.engine.apply_hp_damage(damage)
                result["enemy_hit"] = True
                result["enemy_damage"] = damage
                lines.append(f"{enemy['name']} strikes back — you take {damage} damage.")
                if hp_res.get("state") == "DEAD":
                    state.active_combat = None
                    return {
                        **result, "combat_over": True, "player_dead": True,
                        "enemy_hp": enemy["hp"], "narrative": " ".join(lines),
                    }
            else:
                lines.append(f"{enemy['name']} lunges, but misses.")

        result["combat_over"] = False
        result["enemy_hp"] = enemy["hp"]
        result["enemy_name"] = enemy["name"]
        result["narrative"] = " ".join(lines)
        return result

    def combat_status(self) -> Optional[Dict]:
        """Current enemy for the HUD, or None when not fighting."""
        state = self.engine.state
        if not state or not state.active_combat:
            return None
        return {"name": state.active_combat["name"], "hp": state.active_combat["hp"]}
