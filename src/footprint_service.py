from collections import Counter
from typing import Any

from .activity_utils import normalize_activity_date, normalize_developer_id
from .database import db


ACTIVITY_SOURCES = ("github", "slack", "jira")


async def build_developer_footprint(developer_id: str, date: str) -> dict[str, Any]:
    normalized_developer_id = normalize_developer_id(developer_id)
    normalized_date = normalize_activity_date(date)

    activities = await db.activity_logs.find(
        {"developer_id": normalized_developer_id, "date": normalized_date}
    ).to_list(500)

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
        "developer_id": normalized_developer_id,
        "date": normalized_date,
        "github_count": counts.get("github", 0),
        "slack_count": counts.get("slack", 0),
        "jira_count": counts.get("jira", 0),
        "total_activity_count": sum(counts.get(source, 0) for source in ACTIVITY_SOURCES),
        "samples": samples,
    }


async def build_all_footprints(limit: int = 5000) -> list[dict[str, Any]]:
    activities = await db.activity_logs.find(
        {"source": {"$in": list(ACTIVITY_SOURCES)}},
        {"developer_id": 1, "date": 1, "timestamp": 1},
    ).to_list(limit)

    dev_days = {
        (
            normalize_developer_id(activity.get("developer_id")),
            normalize_activity_date(activity.get("date") or activity.get("timestamp")),
        )
        for activity in activities
    }

    return [
        await build_developer_footprint(developer_id, date)
        for developer_id, date in sorted(dev_days)
        if date != "UNKNOWN"
    ]


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
