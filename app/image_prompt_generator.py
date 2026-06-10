from __future__ import annotations

from app.platform_profiles import get_platform_profile


def generate_image_prompt(platform: str, category: str, angle: str) -> str:
    profile = get_platform_profile(platform)
    return (
        "Editorial lifestyle photo for a premium wine-tech brand, "
        f"focused on {category}, visual angle: {angle}, platform: {platform}. "
        f"Recommended aspect ratio: {profile.recommended_aspect_ratio}. "
        f"Visual goal: {profile.visual_goal}. "
        f"Composition hint: {profile.composition_hint}. "
        "Private wine cellar setting, refined lighting, elegant bottles, "
        "smartphone app visible in a discreet and credible way, "
        "luxury but realistic aesthetic, sober composition, high detail, no loud advertising text."
    )
