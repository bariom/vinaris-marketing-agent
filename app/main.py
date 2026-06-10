from __future__ import annotations

import argparse
from typing import Sequence

from app.config import get_settings
from app.content_generator import CATEGORIES
from app.image_renderer import ImageRenderError
from app.storage import PostStorage, StorageError, VALID_STATUSES
from app.workflows import (
    approve_post,
    export_post,
    generate_posts,
    publish_post,
    reject_post,
    render_batch_images,
    render_post_image,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI interna per contenuti marketing Vinaris.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Genera nuovi post draft.")
    generate_parser.add_argument("--count", type=int, default=5, help="Numero di post da generare.")
    generate_parser.add_argument(
        "--platform",
        choices=["Facebook", "Instagram", "LinkedIn"],
        help="Genera post solo per una piattaforma specifica.",
    )
    generate_parser.add_argument(
        "--category",
        choices=sorted(CATEGORIES),
        help="Genera post solo per una categoria specifica.",
    )
    generate_parser.add_argument(
        "--with-images",
        action="store_true",
        help="Genera anche un'immagine locale per ogni post via OpenAI.",
    )

    list_parser = subparsers.add_parser("list", help="Lista i post salvati.")
    list_parser.add_argument("--status", choices=sorted(VALID_STATUSES), help="Filtra per stato.")
    list_parser.add_argument("--limit", type=int, help="Numero massimo di risultati.")

    show_parser = subparsers.add_parser("show", help="Mostra il dettaglio completo di un post.")
    show_parser.add_argument("--id", type=int, required=True, help="ID del post.")

    render_parser = subparsers.add_parser("render-image", help="Genera un'immagine locale per un post.")
    render_parser.add_argument("--id", type=int, required=True, help="ID del post.")

    export_parser = subparsers.add_parser("export", help="Esporta un pack manuale per un post.")
    export_parser.add_argument("--id", type=int, required=True, help="ID del post.")

    render_batch_parser = subparsers.add_parser(
        "render-batch",
        help="Genera immagini locali per più post filtrati.",
    )
    render_batch_parser.add_argument(
        "--status",
        choices=sorted(VALID_STATUSES),
        default="draft",
        help="Filtra per stato. Default: draft.",
    )
    render_batch_parser.add_argument(
        "--platform",
        choices=["Facebook", "Instagram", "LinkedIn"],
        help="Filtra per piattaforma.",
    )
    render_batch_parser.add_argument("--limit", type=int, help="Numero massimo di post da elaborare.")
    render_batch_parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Genera immagini solo per i post che non hanno ancora image_path.",
    )

    approve_parser = subparsers.add_parser("approve", help="Approva un post draft.")
    approve_parser.add_argument("--id", type=int, required=True, help="ID del post.")

    reject_parser = subparsers.add_parser("reject", help="Rifiuta un post.")
    reject_parser.add_argument("--id", type=int, required=True, help="ID del post.")

    publish_parser = subparsers.add_parser("publish", help="Simula la pubblicazione di un post.")
    publish_parser.add_argument("--id", type=int, required=True, help="ID del post.")

    return parser


def handle_generate(
    count: int,
    with_images: bool,
    platform: str | None,
    category: str | None,
) -> int:
    records = generate_posts(count, with_images=with_images, platform=platform, category=category)
    for post in records:
        image_note = f" image={post.image_path}" if post.image_path else ""
        print(
            f"[draft] id={post.id} platform={post.platform} category={post.category} "
            f"title={post.title_internal}{image_note}"
        )
    print(f"Creati {len(records)} post in stato draft.")
    return 0


def handle_list(status: str | None, limit: int | None) -> int:
    settings = get_settings()
    storage = PostStorage(settings.database_path)
    posts = storage.list_posts(status=status, limit=limit)
    if not posts:
        print("Nessun post trovato.")
        return 0

    for post in posts:
        print(
            f"id={post.id} status={post.status} platform={post.platform} category={post.category} "
            f"ratio={post.platform_aspect_ratio or '-'} scheduled_at={post.scheduled_at or '-'} "
            f"image={'yes' if post.image_path else 'no'} "
            f"title={post.title_internal}"
        )
    return 0


def handle_show(post_id: int) -> int:
    settings = get_settings()
    storage = PostStorage(settings.database_path)
    post = storage.get_post(post_id)
    if post is None:
        print(f"Post {post_id} non trovato.")
        return 1

    details = [
        ("id", post.id),
        ("status", post.status),
        ("platform", post.platform),
        ("category", post.category),
        ("platform_aspect_ratio", post.platform_aspect_ratio or "-"),
        ("title_internal", post.title_internal),
        ("text_short", post.text_short),
        ("text_medium", post.text_medium),
        ("cta", post.cta),
        ("hashtags", post.hashtags),
        ("image_prompt", post.image_prompt),
        ("image_path", post.image_path or "-"),
        ("created_at", post.created_at),
        ("scheduled_at", post.scheduled_at or "-"),
        ("published_at", post.published_at or "-"),
    ]

    for key, value in details:
        print(f"{key}: {value}")
    return 0


def handle_approve(post_id: int) -> int:
    approve_post(post_id)
    print(f"Post {post_id} approvato.")
    return 0


def handle_reject(post_id: int) -> int:
    reject_post(post_id)
    print(f"Post {post_id} rifiutato.")
    return 0


def handle_publish(post_id: int) -> int:
    _, result = publish_post(post_id)
    print(result.message)
    return 0


def handle_render_image(post_id: int) -> int:
    post = render_post_image(post_id)
    print(f"Immagine generata: {post.image_path}.")
    return 0


def handle_export(post_id: int) -> int:
    result = export_post(post_id)
    print(f"Export creato in: {result.export_dir}")
    print(f"Caption: {result.caption_file}")
    print(f"JSON: {result.json_file}")
    if result.image_file:
        print(f"Immagine: {result.image_file}")
    return 0


def handle_render_batch(
    status: str,
    platform: str | None,
    limit: int | None,
    only_missing: bool,
) -> int:
    result = render_batch_images(
        status=status,
        platform=platform,
        limit=limit,
        only_missing=only_missing,
    )
    if not result.items:
        print("Nessun post da elaborare.")
        return 0

    for item in result.items:
        if item.ok:
            print(f"[ok] id={item.post_id} platform={item.platform} image={item.message}")
        else:
            print(f"[error] id={item.post_id} platform={item.platform} reason={item.message}")

    print(f"Render completato. generated={result.generated_count} failed={result.failed_count}")
    return 0 if result.failed_count == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "generate":
            return handle_generate(args.count, args.with_images, args.platform, args.category)
        if args.command == "list":
            return handle_list(args.status, args.limit)
        if args.command == "show":
            return handle_show(args.id)
        if args.command == "render-image":
            return handle_render_image(args.id)
        if args.command == "export":
            return handle_export(args.id)
        if args.command == "render-batch":
            return handle_render_batch(args.status, args.platform, args.limit, args.only_missing)
        if args.command == "approve":
            return handle_approve(args.id)
        if args.command == "reject":
            return handle_reject(args.id)
        if args.command == "publish":
            return handle_publish(args.id)
    except (ValueError, StorageError, ImageRenderError) as exc:
        print(f"Errore: {exc}")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
