#!/usr/bin/env python3
"""
VQGAN+CLIP Image Refinement
Refine procedural images using CLIP embeddings and coherent styling
"""

import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from typing import List, Tuple, Dict, Optional
import open_clip


class VQGANClipRefiner:
    """Refine and enhance images using CLIP embeddings"""

    def __init__(self, model_name: str = "ViT-B-32", pretrained: str = "openai"):
        """
        Initialize CLIP model for image analysis and refinement.

        Args:
            model_name: CLIP model architecture
            pretrained: Pretrained weights source
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎨 VQGAN+CLIP Refiner initialized (device: {self.device})")

        # Load CLIP model
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model.eval()

    # Location-specific prompts and styles
    LOCATION_CONFIGS = {
        "Lighthouse Exterior": {
            "primary": "a mysterious lighthouse on a rocky shore",
            "variations": [
                "foggy lighthouse at dawn with mysterious atmosphere",
                "lighthouse during a violent storm with dramatic sky",
                "clear night lighthouse with beacon light casting rays",
                "ancient lighthouse emerging from mist",
            ],
            "style": "lovecraftian horror, dark atmospheric, eerie",
            "contrast": 1.15,
            "saturation": 0.95,
        },
        "Lighthouse Interior": {
            "primary": "ancient spiral staircase inside dark lighthouse",
            "variations": [
                "spiral stairs with mysterious symbols glowing on walls",
                "torch-lit circular chamber with ancient architecture",
                "steep spiral stairs descending into darkness",
                "keeper's quarters with maritime artifacts",
            ],
            "style": "lovecraftian, ancient mystery, shadow and light",
            "contrast": 1.2,
            "saturation": 0.9,
        },
        "Forest": {
            "primary": "deep dark forest with ancient twisted trees",
            "variations": [
                "moonlit forest clearing with ancient trees",
                "dense forest with towering gnarled trees",
                "overgrown forest path with twisted branches",
                "deep woods with fog and mysterious creatures",
            ],
            "style": "lovecraftian nature, dark woods, mysterious atmosphere",
            "contrast": 1.1,
            "saturation": 0.85,
        },
        "Crypt": {
            "primary": "underground stone crypt with ancient coffins",
            "variations": [
                "stone chamber with sealed coffins and ancient markings",
                "decorated crypt with ornate coffins and dust",
                "deep crypt passage with shadows and mystery",
                "burial chamber with stone grid and bones",
            ],
            "style": "lovecraftian death, ancient burial, stone and shadow",
            "contrast": 1.2,
            "saturation": 0.8,
        },
        "Sea": {
            "primary": "stormy sea with mysterious dark waters",
            "variations": [
                "violent waves during storm with dark clouds",
                "calm waters at dusk with eerie reflections",
                "shipwreck in stormy waters with fog",
                "deep ocean with ancient maritime mystery",
            ],
            "style": "lovecraftian ocean, water horror, drowning atmosphere",
            "contrast": 1.15,
            "saturation": 0.9,
        },
        "Beach": {
            "primary": "isolated sandy beach with dark atmosphere",
            "variations": [
                "desolate beach at twilight with mysterious fog",
                "ancient shore with strange rocks and ruins",
                "empty beach with eerie feeling",
                "coastal wasteland with dark sky",
            ],
            "style": "lovecraftian coast, abandonment, eerie emptiness",
            "contrast": 1.1,
            "saturation": 0.85,
        },
        "Cave": {
            "primary": "underground cave with stalactites and darkness",
            "variations": [
                "deep cave with mineral formations and underground water",
                "stalactite chamber with ancient formations",
                "cave passage with echoing darkness",
                "underground river with cave formations",
            ],
            "style": "lovecraftian underground, ancient stone, deep mystery",
            "contrast": 1.15,
            "saturation": 0.8,
        },
        "Village": {
            "primary": "abandoned village with empty houses",
            "variations": [
                "deserted village at dusk with eerie light",
                "abandoned town with decaying buildings",
                "desolate streets with mysterious architecture",
                "empty village with ominous feeling",
            ],
            "style": "lovecraftian abandonment, decay, eerie emptiness",
            "contrast": 1.1,
            "saturation": 0.9,
        },
    }

    def get_config(self, location: str) -> Dict:
        """Get refinement config for a location"""
        location_key = next(
            (k for k in self.LOCATION_CONFIGS.keys() if k.lower() in location.lower()),
            "Lighthouse Exterior",
        )
        return self.LOCATION_CONFIGS.get(location_key, self.LOCATION_CONFIGS["Lighthouse Exterior"])

    def analyze_image(self, img: Image.Image, location: str) -> Dict:
        """
        Analyze image using CLIP to get semantic understanding.

        Args:
            img: PIL Image to analyze
            location: Location name for context

        Returns:
            Analysis results with embeddings and scores
        """
        config = self.get_config(location)

        # Preprocess image
        img_processed = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # Get image embedding
            image_features = self.model.encode_image(img_processed)
            image_features = F.normalize(image_features, dim=-1)

            # Score against primary prompt
            text_primary = self.tokenizer([config["primary"]]).to(self.device)
            text_features_primary = self.model.encode_text(text_primary)
            text_features_primary = F.normalize(text_features_primary, dim=-1)

            primary_score = (image_features @ text_features_primary.T).item()

            # Score against style
            style_prompt = f"{config['style']}"
            text_style = self.tokenizer([style_prompt]).to(self.device)
            text_features_style = self.model.encode_text(text_style)
            text_features_style = F.normalize(text_features_style, dim=-1)

            style_score = (image_features @ text_features_style.T).item()

        return {
            "location": location,
            "primary_score": primary_score,
            "style_score": style_score,
            "config": config,
        }

    def refine_colors(self, img: Image.Image, config: Dict) -> Image.Image:
        """
        Refine image colors using style config.

        Args:
            img: PIL Image to refine
            config: Refinement configuration

        Returns:
            Refined PIL Image
        """
        # Adjust contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(config["contrast"])

        # Adjust saturation for mood
        img = img.convert("HSV")
        h, s, v = img.split()

        saturation_factor = config["saturation"]
        s = ImageEnhance.Brightness(s).enhance(saturation_factor)

        img = Image.merge("HSV", (h, s, v)).convert("RGB")

        # Apply subtle shadow enhancement
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.95)

        return img

    def apply_atmospheric_grading(self, img: Image.Image, location: str) -> Image.Image:
        """
        Apply location-specific color grading.

        Args:
            img: PIL Image
            location: Location name

        Returns:
            Color-graded image
        """
        img_array = np.array(img, dtype=np.float32)

        location_lower = location.lower()

        # Apply location-specific color shifts
        if "lighthouse" in location_lower:
            if "interior" in location_lower:
                # Interior: Warm torch light
                img_array[:, :, 0] *= 1.1  # More red
                img_array[:, :, 1] *= 1.05  # Slight green
                img_array[:, :, 2] *= 0.95  # Less blue
            else:
                # Exterior: Cool coastal fog
                img_array[:, :, 0] *= 0.95  # Less red
                img_array[:, :, 1] *= 1.0   # Neutral green
                img_array[:, :, 2] *= 1.1   # More blue

        elif "forest" in location_lower:
            # Forest: Green and shadow
            img_array[:, :, 0] *= 0.9   # Less red
            img_array[:, :, 1] *= 1.05  # More green
            img_array[:, :, 2] *= 0.9   # Less blue

        elif "sea" in location_lower or "beach" in location_lower:
            # Water: Cool blues
            img_array[:, :, 0] *= 0.9   # Less red
            img_array[:, :, 1] *= 1.0   # Neutral green
            img_array[:, :, 2] *= 1.15  # More blue

        elif "crypt" in location_lower or "cave" in location_lower:
            # Underground: Cool stone
            img_array[:, :, 0] *= 1.0   # Neutral red
            img_array[:, :, 1] *= 1.0   # Neutral green
            img_array[:, :, 2] *= 1.05  # Slight blue (stone)

        elif "village" in location_lower:
            # Village: Twilight warmth
            img_array[:, :, 0] *= 1.08  # More red (warm)
            img_array[:, :, 1] *= 1.02  # Slight green
            img_array[:, :, 2] *= 0.95  # Less blue

        # Clamp values
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)

        return Image.fromarray(img_array)

    def enhance_details(self, img: Image.Image, amount: float = 1.5) -> Image.Image:
        """
        Enhance fine details using sharpening.

        Args:
            img: PIL Image
            amount: Sharpening amount

        Returns:
            Sharpened image
        """
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(amount)

    def refine(
        self, img: Image.Image, location: str, apply_all: bool = True
    ) -> Image.Image:
        """
        Refine image using CLIP-guided adjustments.

        Args:
            img: PIL Image to refine
            location: Location name
            apply_all: Apply all refinements

        Returns:
            Refined image
        """
        config = self.get_config(location)

        # Analyze original
        analysis = self.analyze_image(img, location)

        # Apply refinements
        refined = img.copy()

        if apply_all:
            # Color refinement
            refined = self.refine_colors(refined, config)

            # Atmospheric color grading
            refined = self.apply_atmospheric_grading(refined, location)

            # Enhance details
            refined = self.enhance_details(refined, amount=1.3)

        return refined

    def get_description(self, img: Image.Image, location: str) -> str:
        """
        Generate a description of the image using CLIP.

        Args:
            img: PIL Image
            location: Location name

        Returns:
            Description string
        """
        config = self.get_config(location)

        # Preprocess image
        img_processed = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(img_processed)
            image_features = F.normalize(image_features, dim=-1)

            # Score against all variations
            descriptions = [
                config["primary"],
            ] + config["variations"]

            text_tokens = self.tokenizer(descriptions).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            text_features = F.normalize(text_features, dim=-1)

            scores = (image_features @ text_features.T).squeeze()

        # Get best matching description
        best_idx = scores.argmax().item()
        return descriptions[best_idx]
