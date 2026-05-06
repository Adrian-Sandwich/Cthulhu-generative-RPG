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

from image_gen import generate_image, generate_lovecraftian_scene, ImageGenerationError
from ascii_render import image_bytes_to_ascii, image_to_ascii_with_metadata, enhance_ascii_art

app = Flask(__name__)
CORS(app)

# Configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
MAX_ASCII_WIDTH = 120
DEFAULT_ASCII_WIDTH = 80

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
    Generate ASCII art from text prompt

    Request JSON:
    {
        "prompt": "lighthouse in fog",
        "width": 80,
        "charset": "dark",
        "style": "lovecraftian",
        "enhance": false
    }

    Response:
    {
        "success": true,
        "ascii_art": "...",
        "image_base64": "...",
        "metadata": {...}
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
        if width < 20 or width > MAX_ASCII_WIDTH:
            width = DEFAULT_ASCII_WIDTH

        charset = data.get("charset", "dark")
        style = data.get("style", "standard")
        enhance = data.get("enhance", False)

        # Generate image based on style
        if style == "lovecraftian":
            image_bytes = generate_lovecraftian_scene(prompt)
        else:
            image_bytes = generate_image(prompt)

        # Convert to ASCII
        metadata = image_to_ascii_with_metadata(image_bytes, width=width, charset=charset)
        ascii_art = metadata["ascii_art"]

        # Optional enhancement
        if enhance:
            ascii_art = enhance_ascii_art(ascii_art, enhance=True)

        # Encode image to base64 for display
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        return jsonify({
            "success": True,
            "ascii_art": ascii_art,
            "image_base64": f"data:image/png;base64,{image_b64}",
            "metadata": {
                "width": metadata["width"],
                "height": metadata["height"],
                "charset": charset,
                "style": style,
            }
        }), 200

    except ImageGenerationError as e:
        return jsonify({"success": False, "error": f"Image generation failed: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

@app.route("/api/charsets", methods=["GET"])
def get_charsets():
    """Get available character sets"""
    from ascii_render import ASCII_CHARSETS
    return jsonify({
        "charsets": list(ASCII_CHARSETS.keys()),
        "samples": {k: v for k, v in ASCII_CHARSETS.items()}
    }), 200

@app.route("/api/styles", methods=["GET"])
def get_styles():
    """Get available generation styles"""
    return jsonify({
        "styles": ["lovecraftian", "standard"]
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
