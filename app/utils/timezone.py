from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PKT = ZoneInfo("Asia/Karachi")


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def format_pkt_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return ensure_utc(value).astimezone(PKT).strftime("%b %d, %Y %I:%M %p")
