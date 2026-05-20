"""Convert image samples to ASCII art for game display"""
import os
from pathlib import Path
from PIL import Image
import numpy as np

SAMPLES_DIR = Path(__file__).parent / "data" / "art_samples"
ASCII_CHARS = "@%#*+=-:. "  # From dark to light

def resize_image(img, width=80, aspect_ratio_correction=2):
    """Resize image maintaining aspect ratio"""
    ratio = img.height / img.width
    height = int(width * ratio / aspect_ratio_correction)
    return img.resize((width, height))

def grayscale_image(img):
    """Convert image to grayscale"""
    return img.convert("L")

def pixels_to_ascii(img):
    """Convert pixel values to ASCII characters"""
    pixels = np.array(img)
    ascii_str = ""
    for row in pixels:
        for pixel in row:
            ascii_str += ASCII_CHARS[int(pixel / 256 * len(ASCII_CHARS) - 1)]
        ascii_str += "\n"
    return ascii_str

def image_to_ascii(image_path, width=80):
    """Convert an image file to ASCII art"""
    try:
        img = Image.open(image_path)
        img = resize_image(img, width)
        img = grayscale_image(img)
        return pixels_to_ascii(img)
    except Exception as e:
        return f"Error processing {Path(image_path).name}: {e}"

def convert_sample(index=0, width=80, save=True):
    """Convert a sample image to ASCII art"""
    if not SAMPLES_DIR.exists():
        return None

    files = sorted([f for f in SAMPLES_DIR.iterdir() if f.is_file()])
    if not files:
        return None

    image_file = files[index % len(files)]
    ascii_art = image_to_ascii(image_file, width)

    if save:
        output_file = SAMPLES_DIR / f"{image_file.stem}_ascii.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(ascii_art)
        return {"file": image_file.name, "ascii": ascii_art, "output": str(output_file)}

    return {"file": image_file.name, "ascii": ascii_art}

def batch_convert(start=0, count=5, width=80):
    """Convert multiple samples to ASCII art"""
    results = []
    for i in range(count):
        result = convert_sample(start + i, width, save=True)
        if result:
            results.append(result)
    return results

def list_samples():
    """List all available samples"""
    if not SAMPLES_DIR.exists():
        return []
    return sorted([f.name for f in SAMPLES_DIR.iterdir() if f.is_file()])

def get_sample_ascii(filename_or_index, width=80):
    """Get ASCII art for a specific sample"""
    files = list_samples()
    if not files:
        return None

    if isinstance(filename_or_index, int):
        filename = files[filename_or_index % len(files)]
    else:
        filename = filename_or_index

    image_path = SAMPLES_DIR / filename
    if not image_path.exists():
        return None

    return image_to_ascii(image_path, width)

if __name__ == "__main__":
    print("ASCII Art Sample Converter")
    print("=" * 60)

    # Demo: convert first 3 samples
    results = batch_convert(start=0, count=3, width=60)

    for result in results:
        print(f"\nSource: {result['file']}")
        print(result['ascii'][:500] + "..." if len(result['ascii']) > 500 else result['ascii'])
        print(f"(Saved to: {result['output']})")
