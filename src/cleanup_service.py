"""
Repo data lifecycle management — Step 8.

Since a repo's data spans 7 collections (activity_logs, developers,
timesheet_entries, detected_gaps, detected_gaps_snapshot, alerts,
developer_aliases) tied together only by repo_id, MongoDB's per-document
TTL indexes can't cascade-delete across them. This module does that
cascade explicitly, either on manual request or via a scheduled sweep
of repos that have gone stale.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from .database import db

SCOPED_COLLECTIONS = [
    "activity_logs",
    "developers",
    "timesheet_entries",
    "detected_gaps",
    "detected_gaps_snapshot",
    "alerts",
    "developer_aliases",
]


async def purge_project_data(repo_id: str, user_id: str | None = None, delete_project_record: bool = True) -> dict[str, Any]:
    """Cascade-delete every document scoped to this repo_id (and, when
    provided, this user_id — so deleting your project never touches
    another user's data on that same repo), across all collections,
    plus the project record itself (unless keeping it as an empty
    placeholder is desired)."""
    deleted_counts: dict[str, int] = {}

    query: dict[str, Any] = {"repo_id": repo_id}
    if user_id:
        query["user_id"] = user_id

    for collection_name in SCOPED_COLLECTIONS:
        result = await db[collection_name].delete_many(query)
        deleted_counts[collection_name] = result.deleted_count

    if delete_project_record:
        project_query: dict[str, Any] = {"repo_id": repo_id}
        if user_id:
            project_query["user_id"] = user_id
        await db["projects"].delete_one(project_query)

    return {"repo_id": repo_id, "deleted": deleted_counts}


async def cleanup_stale_projects(stale_after_days: int = 30) -> dict[str, Any]:
    """Find projects that haven't synced in `stale_after_days` (or were
    registered but never synced at all) and purge their data. Intended
    to run on a schedule, e.g. daily."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=stale_after_days)).isoformat()

    stale_projects = await db["projects"].find(
        {
            "$or": [
                {"last_synced_at": {"$lt": cutoff}},
                {"last_synced_at": None},
                {"last_synced_at": {"$exists": False}},
            ]
        }
    ).to_list(500)

    purged = []
    for project in stale_projects:
        repo_id = project.get("repo_id")
        if not repo_id:
            continue
        result = await purge_project_data(repo_id, user_id=project.get("user_id"))
        purged.append(result)

    return {"stale_after_days": stale_after_days, "projects_purged": len(purged), "details": purged}