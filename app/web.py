from __future__ import annotations

from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from app.config import get_settings
from app.content_generator import (
    CATEGORIES,
    PROMOTIONAL_LEVELS,
    SERIOUSNESS_LEVELS,
    WARMTH_LEVELS,
)
from app.image_renderer import ImageRenderError
from app.storage import PostStorage, StorageError, VALID_STATUSES
from app.workflows import (
    approve_post,
    delete_post,
    export_post,
    generate_posts,
    publish_post,
    reject_post,
    render_batch_images,
    render_post_image,
)


PLATFORMS = ("Facebook", "Instagram", "LinkedIn")

app = Flask(__name__)
app.config["SECRET_KEY"] = get_settings().web_secret_key


@app.get("/")
def dashboard():
    settings = get_settings()
    storage = PostStorage(settings.database_path)
    status = request.args.get("status") or None
    platform = request.args.get("platform") or None

    posts = storage.list_posts(status=status)
    if platform:
        posts = [post for post in posts if post.platform == platform]

    stats = {current_status: len(storage.list_posts(status=current_status)) for current_status in sorted(VALID_STATUSES)}
    return render_template(
        "dashboard.html",
        posts=posts,
        stats=stats,
        active_status=status or "",
        active_platform=platform or "",
        valid_statuses=sorted(VALID_STATUSES),
        categories=sorted(CATEGORIES),
        platforms=PLATFORMS,
        seriousness_levels=SERIOUSNESS_LEVELS,
        warmth_levels=WARMTH_LEVELS,
        promotional_levels=PROMOTIONAL_LEVELS,
    )


@app.get("/posts/<int:post_id>")
def post_detail(post_id: int):
    settings = get_settings()
    storage = PostStorage(settings.database_path)
    post = storage.get_post(post_id)
    if post is None:
        flash(f"Post {post_id} non trovato.", "error")
        return redirect(url_for("dashboard"))

    image_url = url_for("serve_image", post_id=post.id) if post.image_path else None
    return render_template("post_detail.html", post=post, image_url=image_url)


@app.get("/images/<int:post_id>")
def serve_image(post_id: int):
    settings = get_settings()
    storage = PostStorage(settings.database_path)
    post = storage.get_post(post_id)
    if post is None or not post.image_path:
        return redirect(url_for("dashboard"))

    image_path = Path(post.image_path)
    if not image_path.exists():
        flash(f"Immagine del post {post_id} non trovata sul filesystem.", "error")
        return redirect(url_for("post_detail", post_id=post_id))
    return send_file(image_path)


@app.post("/generate")
def generate():
    try:
        count = max(1, int(request.form.get("count", "5")))
        requested_with_images = request.form.get("with_images") == "on"
        platform = request.form.get("platform") or None
        category = request.form.get("category") or None
        seriousness_level = request.form.get("seriousness_level") or "equilibrato"
        tone_warmth = request.form.get("tone_warmth") or "sobrio"
        promotional_intensity = request.form.get("promotional_intensity") or "discreto"
        with_images = requested_with_images and count == 1

        records = generate_posts(
            count,
            with_images=with_images,
            platform=platform,
            category=category,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )

        if requested_with_images and count > 1:
            flash(
                (
                    f"Creati {len(records)} post senza immagini inline. "
                    "Per evitare timeout web, genera le immagini dopo con Render batch."
                ),
                "warning",
            )
        else:
            flash(f"Creati {len(records)} post.", "success")
    except (ValueError, StorageError, ImageRenderError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


@app.post("/posts/<int:post_id>/approve")
def approve(post_id: int):
    return _run_post_action(post_id, approve_post, "Post approvato.")


@app.post("/posts/<int:post_id>/reject")
def reject(post_id: int):
    return _run_post_action(post_id, reject_post, "Post rifiutato.")


@app.post("/posts/<int:post_id>/publish")
def publish(post_id: int):
    try:
        _, result = publish_post(post_id)
        flash(result.message, "success")
    except (StorageError, ImageRenderError) as exc:
        flash(str(exc), "error")
    return redirect(_redirect_target(post_id))


@app.post("/posts/<int:post_id>/render-image")
def render_image(post_id: int):
    try:
        post = render_post_image(post_id)
        flash(f"Immagine generata per il post {post.id}.", "success")
    except (StorageError, ImageRenderError) as exc:
        flash(str(exc), "error")
    return redirect(_redirect_target(post_id))


@app.post("/posts/<int:post_id>/export")
def export(post_id: int):
    try:
        result = export_post(post_id)
        flash(f"Export creato in {result.export_dir}.", "success")
    except (StorageError, ImageRenderError, ValueError, OSError) as exc:
        flash(str(exc), "error")
    return redirect(_redirect_target(post_id))


@app.post("/posts/<int:post_id>/delete")
def delete(post_id: int):
    try:
        delete_post(post_id)
        flash(f"Post {post_id} eliminato con relativi asset.", "success")
        return redirect(url_for("dashboard"))
    except (StorageError, ImageRenderError, ValueError, OSError) as exc:
        flash(str(exc), "error")
        return redirect(_redirect_target(post_id))


@app.post("/posts/delete-selected")
def delete_selected():
    raw_ids = request.form.getlist("post_ids")
    if not raw_ids:
        flash("Seleziona almeno un post da eliminare.", "warning")
        return redirect(url_for("dashboard"))

    try:
        post_ids = sorted({int(post_id) for post_id in raw_ids})
    except ValueError:
        flash("Selezione non valida.", "error")
        return redirect(url_for("dashboard"))

    try:
        deleted_count = 0
        for post_id in post_ids:
            delete_post(post_id)
            deleted_count += 1
        flash(f"Eliminati {deleted_count} post con relativi asset.", "success")
    except (StorageError, ImageRenderError, ValueError, OSError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


@app.post("/render-batch")
def render_batch():
    try:
        status = request.form.get("status") or "draft"
        platform = request.form.get("platform") or None
        limit_value = request.form.get("limit") or ""
        limit = int(limit_value) if limit_value else None
        only_missing = request.form.get("only_missing") == "on"
        result = render_batch_images(
            status=status,
            platform=platform,
            limit=limit,
            only_missing=only_missing,
        )
        flash(
            f"Render batch completato. generated={result.generated_count} failed={result.failed_count}",
            "success" if result.failed_count == 0 else "warning",
        )
    except (StorageError, ImageRenderError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


def _run_post_action(post_id: int, action, message: str):
    try:
        action(post_id)
        flash(message, "success")
    except (StorageError, ImageRenderError) as exc:
        flash(str(exc), "error")
    return redirect(_redirect_target(post_id))


def _redirect_target(post_id: int):
    source = request.form.get("source", "dashboard")
    if source == "detail":
        return url_for("post_detail", post_id=post_id)
    return url_for("dashboard")


if __name__ == "__main__":
    app.run(debug=True)
