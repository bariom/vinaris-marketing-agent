from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

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
    target_age_range: str | None
    target_gender: str | None
    target_region: str | None
    target_expertise: str | None
    target_spending_power: str | None
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


@dataclass(slots=True)
class ImageAsset:
    id: int
    post_id: int
    file_path: str
    source: str
    instruction: str | None
    is_selected: bool
    created_at: str


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
                    target_age_range TEXT,
                    target_gender TEXT,
                    target_region TEXT,
                    target_expertise TEXT,
                    target_spending_power TEXT,
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS generation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    category TEXT NOT NULL,
                    seriousness_level TEXT,
                    tone_warmth TEXT,
                    promotional_intensity TEXT,
                    target_age_range TEXT,
                    target_gender TEXT,
                    target_region TEXT,
                    target_expertise TEXT,
                    target_spending_power TEXT,
                    title_internal TEXT NOT NULL,
                    text_short TEXT NOT NULL,
                    text_medium TEXT NOT NULL,
                    cta TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS image_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    source TEXT NOT NULL,
                    instruction TEXT,
                    is_selected INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(post_id, file_path)
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(posts)").fetchall()
            }
            history_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(generation_history)").fetchall()
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
            if "target_age_range" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN target_age_range TEXT")
            if "target_gender" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN target_gender TEXT")
            if "target_region" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN target_region TEXT")
            if "target_expertise" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN target_expertise TEXT")
            if "target_spending_power" not in columns:
                connection.execute("ALTER TABLE posts ADD COLUMN target_spending_power TEXT")
            if "target_age_range" not in history_columns:
                connection.execute("ALTER TABLE generation_history ADD COLUMN target_age_range TEXT")
            if "target_gender" not in history_columns:
                connection.execute("ALTER TABLE generation_history ADD COLUMN target_gender TEXT")
            if "target_region" not in history_columns:
                connection.execute("ALTER TABLE generation_history ADD COLUMN target_region TEXT")
            if "target_expertise" not in history_columns:
                connection.execute("ALTER TABLE generation_history ADD COLUMN target_expertise TEXT")
            if "target_spending_power" not in history_columns:
                connection.execute("ALTER TABLE generation_history ADD COLUMN target_spending_power TEXT")
            connection.execute(
                """
                INSERT OR IGNORE INTO image_assets (post_id, file_path, source, is_selected, created_at)
                SELECT id, image_path, 'legacy', 1, created_at
                FROM posts
                WHERE image_path IS NOT NULL
                """
            )
            connection.commit()

    def create_post(self, payload: dict[str, Any]) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO posts (
                    platform, category, platform_aspect_ratio, seriousness_level, tone_warmth, promotional_intensity,
                    target_age_range, target_gender, target_region, target_expertise, target_spending_power, title_internal, text_short, text_medium,
                    cta, hashtags, image_prompt, status, created_at, scheduled_at, published_at
                    , image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["platform"],
                    payload["category"],
                    payload.get("platform_aspect_ratio"),
                    payload.get("seriousness_level"),
                    payload.get("tone_warmth"),
                    payload.get("promotional_intensity"),
                    payload.get("target_age_range"),
                    payload.get("target_gender"),
                    payload.get("target_region"),
                    payload.get("target_expertise"),
                    payload.get("target_spending_power"),
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

    def add_image_assets(
        self,
        post_id: int,
        image_paths: list[str],
        *,
        source: str,
        instruction: str | None = None,
        select_first: bool = False,
    ) -> list[ImageAsset]:
        if not image_paths:
            return []

        created_at = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            post_exists = connection.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone()
            if post_exists is None:
                raise StorageError(f"Post {post_id} non trovato.")

            for image_path in image_paths:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO image_assets (post_id, file_path, source, instruction, is_selected, created_at)
                    VALUES (?, ?, ?, ?, 0, ?)
                    """,
                    (post_id, image_path, source, instruction, created_at),
                )

            if select_first:
                self._select_image_asset_in_connection(connection, post_id, image_paths[0])
            connection.commit()

        assets = self.list_image_assets(post_id)
        paths = set(image_paths)
        return [asset for asset in assets if asset.file_path in paths]

    def list_image_assets(self, post_id: int) -> list[ImageAsset]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM image_assets
                WHERE post_id = ?
                ORDER BY is_selected DESC, datetime(created_at) DESC, id DESC
                """,
                (post_id,),
            ).fetchall()
        return [self._row_to_image_asset(row) for row in rows]

    def select_image_asset(self, post_id: int, asset_id: int) -> ImageAsset:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM image_assets WHERE id = ? AND post_id = ?",
                (asset_id, post_id),
            ).fetchone()
            if row is None:
                raise StorageError(f"Asset {asset_id} non trovato per il post {post_id}.")
            self._select_image_asset_in_connection(connection, post_id, row["file_path"])
            connection.commit()
        asset = next((item for item in self.list_image_assets(post_id) if item.id == asset_id), None)
        if asset is None:  # pragma: no cover
            raise StorageError(f"Asset {asset_id} non trovato dopo la selezione.")
        return asset

    def delete_post(self, post_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM image_assets WHERE post_id = ?", (post_id,))
            cursor = connection.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            connection.commit()
        if cursor.rowcount == 0:
            raise StorageError(f"Post {post_id} non trovato.")

    def archive_generated_post(self, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO generation_history (
                    platform, category, seriousness_level, tone_warmth, promotional_intensity,
                    target_age_range, target_gender, target_region, target_expertise, target_spending_power,
                    title_internal, text_short, text_medium, cta, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["platform"],
                    payload["category"],
                    payload.get("seriousness_level"),
                    payload.get("tone_warmth"),
                    payload.get("promotional_intensity"),
                    payload.get("target_age_range"),
                    payload.get("target_gender"),
                    payload.get("target_region"),
                    payload.get("target_expertise"),
                    payload.get("target_spending_power"),
                    payload["title_internal"],
                    payload["text_short"],
                    payload["text_medium"],
                    payload["cta"],
                    payload["created_at"],
                ),
            )
            connection.commit()

    def list_recent_generation_history(self, limit: int = 24) -> list[dict[str, str]]:
        query = """
            SELECT
                platform,
                category,
                target_age_range,
                target_gender,
                target_region,
                target_expertise,
                target_spending_power,
                title_internal,
                text_short,
                text_medium,
                cta,
                created_at
            FROM generation_history
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
        """
        with self._connect() as connection:
            rows = connection.execute(query, (limit,)).fetchall()
        return [
            {
                "platform": str(row["platform"]),
                "category": str(row["category"]),
                "target_age_range": str(row["target_age_range"] or ""),
                "target_gender": str(row["target_gender"] or ""),
                "target_region": str(row["target_region"] or ""),
                "target_expertise": str(row["target_expertise"] or ""),
                "target_spending_power": str(row["target_spending_power"] or ""),
                "title_internal": str(row["title_internal"]),
                "text_short": str(row["text_short"]),
                "text_medium": str(row["text_medium"]),
                "cta": str(row["cta"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

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
            target_age_range=row["target_age_range"],
            target_gender=row["target_gender"],
            target_region=row["target_region"],
            target_expertise=row["target_expertise"],
            target_spending_power=row["target_spending_power"],
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

    @staticmethod
    def _row_to_image_asset(row: sqlite3.Row) -> ImageAsset:
        return ImageAsset(
            id=row["id"],
            post_id=row["post_id"],
            file_path=row["file_path"],
            source=row["source"],
            instruction=row["instruction"],
            is_selected=bool(row["is_selected"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _select_image_asset_in_connection(connection: sqlite3.Connection, post_id: int, file_path: str) -> None:
        connection.execute("UPDATE image_assets SET is_selected = 0 WHERE post_id = ?", (post_id,))
        connection.execute(
            "UPDATE image_assets SET is_selected = 1 WHERE post_id = ? AND file_path = ?",
            (post_id, file_path),
        )
        cursor = connection.execute("UPDATE posts SET image_path = ? WHERE id = ?", (file_path, post_id))
        if cursor.rowcount == 0:
            raise StorageError(f"Post {post_id} non trovato.")
