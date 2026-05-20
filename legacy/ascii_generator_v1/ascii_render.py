"""Convert images (from bytes) to ASCII art"""
from io import BytesIO
from PIL import Image
import numpy as np
from typing import Optional

# ASCII character sets from dark to light
ASCII_CHARSETS = {
    "dark": "@%#*+=-:. ",
    "detailed": "█▓▒░ ",
    "blocks": "██░░  ",
    "standard": "@%#*+=-:. ",
    "artistic": "M8&WN%B@0Q#$O*+=;:,.^'\"- ",
}

class AsciiRenderError(Exception):
    """Error during ASCII rendering"""
    pass

def image_bytes_to_ascii(
    image_bytes: bytes,
    width: int = 80,
    charset: str = "dark",
    aspect_ratio_correction: float = 2.0,
) -> str:
    """
    Convert image bytes to ASCII art

    Args:
        image_bytes: PNG/JPG image bytes
        width: ASCII art width in characters
        charset: Character set to use ("dark", "detailed", "blocks", "standard", "artistic")
        aspect_ratio_correction: Aspect ratio correction factor (default 2.0 for terminal)

    Returns:
        ASCII art as string
    """
    try:
        # Load image from bytes
        img = Image.open(BytesIO(image_bytes))

        # Resize maintaining aspect ratio
        ratio = img.height / img.width
        height = int(width * ratio / aspect_ratio_correction)
        img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Convert to grayscale
        img = img.convert("L")

        # Get charset
        chars = ASCII_CHARSETS.get(charset, ASCII_CHARSETS["dark"])
        num_chars = len(chars)

        # Convert pixels to ASCII
        pixels = np.array(img)
        ascii_str = ""

        for row in pixels:
            for pixel in row:
                # Map pixel value (0-255) to character index
                char_index = int((pixel / 255) * (num_chars - 1))
                ascii_str += chars[char_index]
            ascii_str += "\n"

        return ascii_str

    except Exception as e:
        raise AsciiRenderError(f"Failed to convert image to ASCII: {e}")

def image_path_to_ascii(
    image_path: str,
    width: int = 80,
    charset: str = "dark",
) -> str:
    """Convert image file to ASCII art"""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return image_bytes_to_ascii(image_bytes, width, charset)

def image_to_ascii_with_metadata(
    image_bytes: bytes,
    width: int = 80,
    charset: str = "dark",
) -> dict:
    """
    Convert image to ASCII art and return metadata

    Returns:
        {
            "ascii_art": "...",
            "width": int,
            "height": int,
            "charset": str,
        }
    """
    ascii_art = image_bytes_to_ascii(image_bytes, width, charset)
    lines = ascii_art.strip().split("\n")
    height = len(lines)

    return {
        "ascii_art": ascii_art,
        "width": width,
        "height": height,
        "charset": charset,
        "lines": lines,
    }

def enhance_ascii_art(ascii_art: str, enhance: bool = False) -> str:
    """
    Optionally enhance ASCII art with borders/styling

    Args:
        ascii_art: ASCII art string
        enhance: Whether to add borders
    """
    if not enhance:
        return ascii_art

    lines = ascii_art.strip().split("\n")
    width = max(len(line) for line in lines) if lines else 0

    # Add borders
    border = "╔" + "═" * width + "╗"
    bottom = "╚" + "═" * width + "╝"

    enhanced = [border]
    for line in lines:
        enhanced.append("║" + line.ljust(width) + "║")
    enhanced.append(bottom)

    return "\n".join(enhanced)

if __name__ == "__main__":
    # Test with sample
    from graphics_engine.data.art_samples import list_samples

    samples = list_samples()
    if samples:
        with open(f"graphics_engine/data/art_samples/{samples[0]}", "rb") as f:
            image_bytes = f.read()

        ascii_art = image_bytes_to_ascii(image_bytes, width=60)
        print(ascii_art)
