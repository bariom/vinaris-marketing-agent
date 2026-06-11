from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from app.post_formatter import build_ready_caption
from app.storage import PostRecord


@dataclass(slots=True)
class ExportResult:
    post_id: int
    export_dir: Path
    caption_file: Path
    json_file: Path
    image_file: Path | None


class ExportError(RuntimeError):
    pass


def export_post_pack(post: PostRecord, exports_dir: Path) -> ExportResult:
    exports_dir.mkdir(parents=True, exist_ok=True)
    export_dir = export_dir_for_post(post, exports_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    caption_file = export_dir / "caption.txt"
    json_file = export_dir / "post.json"

    caption_file.write_text(_build_caption(post), encoding="utf-8")
    json_file.write_text(json.dumps(asdict(post), ensure_ascii=False, indent=2), encoding="utf-8")

    image_file: Path | None = None
    if post.image_path:
        source = Path(post.image_path)
        if source.exists():
            image_file = export_dir / source.name
            shutil.copy2(source, image_file)
        else:
            raise ExportError(f"Immagine non trovata sul filesystem: {source}")

    return ExportResult(
        post_id=post.id,
        export_dir=export_dir,
        caption_file=caption_file,
        json_file=json_file,
        image_file=image_file,
    )


def _build_caption(post: PostRecord) -> str:
    return f"{build_ready_caption(post)}\n"


def _build_export_folder_name(post: PostRecord) -> str:
    safe_platform = post.platform.lower().replace(" ", "-")
    return f"post-{post.id}-{safe_platform}"


def export_dir_for_post(post: PostRecord, exports_dir: Path) -> Path:
    return exports_dir / _build_export_folder_name(post)


def delete_export_pack(post: PostRecord, exports_dir: Path) -> None:
    export_dir = export_dir_for_post(post, exports_dir)
    if export_dir.exists():
        shutil.rmtree(export_dir)
