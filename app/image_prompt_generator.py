from __future__ import annotations

from app.platform_profiles import get_platform_profile


def generate_image_prompt(
    platform: str,
    category: str,
    angle: str,
    *,
    seriousness_level: str = "equilibrato",
    tone_warmth: str = "sobrio",
    promotional_intensity: str = "discreto",
) -> str:
    profile = get_platform_profile(platform)
    tone_guidance = build_image_tone_guidance(
        seriousness_level=seriousness_level,
        tone_warmth=tone_warmth,
        promotional_intensity=promotional_intensity,
    )
    return (
        "Editorial lifestyle photo for a premium wine-tech brand, "
        f"focused on {category}, visual angle: {angle}, platform: {platform}. "
        f"Recommended aspect ratio: {profile.recommended_aspect_ratio}. "
        f"Visual goal: {profile.visual_goal}. "
        f"Composition hint: {profile.composition_hint}. "
        f"{tone_guidance} "
        "Private wine cellar setting, refined lighting, elegant bottles, "
        "smartphone app visible in a discreet and credible way, "
        "luxury but realistic aesthetic, sober composition, high detail, no loud advertising text."
    )


def build_image_tone_guidance(
    *,
    seriousness_level: str = "equilibrato",
    tone_warmth: str = "sobrio",
    promotional_intensity: str = "discreto",
) -> str:
    seriousness_guidance = {
        "alto": "Visual tone: highly serious, restrained, authoritative, editorial, no playful cues.",
        "equilibrato": "Visual tone: balanced, polished, elegant, approachable but still premium.",
        "leggero": "Visual tone: lighter and more relaxed, airy, inviting, still refined and never goofy.",
    }[seriousness_level]
    warmth_guidance = {
        "sobrio": "Emotional temperature: composed, cool, discreet, controlled facial expressions and body language.",
        "caldo": "Emotional temperature: warmer, more human, subtly welcoming, natural lived-in atmosphere.",
        "coinvolgente": "Emotional temperature: more vivid and inviting, engaging moment, stronger sense of presence and ease.",
    }[tone_warmth]
    promotional_guidance = {
        "discreto": "Brand presence should remain subtle and understated, with no overt sales energy.",
        "equilibrato": "Brand presence can be slightly more visible and product-oriented, but still tasteful.",
        "deciso": "Brand presence may be clearer and more intentional, with stronger product focus but no hard-sell look.",
    }[promotional_intensity]
    return f"{seriousness_guidance} {warmth_guidance} {promotional_guidance}"
