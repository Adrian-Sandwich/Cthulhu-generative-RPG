"""Generate ASCII art directly using Ollama LLM"""
import requests
import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

class AsciiGenerationError(Exception):
    """Error during ASCII generation"""
    pass

def generate_ascii_art(prompt: str, width: int = 80, style: str = "lovecraftian") -> str:
    """
    Generate ASCII art using Ollama LLM

    Args:
        prompt: Description of the scene to generate ASCII art for
        width: Width of ASCII art in characters
        style: Style (lovecraftian, cosmic, nature, urban, etc.)

    Returns:
        ASCII art as string
    """
    if not prompt.strip():
        raise AsciiGenerationError("Prompt cannot be empty")

    # Build the LLM prompt
    system_prompt = f"""You are an expert ASCII artist. Generate high-quality ASCII art based on descriptions.

Rules:
- Width: exactly {width} characters per line
- Use a rich palette of ASCII characters: @ % # * + = - : . space
- Create detailed, artistic representations
- NO explanations, NO markdown, just the ASCII art
- Style: {style}
- Make it atmospheric and detailed"""

    user_prompt = f"Generate ASCII art for: {prompt}"

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "temperature": 0.7,
            },
            timeout=240,
        )

        if response.status_code != 200:
            raise AsciiGenerationError(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        result = response.json()
        ascii_art = result.get("response", "").strip()

        if not ascii_art:
            raise AsciiGenerationError("Empty response from Ollama")

        return ascii_art

    except requests.ConnectionError as e:
        raise AsciiGenerationError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is running."
        )
    except requests.RequestException as e:
        raise AsciiGenerationError(f"Request failed: {e}")
    except Exception as e:
        raise AsciiGenerationError(f"Failed to generate ASCII art: {e}")

def test_ollama():
    """Test Ollama connectivity"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✓ Ollama online. Available models: {[m['name'] for m in models]}")
            return True
        else:
            print(f"✗ Ollama returned error: {response.status_code}")
            return False
    except requests.ConnectionError:
        print(
            f"✗ Cannot connect to Ollama at {OLLAMA_BASE_URL}\n"
            "Make sure Ollama is running: ollama serve"
        )
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_ollama()

    # Test generation
    try:
        ascii_art = generate_ascii_art(
            "A dark lighthouse on a rocky coast with fog",
            width=60,
            style="lovecraftian"
        )
        print("\nGenerated ASCII art:")
        print(ascii_art)
    except AsciiGenerationError as e:
        print(f"Error: {e}")
