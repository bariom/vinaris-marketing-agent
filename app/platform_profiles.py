from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformProfile:
    name: str
    recommended_aspect_ratio: str
    recommended_size: str
    visual_goal: str
    composition_hint: str


PLATFORM_PROFILES: dict[str, PlatformProfile] = {
    "Instagram": PlatformProfile(
        name="Instagram",
        recommended_aspect_ratio="4:5",
        recommended_size="1024x1280",
        visual_goal="high visual appeal for feed browsing",
        composition_hint="centered subject, strong focal point, premium lifestyle aesthetic",
    ),
    "Facebook": PlatformProfile(
        name="Facebook",
        recommended_aspect_ratio="1.91:1",
        recommended_size="1536x800",
        visual_goal="clear storytelling in feed previews",
        composition_hint="wider composition, contextual cellar environment, balanced negative space",
    ),
    "LinkedIn": PlatformProfile(
        name="LinkedIn",
        recommended_aspect_ratio="1.91:1",
        recommended_size="1536x800",
        visual_goal="professional credibility and product clarity",
        composition_hint="clean editorial composition, understated product presence, strategic tone",
    ),
}


def get_platform_profile(platform: str) -> PlatformProfile:
    return PLATFORM_PROFILES.get(
        platform,
        PlatformProfile(
            name=platform,
            recommended_aspect_ratio="1:1",
            recommended_size="1024x1024",
            visual_goal="balanced social media asset",
            composition_hint="clean composition, premium tone",
        ),
    )
