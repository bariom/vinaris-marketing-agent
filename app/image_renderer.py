from __future__ import annotations

import base64
from dataclasses import dataclass
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from typing import Iterable

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
        return self.render_post_variants(
            post_id=post_id,
            platform=platform,
            title=title,
            prompt=prompt,
            count=1,
            aspect_ratio=aspect_ratio,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )[0]

    def render_post_variants(
        self,
        *,
        post_id: int,
        platform: str,
        title: str,
        prompt: str,
        count: int = 3,
        aspect_ratio: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
    ) -> list[RenderedImage]:
        if count < 1 or count > 4:
            raise ImageRenderError("Il numero di varianti deve essere compreso tra 1 e 4.")
        full_prompt, size = self._build_generation_prompt(
            platform=platform,
            title=title,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )
        try:
            result = self._client().images.generate(
                model=self.model,
                prompt=full_prompt,
                size=size,
                quality=self.quality,
                output_format=self.output_format,
                n=count,
            )
        except Exception as exc:  # pragma: no cover
            raise ImageRenderError(f"Errore OpenAI durante la generazione immagine: {exc}") from exc
        return self._save_result_images(result, post_id=post_id, platform=platform, operation="variant")

    def refine_post_image(
        self,
        *,
        post_id: int,
        platform: str,
        source_image: Path,
        instruction: str,
        reference_images: Iterable[Path] = (),
    ) -> RenderedImage:
        if not instruction.strip():
            raise ImageRenderError("Inserisci un'istruzione di rifinitura.")
        if not source_image.is_file():
            raise ImageRenderError(f"Immagine sorgente non trovata: {source_image}")

        references = [path for path in reference_images if path.is_file()]
        try:
            with ExitStack() as stack:
                images = [stack.enter_context(source_image.open("rb"))]
                images.extend(stack.enter_context(path.open("rb")) for path in references)
                result = self._client().images.edit(
                    model=self.model,
                    image=images,
                    prompt=(
                        "Refine the first image for Vinaris, a premium wine-tech brand. "
                        f"Requested change: {instruction.strip()}\n"
                        "Preserve the core subject and editorial quality. "
                        "Use any following images only as brand-style references. "
                        "No visible marketing text overlay unless explicitly requested."
                    ),
                    output_format=self.output_format,
                )
        except Exception as exc:  # pragma: no cover
            raise ImageRenderError(f"Errore OpenAI durante la rifinitura immagine: {exc}") from exc
        return self._save_result_images(result, post_id=post_id, platform=platform, operation="refined")[0]

    def _client(self) -> OpenAI:
        if not self.api_key:
            raise ImageRenderError("OPENAI_API_KEY non configurata.")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return OpenAI(api_key=self.api_key)

    def _build_generation_prompt(
        self,
        *,
        platform: str,
        title: str,
        prompt: str,
        aspect_ratio: str | None,
        seriousness_level: str,
        tone_warmth: str,
        promotional_intensity: str,
    ) -> tuple[str, str]:
        profile = get_platform_profile(platform)
        ratio = aspect_ratio or profile.recommended_aspect_ratio
        size = profile.recommended_size
        tone_guidance = build_image_tone_guidance(
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )
        return (
            f"Create a premium social media image for {platform}.\n"
            f"Internal post title: {title}.\n"
            f"Visual direction: {prompt}\n"
            f"Editorial tone guidance: {tone_guidance}\n"
            f"Target aspect ratio: {ratio}.\n"
            f"Target size: {size}.\n"
            f"Platform visual goal: {profile.visual_goal}.\n"
            f"Composition guidance: {profile.composition_hint}.\n"
            "No visible marketing text overlay unless naturally integrated. "
            "Elegant, realistic, refined, suitable for a luxury wine-tech brand.",
            size,
        )

    def _save_result_images(self, result: object, *, post_id: int, platform: str, operation: str) -> list[RenderedImage]:
        data = getattr(result, "data", None)
        if not data:
            raise ImageRenderError("OpenAI non ha restituito immagini.")
        extension = "jpg" if self.output_format == "jpeg" else self.output_format
        generated: list[RenderedImage] = []
        stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        for index, item in enumerate(data, start=1):
            encoded = getattr(item, "b64_json", None)
            if not encoded:
                continue
            file_path = self.output_dir / _build_filename(post_id, platform, extension, operation, stamp, index)
            try:
                file_path.write_bytes(base64.b64decode(encoded))
            except Exception as exc:  # pragma: no cover
                raise ImageRenderError(f"Impossibile salvare l'immagine generata: {exc}") from exc
            generated.append(RenderedImage(post_id=post_id, file_path=file_path, model=self.model))
        if not generated:
            raise ImageRenderError("OpenAI non ha restituito immagini utilizzabili.")
        return generated


def _build_filename(post_id: int, platform: str, extension: str, operation: str, stamp: str, index: int) -> str:
    safe_platform = platform.lower().replace(" ", "-")
    return f"post-{post_id}-{safe_platform}-{operation}-{stamp}-{index}.{extension}"
