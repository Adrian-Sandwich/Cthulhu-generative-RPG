"""HuggingFace Inference API client for image generation"""
import requests
import os
from io import BytesIO
from PIL import Image

HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

class ImageGenerationError(Exception):
    """Error during image generation"""
    pass

def generate_image(prompt: str, negative_prompt: str = "", max_retries: int = 3) -> bytes:
    """
    Generate image using HuggingFace Stable Diffusion XL API

    Args:
        prompt: Text description of the image
        negative_prompt: What to avoid in the image
        max_retries: Max API retry attempts

    Returns:
        PNG image bytes

    Raises:
        ImageGenerationError: If generation fails
    """
    if not HF_TOKEN:
        raise ImageGenerationError("HF_TOKEN environment variable not set")

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
    }

    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    # Retry logic for API rate limits
    for attempt in range(max_retries):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                return response.content  # PNG bytes
            elif response.status_code == 503:
                # Model loading, retry
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                    continue
                else:
                    raise ImageGenerationError(f"Model unavailable after {max_retries} retries")
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                raise ImageGenerationError(f"HF API error: {error_msg}")

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
                continue
            else:
                raise ImageGenerationError(f"Request failed: {e}")

    raise ImageGenerationError("Unknown error during image generation")

def generate_lovecraftian_scene(scene_description: str) -> bytes:
    """
    Generate a Lovecraftian horror scene image

    Args:
        scene_description: Description of the scene

    Returns:
        PNG image bytes
    """
    # Enhance prompt with Lovecraftian elements
    prompt = f"""
    Lovecraftian horror scene: {scene_description}
    Dark, atmospheric, cosmic horror, eldritch, creepy,
    high detail, realistic, cinematic lighting, fog, shadows
    """

    negative_prompt = "bright, colorful, cheerful, cartoon, anime, simple"

    return generate_image(prompt, negative_prompt)

def test_api():
    """Test API connectivity"""
    try:
        # Simple test generation
        image_bytes = generate_image("A dark lighthouse on a rocky coast at night, foggy, horror atmosphere")
        img = Image.open(BytesIO(image_bytes))
        print(f"✓ API working. Generated image: {img.size}")
        return True
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_api()
