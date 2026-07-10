from datetime import datetime, timezone
from typing import Any


def normalize_developer_id(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    normalized = str(value).strip().upper()
    return normalized or "UNKNOWN"


DEVELOPER_ALIASES = {
    "YUVRAJ": "YUVRAJ SADANA",
    "YUVRAJ SADANA": "YUVRAJ SADANA",
}


def resolve_developer_id(value: Any) -> str:
    normalized = normalize_developer_id(value)
    return DEVELOPER_ALIASES.get(normalized, normalized)


def normalize_activity_date(value: Any) -> str:
    if value is None:
        return "UNKNOWN"

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date().isoformat()

    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "unknown"}:
        return "UNKNOWN"

    if "T" in text:
        text = text.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text).date().isoformat()
        except ValueError:
            return text[:10]

    if len(text) >= 10:
        return text[:10]

    return text