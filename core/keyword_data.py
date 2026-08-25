#!/usr/bin/env python3
"""Keyword tables, limits, and cue sets used by the generative game engine."""

import re
from typing import Dict, List, Tuple


# Phase 2e: Fix C — Roll synthesis mapping (keyword → (skill, difficulty))
# Used when LLM omits a roll for a physical action
ROLL_KEYWORDS: Dict[str, Tuple[str, str]] = {
    # Physical exertion
    'lift': ('climb', 'Hard'),
    'push': ('brawl', 'Normal'),
    'pull': ('climb', 'Normal'),
    'pry': ('climb', 'Hard'),
    'force': ('brawl', 'Hard'),
    'break': ('brawl', 'Hard'),
    'move': ('climb', 'Normal'),
    'drag': ('climb', 'Normal'),
    'carry': ('climb', 'Normal'),

    # Climbing/swimming
    'climb': ('climb', 'Normal'),
    'climb up': ('climb', 'Normal'),
    'scale': ('climb', 'Hard'),
    'jump': ('jump', 'Normal'),
    'leap': ('jump', 'Normal'),
    'swim': ('swim', 'Normal'),
    'dodge': ('dodge', 'Normal'),
    'run': ('climb', 'Normal'),

    # Combat
    'attack': ('brawl', 'Normal'),
    'fight': ('brawl', 'Normal'),
    'hit': ('brawl', 'Normal'),
    'punch': ('brawl', 'Normal'),
    'kick': ('brawl', 'Normal'),
    'shoot': ('firearms_revolver', 'Normal'),
    'fire': ('firearms_revolver', 'Normal'),
    'stab': ('brawl', 'Normal'),
    'swing': ('brawl', 'Normal'),
    'strike': ('brawl', 'Normal'),
    'brawl': ('brawl', 'Normal'),

    # Search/Investigation
    'search': ('spot_hidden', 'Hard'),
    'search for': ('spot_hidden', 'Hard'),
    'investigate': ('investigate', 'Normal'),
    'examine': ('investigate', 'Normal'),
    'examine carefully': ('investigate', 'Normal'),
    'look for': ('spot_hidden', 'Hard'),
    'find': ('spot_hidden', 'Hard'),
    'discover': ('spot_hidden', 'Hard'),
    'spot': ('spot_hidden', 'Hard'),
    'notice': ('spot_hidden', 'Hard'),
    'check': ('investigate', 'Normal'),
    'look closely': ('investigate', 'Normal'),

    # Occult/Knowledge
    'decipher': ('occult', 'Hard'),
    'interpret': ('occult', 'Hard'),
    'read': ('occult', 'Hard'),
    'understand': ('occult', 'Hard'),

    # Social pressure
    'persuade': ('persuade', 'Normal'),
    'convince': ('persuade', 'Normal'),
    'deceive': ('persuade', 'Hard'),
    'bluff': ('persuade', 'Hard'),
    'intimidate': ('persuade', 'Normal'),
    'bribe': ('persuade', 'Normal'),

    # --- Spanish action verbs (playtest: ES players almost never rolled) ---
    # physical / climb / move
    'trepo': ('climb', 'Normal'), 'trepar': ('climb', 'Normal'),
    'escalo': ('climb', 'Normal'), 'escalar': ('climb', 'Hard'),
    'subo': ('climb', 'Normal'), 'trepar por': ('climb', 'Normal'),
    'empujo': ('brawl', 'Normal'), 'empujar': ('brawl', 'Normal'),
    'jalo': ('climb', 'Normal'), 'fuerzo': ('brawl', 'Hard'), 'forzar': ('brawl', 'Hard'),
    'rompo': ('brawl', 'Hard'), 'romper': ('brawl', 'Hard'),
    'salto': ('jump', 'Normal'), 'saltar': ('jump', 'Normal'),
    'nado': ('swim', 'Normal'), 'nadar': ('swim', 'Normal'),
    'esquivo': ('dodge', 'Normal'), 'esquivar': ('dodge', 'Normal'),
    'corro': ('climb', 'Normal'), 'huyo': ('dodge', 'Normal'),
    # combat
    'ataco': ('brawl', 'Normal'), 'atacar': ('brawl', 'Normal'),
    'golpeo': ('brawl', 'Normal'), 'golpear': ('brawl', 'Normal'),
    'peleo': ('brawl', 'Normal'), 'pelear': ('brawl', 'Normal'),
    'disparo': ('firearms_revolver', 'Normal'), 'disparar': ('firearms_revolver', 'Normal'),
    'apuñalo': ('brawl', 'Normal'), 'apuñalar': ('brawl', 'Normal'),
    # search / investigation
    'busco': ('spot_hidden', 'Hard'), 'buscar': ('spot_hidden', 'Hard'),
    'investigo': ('investigate', 'Normal'), 'investigar': ('investigate', 'Normal'),
    'examino': ('investigate', 'Normal'), 'examinar': ('investigate', 'Normal'),
    'reviso': ('investigate', 'Normal'), 'revisar': ('investigate', 'Normal'),
    'inspecciono': ('investigate', 'Normal'), 'inspeccionar': ('investigate', 'Normal'),
    'escucho': ('listen', 'Normal'), 'escuchar': ('listen', 'Normal'),
    # occult / knowledge
    'descifro': ('occult', 'Hard'), 'descifrar': ('occult', 'Hard'),
    'leo': ('occult', 'Hard'), 'leer': ('occult', 'Hard'),
    'interpreto': ('occult', 'Hard'), 'entiendo': ('occult', 'Hard'),
    # social
    'persuado': ('persuade', 'Normal'), 'persuadir': ('persuade', 'Normal'),
    'convenzo': ('persuade', 'Normal'), 'convencer': ('persuade', 'Normal'),
    'intimido': ('persuade', 'Normal'), 'intimidar': ('persuade', 'Normal'),
    'engaño': ('persuade', 'Hard'), 'engañar': ('persuade', 'Hard'),
}


# --- Anti-abuse limits ---------------------------------------------------
# The engine owns all mechanics; these clamp what any single turn can do, so a
# prompt-injection attempt ("I find 100000 ammo", "[HP_DAMAGE: 9999]") or a
# hallucinating model can't break the game's economy.
MAX_PLAYER_INPUT = 500   # characters; longer actions are truncated
MAX_HP_DAMAGE = 30       # ceiling on a single HP loss
MAX_SAN_DAMAGE = 30      # ceiling on a single SAN loss
AMMO_FIND_CAP = 6        # most rounds one discovery can grant
AMMO_MAX = 24            # hard ceiling on carried rounds
_TAG_LIKE = re.compile(r'\[[^\]]*\]')  # strip bracket directives from player text


# Failed-roll consequence categories. The ENGINE decides the mechanical bite
# (not the LLM), so failure always costs something and can't be retried away.
PHYSICAL_SKILLS = {
    "climb", "swim", "jump", "dodge", "brawl", "fight", "throw",
    "firearms", "firearms_revolver", "firearms_rifle", "firearms_shotgun",
}
MENTAL_SKILLS = {
    "occult", "investigate", "spot_hidden", "library", "library_use",
    "psychology", "science", "navigate", "listen", "archaeology", "anthropology",
}

# Attack intent (English + Spanish) — used to synthesize combat when the player
# clearly attacks a present threat but the DM didn't formally start a fight.
ATTACK_VERBS = {
    "attack", "fight", "hit", "punch", "kick", "shoot", "fire", "stab", "strike",
    "kill", "slash", "swing", "shoot at", "gun down", "engage", "combat",
    "charge at", "lunge at", "confront",
    "ataco", "atacar", "ataca", "disparo", "disparar", "dispara", "golpeo",
    "golpear", "golpea", "pelear", "peleo", "mato", "matar", "apuñalo",
    "apuñalar", "embisto", "embestir", "le pego", "disparale", "combate",
    "enfrento", "enfrentar", "me enfrento",
}

# Ambush: the DM narrates something physically seizing/attacking the PLAYER.
# Combat should start even though the player never declared an attack.
AMBUSH_CUES = {
    "grabs you", "grabs your", "grasps your", "grasps you", "seizes you",
    "lunges at you", "attacks you", "strikes at you", "charges at you",
    "wraps around you", "pounces on you", "drags you", "claws at you",
    "te agarra", "te ataca", "se abalanza sobre ti", "te embiste",
    "te arrastra", "te sujeta",
}

# Movement intent — location auto-detect only fires when the PLAYER tries to
# move. Matching location keywords against the DM's prose alone teleported the
# player whenever the DM merely mentioned a room ("the hidden chamber above").
MOVEMENT_VERBS = {
    "go", "enter", "climb", "descend", "head", "walk", "move", "step", "run to",
    "approach", "leave", "exit", "sneak", "crawl", "follow", "return",
    "entro", "entrar", "subo", "subir", "bajo", "bajar", "voy", "camino",
    "me dirijo", "avanzo", "salgo", "salir", "regreso", "vuelvo", "sigo",
}

# Item pickup intent. The DM is supposed to emit [ITEM_FOUND: key] (or call the
# pickup_item tool) when the player takes something, and in practice it does
# neither: measured over real turns, the local models emit no mechanic tags at
# all and return no tool calls. Rolls, combat, sanity and movement all survive
# that because the engine has keyword fallbacks for them — items were the one
# mechanic with no fallback, which is why the LAN playtest recorded "0 armas
# encontradas" and AMMO 6 that no one could ever spend.
#
# Gated on the PLAYER's words, never the DM's prose: the same mistake on
# [LOCATION:] teleported players whenever a room was merely mentioned.
TAKE_VERBS = {
    "agarro", "agarrar", "tomo", "tomar", "recojo", "recoger", "cojo", "coger",
    "saco", "sacar", "guardo", "guardar", "me llevo", "llevo", "empuño",
    "take", "takes", "grab", "grabs", "pick up", "picks up", "pocket",
    "collect", "retrieve", "i take", "i grab",
}

# Noun -> key in GenerativeGameEngine.ITEMS. Only registry items can be granted,
# so a player asking for a knife still gets nothing — that rejection is the
# containment working, not a gap.
ITEM_KEYWORDS = {
    "revolver": "revolver", "revólver": "revolver", "pistola": "revolver",
    "pistol": "revolver", "gun": "revolver", "firearm": "revolver",
    "arma": "revolver", ".38": "revolver",
    "linterna": "flashlight", "flashlight": "flashlight", "torch": "flashlight",
    "cuerda": "rope", "soga": "rope", "rope": "rope",
    "diario": "logbook", "bitácora": "logbook", "bitacora": "logbook",
    "logbook": "logbook", "registro": "logbook", "log": "logbook",
    "libreta": "notebook", "cuaderno": "notebook", "notebook": "notebook",
    "dinamita": "dynamite", "dynamite": "dynamite", "explosivo": "dynamite",
    "agua bendita": "holy_water", "holy water": "holy_water",
    "texto antiguo": "ancient_text", "ancient text": "ancient_text",
    "manuscrito": "ancient_text", "tome": "ancient_text",
}

# Deliberate recovery: resting/praying steadies the mind. Costs the turn (the
# doom clock keeps ticking), gated by a cooldown so it can't be spammed.
REST_KEYWORDS = {
    "rest", "take a breath", "catch my breath", "calm down", "calm myself",
    "meditate", "pray", "steady myself", "compose myself",
    "descanso", "descansar", "respiro", "me calmo", "calmarme", "medito",
    "meditar", "rezo", "rezar", "oro", "orar", "me recompongo",
}
REST_COOLDOWN_TURNS = 3
REST_RECOVERY = (1, 2)  # random range of SAN recovered per rest

# STRICT cues for a major horror reveal in the DM's OWN prose (a demon
# unleashed, an entity manifesting). Deliberately narrow — unlike
# SANITY_TRIGGERS (keyed off the player's words), matching the DM's prose too
# loosely would bleed SAN on mere atmosphere. Big reveals must cost sanity.
ESCALATION_CUES = {
    "unleashed", "has awakened", "awakens", "demon", "manifests before",
    "rises from the deep", "sea monster", "it has claimed", "will not rest",
    "demonio", "liberado", "ha despertado", "se manifiesta", "monstruo marino",
    "no descansará",
}

# Witnessing the unnatural costs Sanity. If the DM narrates horror but forgets
# the mechanic, the engine forces a Sanity check on these cues.
SANITY_TRIGGERS = {
    "monster", "monstrous", "monstrosity", "creature", "eldritch", "abomination",
    "horror", "horrifying", "tentacle", "writhing", "grotesque", "incomprehensible",
    "comprehend", "unnatural", "nightmare", "deep one", "corpse", "rotting",
    "blasphem", "non-euclidean", "impossible geometry", "thing beneath", "cyclopean",
}


__all__ = [
    "ROLL_KEYWORDS",
    "TAKE_VERBS",
    "ITEM_KEYWORDS",
    "MAX_PLAYER_INPUT",
    "MAX_HP_DAMAGE",
    "MAX_SAN_DAMAGE",
    "AMMO_FIND_CAP",
    "AMMO_MAX",
    "_TAG_LIKE",
    "PHYSICAL_SKILLS",
    "MENTAL_SKILLS",
    "ATTACK_VERBS",
    "AMBUSH_CUES",
    "MOVEMENT_VERBS",
    "REST_KEYWORDS",
    "REST_COOLDOWN_TURNS",
    "REST_RECOVERY",
    "ESCALATION_CUES",
    "SANITY_TRIGGERS",
]
