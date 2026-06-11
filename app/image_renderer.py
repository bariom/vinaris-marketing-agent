from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from app.image_prompt_generator import build_image_tone_guidance
from app.platform_profiles import get_platform_profile


class ImageRenderError(RuntimeError):
    pass


@dataclass(slots=True)
class RenderedImage:
    post_id: int
    file_path: Path
    model: str


class OpenAIImageRenderer:
    def __init__(
        self,
        *,
        api_key: str | None,
        output_dir: Path,
        model: str,
        quality: str = "medium",
        output_format: str = "png",
    ) -> None:
        self.api_key = api_key
        self.output_dir = output_dir
        self.model = model
        self.quality = quality
        self.output_format = output_format

    def render_post_image(
        self,
        *,
        post_id: int,
        platform: str,
        title: str,
        prompt: str,
        aspect_ratio: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
    ) -> RenderedImage:
        if not self.api_key:
            raise ImageRenderError("OPENAI_API_KEY non configurata.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        profile = get_platform_profile(platform)
        ratio = aspect_ratio or profile.recommended_aspect_ratio
        size = profile.recommended_size
        tone_guidance = build_image_tone_guidance(
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )

        client = OpenAI(api_key=self.api_key)
        full_prompt = (
            f"Create a premium social media image for {platform}.\n"
            f"Internal post title: {title}.\n"
            f"Visual direction: {prompt}\n"
            f"Editorial tone guidance: {tone_guidance}\n"
            f"Target aspect ratio: {ratio}.\n"
            f"Target size: {size}.\n"
            f"Platform visual goal: {profile.visual_goal}.\n"
            f"Composition guidance: {profile.composition_hint}.\n"
            "No visible marketing text overlay unless naturally integrated. "
            "Elegant, realistic, refined, suitable for a luxury wine-tech brand."
        )

        try:
            result = client.images.generate(
                model=self.model,
                prompt=full_prompt,
                size=size,
                quality=self.quality,
                output_format=self.output_format,
            )
        except Exception as exc:  # pragma: no cover
            raise ImageRenderError(f"Errore OpenAI durante la generazione immagine: {exc}") from exc

        if not result.data or not result.data[0].b64_json:
            raise ImageRenderError("OpenAI non ha restituito un'immagine.")

        extension = "jpg" if self.output_format == "jpeg" else self.output_format
        file_path = self.output_dir / _build_filename(post_id, platform, extension)

        try:
            file_path.write_bytes(base64.b64decode(result.data[0].b64_json))
        except Exception as exc:  # pragma: no cover
            raise ImageRenderError(f"Impossibile salvare l'immagine generata: {exc}") from exc

        return RenderedImage(post_id=post_id, file_path=file_path, model=self.model)


def _build_filename(post_id: int, platform: str, extension: str) -> str:
    safe_platform = platform.lower().replace(" ", "-")
    return f"post-{post_id}-{safe_platform}.{extension}"
