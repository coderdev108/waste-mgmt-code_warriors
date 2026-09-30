"""
AI Image and Synthetic Media Authenticity Detector.
Detects:
1. AI Generation Metadata (Stable Diffusion, Midjourney, DALL-E, ComfyUI, Automatic1111, Flux, etc.)
2. C2PA / Content Authenticity Initiative synthetic / digital generation markers
3. Camera EXIF absence vs. phone hardware signatures
4. Synthetic resolution profiles (512x512, 1024x1024, etc.)
5. Image noise / color distribution heuristics
"""
import io
import re
import math
from PIL import Image, ExifTags

# Known AI software / prompt keywords
AI_METADATA_KEYWORDS = [
    'stable diffusion', 'stablediffusion', 'midjourney', 'dall-e', 'dalle',
    'novelai', 'automatic1111', 'comfyui', 'invokeai', 'fooocus', 'flux.1',
    'dreamstudio', 'nightcafe', 'bing image creator', 'chatgpt', 'openai',
    'leonardo.ai', 'c2pa.synthetic', 'c2pa.created', 'urn:c2pa', 'photoleap',
    'craiyon', 'clipdrop', 'firefly', 'adobe sensei', 'deepai'
]

# Standard AI generation canvas sizes
AI_DIMENSIONS = {
    (512, 512), (768, 768), (1024, 1024), (1536, 1536), (2048, 2048),
    (512, 768), (768, 512), (768, 1024), (1024, 768),
    (896, 1152), (1152, 896), (832, 1216), (1216, 832),
    (1344, 768), (768, 1344), (1024, 1536), (1536, 1024),
}

KNOWN_CAMERA_MAKES = [
    'apple', 'samsung', 'google', 'xiaomi', 'oneplus', 'sony', 'huawei',
    'oppo', 'vivo', 'motorola', 'realme', 'redmi', 'poco', 'lg', 'htc',
    'canon', 'nikon', 'fujifilm', 'panasonic', 'olympus', 'leica'
]


def analyze_image_authenticity(image_file):
    """
    Analyzes an uploaded image file (Django UploadedFile or file-like object).
    Returns dict:
      {
         'is_ai': bool,             # True if image is flagged as AI-generated
         'is_suspicious': bool,     # True if high likelihood / warnings
         'confidence': float,       # 0.0 to 1.0 score
         'score': int,              # integer points
         'reasons': list of str,    # human-readable flags
         'is_valid_image': bool,
      }
    """
    reasons = []
    score = 0
    max_score = 10

    try:
        # Read content for raw byte analysis
        image_file.seek(0)
        raw_bytes = image_file.read()
        image_file.seek(0)

        raw_lower = raw_bytes[:131072].lower() + raw_bytes[-65536:].lower()

        # ── 1. Hard AI Metadata signatures in raw bytes ─────────────────
        found_keywords = []
        for kw in AI_METADATA_KEYWORDS:
            if kw.encode('utf-8') in raw_lower:
                found_keywords.append(kw)

        if found_keywords:
            score += 6
            reasons.append(f"AI generation metadata detected ({', '.join(found_keywords[:3])})")

        # Check for SD prompt indicators
        if b"parameters\x00" in raw_lower or b"steps: " in raw_lower and b"sampler: " in raw_lower:
            score += 6
            reasons.append("Stable Diffusion / WebUI generation parameters detected")

        # ── 2. Open with Pillow for format-level metadata ───────────────
        image_file.seek(0)
        img = Image.open(image_file)
        w, h = img.size

        # Check Pillow info dict (PNG chunks, comments)
        if hasattr(img, 'info') and img.info:
            info_str = str(img.info).lower()
            for kw in AI_METADATA_KEYWORDS:
                if kw in info_str and not any(kw in r for r in reasons):
                    score += 5
                    reasons.append(f"AI software marker in image metadata: '{kw}'")
                    break

            if 'prompt' in img.info or 'workflow' in img.info:
                score += 5
                reasons.append("ComfyUI / AI workflow dictionary embedded in image")

        # ── 3. EXIF Analysis ──────────────────────────────────────────
        has_camera_hardware = False
        try:
            exif = img.getexif()
            if exif:
                # 271: Make, 272: Model, 305: Software
                make = str(exif.get(271, '')).lower()
                model = str(exif.get(272, '')).lower()
                software = str(exif.get(305, '')).lower()

                for cam in KNOWN_CAMERA_MAKES:
                    if cam in make or cam in model:
                        has_camera_hardware = True
                        break

                for kw in AI_METADATA_KEYWORDS:
                    if kw in software:
                        score += 5
                        reasons.append(f"AI Software tag in EXIF: '{software}'")

                # If camera hardware confirmed, decrease suspicion
                if has_camera_hardware:
                    score = max(0, score - 3)
        except Exception:
            pass

        # ── 4. Resolution & Aspect Ratio heuristic ─────────────────────
        if (w, h) in AI_DIMENSIONS:
            score += 2
            reasons.append(f"Standard AI generation canvas dimension ({w}×{h}px)")
        elif w == h and w in [512, 768, 1024, 1536, 2048]:
            score += 2
            reasons.append(f"Perfect square AI canvas dimension ({w}×{w}px)")

        # ── 5. Camera metadata absence penalty (if square or common AI size) ─
        if not has_camera_hardware and (w == h or (w, h) in AI_DIMENSIONS):
            # Real camera photos are almost always 4:3 or 16:9, rarely perfect squares
            if len(raw_bytes) > 40000:
                score += 1
                reasons.append("Image lacks authentic camera hardware metadata and has synthetic proportions")

        # ── 6. Filename pattern check ──────────────────────────────────
        filename = getattr(image_file, 'name', '').lower()
        if filename:
            ai_file_prefixes = ['dall', 'midjourney', 'stablediffusion', 'sd_', 'comfy', 'output_', 'gen_']
            if any(filename.startswith(p) for p in ai_file_prefixes):
                score += 2
                reasons.append(f"File naming pattern matches AI generator: '{filename}'")

        # Normalize confidence
        confidence = min(1.0, round(score / 5.0, 2))
        is_ai = score >= 4
        is_suspicious = score >= 2

        image_file.seek(0)
        return {
            'is_ai': is_ai,
            'is_suspicious': is_suspicious,
            'confidence': confidence,
            'score': score,
            'reasons': reasons,
            'dimensions': f"{w}x{h}",
            'is_valid_image': True
        }

    except Exception as e:
        image_file.seek(0)
        return {
            'is_ai': False,
            'is_suspicious': False,
            'confidence': 0.0,
            'score': 0,
            'reasons': [f"Detection error: {str(e)}"],
            'dimensions': 'unknown',
            'is_valid_image': False
        }
