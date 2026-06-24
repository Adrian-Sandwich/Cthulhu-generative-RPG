#!/usr/bin/env python3
"""
Cthulhu Lighthouse Game - Web Interface
Flask backend for the generative RPG
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import threading
from functools import wraps
from pathlib import Path
from core.game_generative import GenerativeGameEngine
from core.archetypes import get_archetype_sheets, create_investigator
from game.game_image_integration import generate_for_location

app = Flask(__name__)
# Frontend is served by this same app; CORS only needed for external
# origins, configurable via comma-separated CORS_ORIGINS env var.
_cors_origins = [o for o in os.environ.get('CORS_ORIGINS', '').split(',') if o]
if _cors_origins:
    CORS(app, origins=_cors_origins)

# Generated location images. SDXL scene generation is gated behind a
# flag (off by default) — the procedural art was more confusing than
# helpful, so the game runs text-only unless ENABLE_IMAGES=1.
GENERATED_IMAGES_DIR = Path(__file__).parent / 'game' / 'generated'
IMAGES_ENABLED = os.environ.get('ENABLE_IMAGES', '0') == '1'

@app.route('/images/<path:filename>')
def serve_generated_image(filename):
    """Serve generated location images"""
    return send_from_directory(GENERATED_IMAGES_DIR, filename)


# Global game instance. Flask serves requests from multiple threads;
# the lock serializes access so concurrent requests can't corrupt state.
game_engine = None
current_investigator = None
state_lock = threading.Lock()


def synchronized(f):
    """Serialize handler execution around the shared game state."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        with state_lock:
            return f(*args, **kwargs)
    return wrapper


# Image generation runs in a background thread: SDXL inference takes
# 30s+ and must not block request handlers (which hold state_lock).
_generating_locations = set()
_generating_lock = threading.Lock()


def request_image_generation(location_state):
    """Kick off background image generation for a location (idempotent)."""
    key = location_state.key
    with _generating_lock:
        if key in _generating_locations:
            return
        _generating_locations.add(key)

    def work():
        try:
            generate_for_location(location_state)
        except Exception as e:
            print(f"Warning: Could not generate image for {key}: {e}")
        finally:
            with _generating_lock:
                _generating_locations.discard(key)

    threading.Thread(target=work, daemon=True, name=f"imagegen-{key}").start()


@app.route('/')
def index():
    """Main game interface"""
    return render_template('index.html')


@app.route('/api/archetypes', methods=['GET'])
def get_archetypes():
    """Archetype stat blocks for the character sheet preview"""
    return jsonify({"archetypes": get_archetype_sheets()})


@app.route('/api/game/start', methods=['POST'])
@synchronized
def start_game():
    """Start a new game"""
    global game_engine, current_investigator

    data = request.json
    investigator_name = data.get('name', 'Unknown Investigator')
    occupation = data.get('archetype', 'scholar')  # Called 'occupation' in game engine

    try:
        current_investigator = create_investigator(investigator_name, occupation)

        # Initialize game engine
        game_engine = GenerativeGameEngine(use_memory=False)
        game_engine.create_game(current_investigator)

        # Opening narrative so the player knows the situation and that
        # they drive the story with free-text actions
        intro = game_engine.STORY_SEED.strip()

        return jsonify({
            "success": True,
            "message": f"Game started! Welcome, {investigator_name}",
            "intro": intro,
            "location": game_engine.state.location,
            "investigator": {
                "name": current_investigator.name,
                "archetype": current_investigator.occupation,
                "HP": current_investigator.characteristics['HP'],
                "SAN": current_investigator.characteristics['SAN'],
                "Luck": current_investigator.characteristics['Luck']
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/state', methods=['GET'])
@synchronized
def get_game_state():
    """Get current game state"""
    if not game_engine or not current_investigator:
        return jsonify({"error": "Game not started"}), 400

    # Get location state and request image generation if missing
    location_state = None
    if game_engine.location_state:
        location_state = game_engine.location_state.get_location(game_engine.state.location)
    image_url = None
    image_generating = False
    if IMAGES_ENABLED and location_state:
        if not location_state.generated_image_path:
            request_image_generation(location_state)
            image_generating = True
        else:
            image_path = Path(location_state.generated_image_path)
            image_url = f"/images/{image_path.name}"

    return jsonify({
        "location": game_engine.state.location,
        "turn": game_engine.state.turn,
        "image_url": image_url,
        "image_generating": image_generating,
        "investigator": {
            "name": current_investigator.name,
            "archetype": current_investigator.occupation,
            "HP": current_investigator.characteristics['HP'],
            "SAN": current_investigator.characteristics['SAN'],
            "Luck": current_investigator.characteristics['Luck'],
            "characteristics": current_investigator.characteristics,
            "skills": current_investigator.skills,
            "inventory": current_investigator.inventory
        },
        "narrative": game_engine.state.narrative[-5:] if game_engine.state.narrative else []
    })


# Roll waiting for the player to throw the die (skill, difficulty, target).
# Mutated only under state_lock via @synchronized handlers.
pending_roll = None


def _investigator_stats():
    return {
        "HP": current_investigator.characteristics['HP'],
        "SAN": current_investigator.characteristics['SAN'],
        "Luck": current_investigator.characteristics['Luck']
    }


@app.route('/api/game/action', methods=['POST'])
@synchronized
def process_action():
    """Process player action"""
    global pending_roll

    if not game_engine or not current_investigator:
        return jsonify({"error": "Game not started"}), 400

    if pending_roll:
        return jsonify({"error": "Resolve the pending roll first"}), 409

    data = request.json
    player_input = data.get('action', '')

    if not player_input.strip():
        return jsonify({"error": "Action cannot be empty"}), 400

    try:
        # Process the action
        result = game_engine.process_player_action(player_input)

        # Apply immediate consequences the DM declared inline
        for damage in result.get("hp_damage", []):
            game_engine.apply_hp_damage(int(damage))
        for damage in result.get("sanity_checks", []):
            game_engine.apply_sanity_check(int(damage))

        # If the DM requested a roll, hand the die to the player
        # instead of resolving it silently
        rolls = result.get("rolls_requested", [])
        if rolls:
            skill, difficulty = rolls[0]
            pending_roll = game_engine.prepare_skill_check(skill, difficulty)

        return jsonify({
            "success": True,
            "turn": game_engine.state.turn,
            "location": game_engine.state.location,
            "narrative": result.get("narrative", ""),
            "pending_roll": pending_roll,
            "state": _investigator_stats()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/roll', methods=['POST'])
@synchronized
def execute_roll():
    """Player throws the die for the pending skill check"""
    global pending_roll

    if not game_engine or not current_investigator:
        return jsonify({"error": "Game not started"}), 400

    if not pending_roll:
        return jsonify({"error": "No pending roll"}), 400

    try:
        roll = pending_roll
        pending_roll = None

        # Server rolls the actual die (the client animation is theater)
        result = game_engine.execute_skill_check(roll["skill"], roll["difficulty"])

        # DM narrates the outcome immediately
        consequence = game_engine.resolve_roll_consequences()
        narrative = ""
        if isinstance(consequence, dict):
            narrative = consequence.get("narrative", "")

        return jsonify({
            "success": True,
            "skill": roll["skill"],
            "difficulty": roll["difficulty"],
            "roll": result["roll"],
            "target": result["target"],
            "roll_success": result["success"],
            "message": result["message"],
            "narrative": narrative,
            "turn": game_engine.state.turn,
            "location": game_engine.state.location,
            "state": _investigator_stats()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/reset', methods=['POST'])
@synchronized
def reset_game():
    """Reset game to start"""
    global game_engine, current_investigator, pending_roll
    game_engine = None
    current_investigator = None
    pending_roll = None

    return jsonify({"success": True, "message": "Game reset"})


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=debug, port=port)
