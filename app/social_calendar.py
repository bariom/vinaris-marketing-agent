from __future__ import annotations

from datetime import datetime, timedelta


def suggest_scheduled_date(index: int, start_at: datetime | None = None) -> datetime:
    base = start_at or datetime.now()
    slot_days = index // 2
    hour = 9 if index % 2 == 0 else 18
    return (base + timedelta(days=slot_days)).replace(hour=hour, minute=0, second=0, microsecond=0)
