"""ASCII Art Generator Server - Flask backend
Generates ASCII art from text descriptions using HuggingFace Stable Diffusion + image conversion
"""
import os
import base64
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

from ascii_gen import generate_ascii_art, AsciiGenerationError, test_ollama

app = Flask(__name__)
CORS(app)

# Configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
MAX_ASCII_WIDTH = 2000
DEFAULT_ASCII_WIDTH = 160

@app.route("/", methods=["GET"])
def index():
    """Serve the React app"""
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "ascii-art-generator"}), 200

@app.route("/api/generate", methods=["POST"])
def generate_ascii():
    """
    Generate ASCII art from text prompt using Ollama LLM

    Request JSON:
    {
        "prompt": "lighthouse in fog",
        "width": 80,
        "style": "lovecraftian"
    }

    Response:
    {
        "success": true,
        "ascii_art": "...",
        "metadata": {
            "width": 80,
            "style": "lovecraftian"
        }
    }
    """
    try:
        data = request.get_json()

        if not data or "prompt" not in data:
            return jsonify({"success": False, "error": "Missing 'prompt' field"}), 400

        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({"success": False, "error": "Prompt cannot be empty"}), 400

        width = int(data.get("width", DEFAULT_ASCII_WIDTH))
        if width < 40 or width > MAX_ASCII_WIDTH:
            width = DEFAULT_ASCII_WIDTH

        style = data.get("style", "lovecraftian")

        # Generate ASCII art using Ollama
        ascii_art = generate_ascii_art(prompt, width=width, style=style)

        return jsonify({
            "success": True,
            "ascii_art": ascii_art,
            "metadata": {
                "width": width,
                "style": style,
                "prompt": prompt,
            }
        }), 200

    except AsciiGenerationError as e:
        return jsonify({"success": False, "error": f"ASCII generation failed: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

@app.route("/api/styles", methods=["GET"])
def get_styles():
    """Get available generation styles"""
    return jsonify({
        "styles": [
            "lovecraftian",
            "cosmic-horror",
            "nature",
            "urban",
            "fantasy",
            "dark-fantasy"
        ]
    }), 200

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = FLASK_PORT
    debug = os.getenv("DEBUG", "True").lower() == "true"
    print(f"🎨 ASCII Art Generator Server")
    print(f"📍 Port: {port}")
    print(f"🔗 http://localhost:{port}")
    print(f"🔄 Debug: {debug}")
    print(f"━" * 50)

    app.run(debug=debug, port=port, host="0.0.0.0")
