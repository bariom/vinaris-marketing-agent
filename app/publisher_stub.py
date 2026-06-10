from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PublishResult:
    post_id: int
    platform: str
    published_at: datetime
    message: str


def simulate_publish(post_id: int, platform: str) -> PublishResult:
    published_at = datetime.now()
    return PublishResult(
        post_id=post_id,
        platform=platform,
        published_at=published_at,
        message=(
            f"Simulazione pubblicazione completata per il post {post_id} "
            f"su {platform} alle {published_at.isoformat(timespec='seconds')}."
        ),
    )
