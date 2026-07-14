from datetime import datetime, timezone
from typing import Any


def normalize_developer_id(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    normalized = str(value).strip().upper()
    return normalized or "UNKNOWN"


def resolve_developer_id(value: Any, aliases: dict[str, str] | None = None) -> str:
    """Normalize, then apply a repo-scoped alias map if one is provided.
    `aliases` should come from alias_service.load_developer_aliases(repo_id),
    loaded once per operation — not per row — to avoid N+1 queries."""
    normalized = normalize_developer_id(value)
    if aliases:
        return aliases.get(normalized, normalized)
    return normalized


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

DEFAULT_REPO_ID = "UNSCOPED"

def normalize_repo_id(owner, repo=None) -> str:
    """
    Canonical repo_id used to scope every collection.
    normalize_repo_id("MyOrg", "MyRepo") -> "myorg/myrepo"
    normalize_repo_id("MyOrg/MyRepo")    -> "myorg/myrepo"
    """
    if owner is None:
        return DEFAULT_REPO_ID
    combined = str(owner).strip() if repo is None else f"{str(owner).strip()}/{str(repo).strip()}"
    combined = combined.strip("/").lower()
    return combined or DEFAULT_REPO_ID
