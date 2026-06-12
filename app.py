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
from legacy.graphics_engine_v1.ascii_scenes_hd import get_scene_hd, list_scenes_hd
from core.game_generative import GenerativeGameEngine, InvestigatorState
from game.game_image_integration import generate_for_location

app = Flask(__name__)
# Frontend is served by this same app; CORS only needed for external
# origins, configurable via comma-separated CORS_ORIGINS env var.
_cors_origins = [o for o in os.environ.get('CORS_ORIGINS', '').split(',') if o]
if _cors_origins:
    CORS(app, origins=_cors_origins)

# Generated location images
GENERATED_IMAGES_DIR = Path(__file__).parent / 'game' / 'generated'


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


@app.route('/api/scenes', methods=['GET'])
def get_scenes():
    """Get list of available scenes"""
    scenes = list_scenes_hd()
    return jsonify({"scenes": list(scenes.keys())})


@app.route('/api/scene/<scene_key>', methods=['GET'])
def get_scene(scene_key):
    """Get a specific scene by key"""
    scene_content = get_scene_hd(scene_key)
    if scene_content == "Scene not found.":
        return jsonify({"error": "Scene not found"}), 404

    return jsonify({
        "key": scene_key,
        "content": scene_content
    })


@app.route('/api/game/start', methods=['POST'])
@synchronized
def start_game():
    """Start a new game"""
    global game_engine, current_investigator

    data = request.json
    investigator_name = data.get('name', 'Unknown Investigator')
    occupation = data.get('archetype', 'scholar')  # Called 'occupation' in game engine

    try:
        # Initialize investigator
        current_investigator = InvestigatorState(
            name=investigator_name,
            occupation=occupation,
            characteristics={
                'STR': 50,
                'CON': 50,
                'SIZ': 50,
                'DEX': 50,
                'APP': 50,
                'INT': 70 if occupation == 'scholar' else 60,
                'POW': 60,
                'EDU': 75 if occupation == 'scholar' else 65,
                'HP': 7,
                'SAN': 70,
                'Luck': 50
            },
            skills={},
            inventory=[],
            visited_locations=[],
            sanity_breaks=[]
        )

        # Initialize game engine
        game_engine = GenerativeGameEngine(use_memory=False)
        game_engine.create_game(current_investigator)

        return jsonify({
            "success": True,
            "message": f"Game started! Welcome, {investigator_name}",
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
    if location_state and not location_state.generated_image_path:
        request_image_generation(location_state)
        image_generating = True

    # Convert image path to URL
    if location_state and location_state.generated_image_path:
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
            "Luck": current_investigator.characteristics['Luck']
        },
        "narrative": game_engine.state.narrative[-5:] if game_engine.state.narrative else []
    })


@app.route('/api/game/action', methods=['POST'])
@synchronized
def process_action():
    """Process player action"""
    if not game_engine or not current_investigator:
        return jsonify({"error": "Game not started"}), 400

    data = request.json
    player_input = data.get('action', '')

    if not player_input.strip():
        return jsonify({"error": "Action cannot be empty"}), 400

    try:
        # Process the action
        result = game_engine.process_player_action(player_input)

        return jsonify({
            "success": True,
            "turn": game_engine.state.turn,
            "location": game_engine.state.location,
            "narrative": result.get("narrative", ""),
            "state": {
                "HP": current_investigator.characteristics['HP'],
                "SAN": current_investigator.characteristics['SAN'],
                "Luck": current_investigator.characteristics['Luck']
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/reset', methods=['POST'])
@synchronized
def reset_game():
    """Reset game to start"""
    global game_engine, current_investigator
    game_engine = None
    current_investigator = None

    return jsonify({"success": True, "message": "Game reset"})


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=debug, port=port)
