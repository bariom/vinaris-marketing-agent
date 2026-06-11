from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.platform_profiles import get_platform_profile


VALID_STATUSES = {"draft", "approved", "published", "rejected"}


@dataclass(slots=True)
class PostRecord:
    id: int
    platform: str
    category: str
    platform_aspect_ratio: str | None
    seriousness_level: str | None
    tone_warmth: str | None
    promotional_intensity: str | None
    title_internal: str
    text_short: str
    text_medium: str
    cta: str
    hashtags: str
    image_prompt: str
    status: str
    created_at: str
    scheduled_at: str | None
    published_at: str | None
    image_path: str | None


class StorageError(RuntimeError):
    pass


class PostStorage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    category TEXT NOT NULL,
                    platform_aspect_ratio TEXT,
                    seriousness_level TEXT,
                    tone_warmth TEXT,
                    promotional_intensity TEXT,
                    title_internal TEXT NOT NULL,
                    text_short TEXT NOT NULL,
                    text_medium TEXT NOT NULL,
                    cta TEXT NOT NULL,
                    hashtags TEXT NOT NULL,
                    image_prompt TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    scheduled_at TEXT,
                    published_at TEXT,
                    image_path TEXT
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(posts)").fetchall()
            }
            if "image_path" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN image_path TEXT")
            if "platform_aspect_ratio" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN platform_aspect_ratio TEXT")
            if "seriousness_level" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN seriousness_level TEXT")
            if "tone_warmth" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN tone_warmth TEXT")
            if "promotional_intensity" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN promotional_intensity TEXT")
            connection.commit()

    def create_post(self, payload: dict[str, Any]) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO posts (
                    platform, category, platform_aspect_ratio, seriousness_level, tone_warmth, promotional_intensity, title_internal, text_short, text_medium,
                    cta, hashtags, image_prompt, status, created_at, scheduled_at, published_at
                    , image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["platform"],
                    payload["category"],
                    payload.get("platform_aspect_ratio"),
                    payload.get("seriousness_level"),
                    payload.get("tone_warmth"),
                    payload.get("promotional_intensity"),
                    payload["title_internal"],
                    payload["text_short"],
                    payload["text_medium"],
                    payload["cta"],
                    payload["hashtags"],
                    payload["image_prompt"],
                    payload["status"],
                    payload["created_at"],
                    payload.get("scheduled_at"),
                    payload.get("published_at"),
                    payload.get("image_path"),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def get_post(self, post_id: int) -> PostRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM posts WHERE id = ?",
                (post_id,),
            ).fetchone()
        return self._row_to_post(row) if row else None

    def list_posts(self, status: str | None = None, limit: int | None = None) -> list[PostRecord]:
        query = "SELECT * FROM posts"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY datetime(created_at) DESC, id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_post(row) for row in rows]

    def update_status(self, post_id: int, status: str) -> None:
        if status not in VALID_STATUSES:
            raise StorageError(f"Stato non valido: {status}")

        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE posts SET status = ? WHERE id = ?",
                (status, post_id),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise StorageError(f"Post {post_id} non trovato.")

    def mark_published(self, post_id: int, published_at: datetime) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE posts
                SET status = 'published', published_at = ?
                WHERE id = ?
                """,
                (published_at.isoformat(timespec="seconds"), post_id),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise StorageError(f"Post {post_id} non trovato.")

    def set_image_path(self, post_id: int, image_path: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE posts SET image_path = ? WHERE id = ?",
                (image_path, post_id),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise StorageError(f"Post {post_id} non trovato.")

    def delete_post(self, post_id: int) -> None:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            connection.commit()
        if cursor.rowcount == 0:
            raise StorageError(f"Post {post_id} non trovato.")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_post(row: sqlite3.Row) -> PostRecord:
        platform = row["platform"]
        aspect_ratio = row["platform_aspect_ratio"] or get_platform_profile(platform).recommended_aspect_ratio
        return PostRecord(
            id=row["id"],
            platform=platform,
            category=row["category"],
            platform_aspect_ratio=aspect_ratio,
            seriousness_level=row["seriousness_level"],
            tone_warmth=row["tone_warmth"],
            promotional_intensity=row["promotional_intensity"],
            title_internal=row["title_internal"],
            text_short=row["text_short"],
            text_medium=row["text_medium"],
            cta=row["cta"],
            hashtags=row["hashtags"],
            image_prompt=row["image_prompt"],
            status=row["status"],
            created_at=row["created_at"],
            scheduled_at=row["scheduled_at"],
            published_at=row["published_at"],
            image_path=row["image_path"],
        )
