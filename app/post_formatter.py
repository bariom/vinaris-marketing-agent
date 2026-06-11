from __future__ import annotations

from app.storage import PostRecord


def build_ready_caption(post: PostRecord) -> str:
    sections = [post.text_short.strip(), post.text_medium.strip(), post.cta.strip(), post.hashtags.strip()]
    return "\n\n".join(section for section in sections if section)
