from collections import Counter, defaultdict
from typing import Any

from .activity_utils import normalize_activity_date, normalize_developer_id, normalize_repo_id, resolve_developer_id
from .alias_service import load_developer_aliases
from .config import get_settings
from .database import db


ACTIVITY_SOURCES = ("github", "slack", "jira")



_settings = get_settings()
DEFAULT_REPO_ID = normalize_repo_id(_settings.github_owner, _settings.github_repo)


def _activity_sample(activity: dict[str, Any]) -> dict[str, Any]:
    return {
        "activity_type": activity.get("activity_type"),
        "timestamp": activity.get("timestamp"),
        "project": activity.get("project"),
        "message": activity.get("message") or activity.get("text") or activity.get("summary"),
        "external_id": (
            activity.get("commit_id")
            or activity.get("message_ts")
            or activity.get("issue_key")
        ),
    }


def _footprint_from_activities(developer_id: str, date: str, activities: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure function — builds a footprint from an already-fetched list of activities. No DB call."""
    counts = Counter(activity.get("source", "unknown") for activity in activities)
    samples = {
        source: [
            _activity_sample(activity)
            for activity in activities
            if activity.get("source") == source
        ][:5]
        for source in ACTIVITY_SOURCES
    }

    return {
        "developer_id": developer_id,
        "date": date,
        "github_count": counts.get("github", 0),
        "slack_count": counts.get("slack", 0),
        "jira_count": counts.get("jira", 0),
        "total_activity_count": sum(counts.get(source, 0) for source in ACTIVITY_SOURCES),
        "samples": samples,
    }


async def build_developer_footprint(developer_id: str, date: str, repo_id: str = DEFAULT_REPO_ID, user_id: str | None = None) -> dict[str, Any]:
    normalized_developer_id = normalize_developer_id(developer_id)
    normalized_date = normalize_activity_date(date)

    query: dict[str, Any] = {"repo_id": repo_id, "developer_id": normalized_developer_id, "date": normalized_date}
    if user_id:
        query["user_id"] = user_id

    activities = await db.activity_logs.find(query).to_list(500)

    return _footprint_from_activities(normalized_developer_id, normalized_date, activities)



async def build_all_footprints(limit: int = 5000, repo_id: str = DEFAULT_REPO_ID, user_id: str | None = None) -> list[dict[str, Any]]:
    aliases = await load_developer_aliases(repo_id)   # NEW — one query, not per-activity
    query: dict[str, Any] = {"repo_id": repo_id, "source": {"$in": list(ACTIVITY_SOURCES)}}
    if user_id:
        query["user_id"] = user_id
    activities = await db.activity_logs.find(query).to_list(limit)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for activity in activities:
        developer_id = resolve_developer_id(activity.get("developer_id"), aliases)  # CHANGED
        date = normalize_activity_date(activity.get("date") or activity.get("timestamp"))
        if date == "UNKNOWN":
            continue
        grouped[(developer_id, date)].append(activity)

    return [
        _footprint_from_activities(developer_id, date, activities_for_day)
        for (developer_id, date), activities_for_day in sorted(grouped.items())
    ]