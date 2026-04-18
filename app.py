#!/usr/bin/env python3
"""
Cthulhu Lighthouse Game - Web Interface
Flask backend for the generative RPG
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from graphics_engine.ascii_scenes_hd import get_scene_hd, list_scenes_hd
from core.game_generative import GenerativeGameEngine, InvestigatorState

app = Flask(__name__)
CORS(app)

# Global game instance
game_engine = None
current_investigator = None


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
def start_game():
    """Start a new game"""
    global game_engine, current_investigator

    data = request.json
    investigator_name = data.get('name', 'Unknown Investigator')
    archetype = data.get('archetype', 'scholar')

    try:
        # Initialize investigator
        current_investigator = InvestigatorState(
            name=investigator_name,
            archetype=archetype,
            characteristics={
                'STR': 50,
                'CON': 50,
                'SIZ': 50,
                'DEX': 50,
                'APP': 50,
                'INT': 70 if archetype == 'scholar' else 60,
                'POW': 60,
                'EDU': 75 if archetype == 'scholar' else 65,
                'HP': 7,
                'SAN': 70,
                'Luck': 50
            }
        )

        # Initialize game engine
        game_engine = GenerativeGameEngine(use_memory=False)
        game_engine.create_game(current_investigator)

        return jsonify({
            "success": True,
            "message": f"Game started! Welcome, {investigator_name}",
            "investigator": {
                "name": current_investigator.name,
                "archetype": current_investigator.archetype,
                "HP": current_investigator.characteristics['HP'],
                "SAN": current_investigator.characteristics['SAN'],
                "Luck": current_investigator.characteristics['Luck']
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Get current game state"""
    if not game_engine or not current_investigator:
        return jsonify({"error": "Game not started"}), 400

    return jsonify({
        "location": game_engine.state.location,
        "turn": game_engine.state.turn,
        "investigator": {
            "name": current_investigator.name,
            "archetype": current_investigator.archetype,
            "HP": current_investigator.characteristics['HP'],
            "SAN": current_investigator.characteristics['SAN'],
            "Luck": current_investigator.characteristics['Luck']
        },
        "narrative": game_engine.state.narrative[-5:] if game_engine.state.narrative else []
    })


@app.route('/api/game/action', methods=['POST'])
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
def reset_game():
    """Reset game to start"""
    global game_engine, current_investigator
    game_engine = None
    current_investigator = None

    return jsonify({"success": True, "message": "Game reset"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
