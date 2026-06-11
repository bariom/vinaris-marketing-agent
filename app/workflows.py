from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass

from app.config import Settings, get_settings
from app.content_generator import ContentGenerator
from app.exporter import ExportResult, delete_export_pack, export_post_pack
from app.image_renderer import OpenAIImageRenderer
from app.publisher_stub import PublishResult, simulate_publish
from app.storage import PostRecord, PostStorage, StorageError


@dataclass(slots=True)
class RenderBatchItemResult:
    post_id: int
    platform: str
    ok: bool
    message: str


@dataclass(slots=True)
class RenderBatchResult:
    generated_count: int
    failed_count: int
    items: list[RenderBatchItemResult]


def build_storage(settings: Settings | None = None) -> PostStorage:
    active_settings = settings or get_settings()
    return PostStorage(active_settings.database_path)


def generate_posts(
    count: int,
    with_images: bool = False,
    platform: str | None = None,
    category: str | None = None,
    seriousness_level: str = "equilibrato",
    tone_warmth: str = "sobrio",
    promotional_intensity: str = "discreto",
    target_age_range: str | None = None,
    target_gender: str | None = None,
    target_region: str | None = None,
    target_expertise: str | None = None,
    target_spending_power: str | None = None,
    settings: Settings | None = None,
) -> list[PostRecord]:
    active_settings = settings or get_settings()
    storage = build_storage(active_settings)
    generator = ContentGenerator(active_settings.openai_api_key)
    renderer = OpenAIImageRenderer(
        api_key=active_settings.openai_api_key,
        output_dir=active_settings.generated_images_dir,
        model=active_settings.openai_image_model,
        quality=active_settings.openai_image_quality,
        output_format=active_settings.openai_image_format,
    )

    records: list[PostRecord] = []
    recent_history = storage.list_recent_generation_history(limit=36)
    for post in generator.generate_posts(
        count,
        platform=platform,
        category=category,
        seriousness_level=seriousness_level,
        tone_warmth=tone_warmth,
        promotional_intensity=promotional_intensity,
        target_age_range=target_age_range,
        target_gender=target_gender,
        target_region=target_region,
        target_expertise=target_expertise,
        target_spending_power=target_spending_power,
        recent_history=recent_history,
    ):
        payload = post.to_dict()
        post_id = storage.create_post(payload)
        storage.archive_generated_post(payload)
        if with_images:
            rendered = renderer.render_post_image(
                post_id=post_id,
                platform=post.platform,
                title=post.title_internal,
                prompt=post.image_prompt,
                aspect_ratio=post.platform_aspect_ratio,
                seriousness_level=post.seriousness_level or "equilibrato",
                tone_warmth=post.tone_warmth or "sobrio",
                promotional_intensity=post.promotional_intensity or "discreto",
            )
            storage.set_image_path(post_id, str(rendered.file_path))
        record = storage.get_post(post_id)
        if record is None:
            raise StorageError(f"Post {post_id} non trovato dopo la creazione.")
        records.append(record)
    return records


def approve_post(post_id: int, settings: Settings | None = None) -> PostRecord:
    storage = build_storage(settings)
    post = _require_post(storage, post_id)
    if post.status == "published":
        raise StorageError(f"Post {post_id} già pubblicato.")
    if post.status != "approved":
        storage.update_status(post_id, "approved")
    return _require_post(storage, post_id)


def reject_post(post_id: int, settings: Settings | None = None) -> PostRecord:
    storage = build_storage(settings)
    post = _require_post(storage, post_id)
    if post.status == "published":
        raise StorageError(f"Post {post_id} già pubblicato.")
    storage.update_status(post_id, "rejected")
    return _require_post(storage, post_id)


def publish_post(post_id: int, settings: Settings | None = None) -> tuple[PostRecord, PublishResult]:
    storage = build_storage(settings)
    post = _require_post(storage, post_id)
    if post.status != "approved":
        raise StorageError(f"Post {post_id} non è approvato. Stato attuale: {post.status}.")

    result = simulate_publish(post.id, post.platform)
    storage.mark_published(post.id, result.published_at)
    return _require_post(storage, post_id), result


def render_post_image(post_id: int, settings: Settings | None = None) -> PostRecord:
    active_settings = settings or get_settings()
    storage = build_storage(active_settings)
    post = _require_post(storage, post_id)
    renderer = OpenAIImageRenderer(
        api_key=active_settings.openai_api_key,
        output_dir=active_settings.generated_images_dir,
        model=active_settings.openai_image_model,
        quality=active_settings.openai_image_quality,
        output_format=active_settings.openai_image_format,
    )
    rendered = renderer.render_post_image(
        post_id=post.id,
        platform=post.platform,
        title=post.title_internal,
        prompt=post.image_prompt,
        aspect_ratio=post.platform_aspect_ratio,
        seriousness_level=post.seriousness_level or "equilibrato",
        tone_warmth=post.tone_warmth or "sobrio",
        promotional_intensity=post.promotional_intensity or "discreto",
    )
    storage.set_image_path(post.id, str(rendered.file_path))
    return _require_post(storage, post_id)


def render_batch_images(
    *,
    status: str = "draft",
    platform: str | None = None,
    limit: int | None = None,
    only_missing: bool = False,
    settings: Settings | None = None,
) -> RenderBatchResult:
    active_settings = settings or get_settings()
    storage = build_storage(active_settings)
    renderer = OpenAIImageRenderer(
        api_key=active_settings.openai_api_key,
        output_dir=active_settings.generated_images_dir,
        model=active_settings.openai_image_model,
        quality=active_settings.openai_image_quality,
        output_format=active_settings.openai_image_format,
    )

    posts = storage.list_posts(status=status, limit=limit)
    if platform:
        posts = [post for post in posts if post.platform == platform]
    if only_missing:
        posts = [post for post in posts if not post.image_path]

    items: list[RenderBatchItemResult] = []
    generated_count = 0
    failed_count = 0

    for post in posts:
        try:
            rendered = renderer.render_post_image(
                post_id=post.id,
                platform=post.platform,
                title=post.title_internal,
                prompt=post.image_prompt,
                aspect_ratio=post.platform_aspect_ratio,
                seriousness_level=post.seriousness_level or "equilibrato",
                tone_warmth=post.tone_warmth or "sobrio",
                promotional_intensity=post.promotional_intensity or "discreto",
            )
            storage.set_image_path(post.id, str(rendered.file_path))
            generated_count += 1
            items.append(RenderBatchItemResult(post.id, post.platform, True, str(rendered.file_path)))
        except Exception as exc:
            failed_count += 1
            items.append(RenderBatchItemResult(post.id, post.platform, False, str(exc)))

    return RenderBatchResult(generated_count=generated_count, failed_count=failed_count, items=items)


def export_post(post_id: int, settings: Settings | None = None) -> ExportResult:
    active_settings = settings or get_settings()
    storage = build_storage(active_settings)
    post = _require_post(storage, post_id)
    return export_post_pack(post, active_settings.exports_dir)


def delete_post(post_id: int, settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    storage = build_storage(active_settings)
    post = _require_post(storage, post_id)

    _delete_image_if_present(post.image_path)
    delete_export_pack(post, active_settings.exports_dir)
    storage.delete_post(post.id)


def _require_post(storage: PostStorage, post_id: int) -> PostRecord:
    post = storage.get_post(post_id)
    if post is None:
        raise StorageError(f"Post {post_id} non trovato.")
    return post


def _delete_image_if_present(image_path: str | None) -> None:
    if not image_path:
        return
    path = Path(image_path)
    if path.exists():
        path.unlink()
