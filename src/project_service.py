"""
Project registry service — Step 2.

Replaces the single fixed GITHUB_OWNER/GITHUB_REPO env-var pair with a
MongoDB-backed registry of repos ("projects"), one of which is marked
active at a time. This lets the app target a different repo without
restarting or editing .env.
"""

from datetime import datetime, timezone
from typing import Any

from .activity_utils import normalize_repo_id
from .database import db
from .activity_utils import normalize_repo_id

async def register_project(
    owner: str,
    repo: str,
    github_token_override: str | None = None,
    make_active: bool = True,
) -> dict[str, Any]:
    """Create (or update) a project record for a given owner/repo."""
    repo_id = normalize_repo_id(owner, repo)

    doc = {
        "repo_id": repo_id,
        "owner": owner,
        "repo": repo,
        "github_token_override": github_token_override,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db["projects"].update_one(
        {"repo_id": repo_id},
        {
            "$set": doc,
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat(), "last_synced_at": None},
        },
        upsert=True,
    )

    if make_active:
        await set_active_project(repo_id)

    return await db["projects"].find_one({"repo_id": repo_id}, {"_id": 0})


async def set_active_project(repo_id: str) -> bool:
    """Mark exactly one project as active; unset all others."""
    existing = await db["projects"].find_one({"repo_id": repo_id})
    if not existing:
        return False

    await db["projects"].update_many({}, {"$set": {"is_active": False}})
    await db["projects"].update_one({"repo_id": repo_id}, {"$set": {"is_active": True}})
    return True


async def get_active_project() -> dict[str, Any] | None:
    """Return the currently active project doc, or None if none is set."""
    return await db["projects"].find_one({"is_active": True}, {"_id": 0})


async def list_projects() -> list[dict[str, Any]]:
    projects = await db["projects"].find({}, {"_id": 0}).to_list(200)
    return projects


async def touch_last_synced(repo_id: str) -> None:
    """Called after a successful fetch to record when this repo was last synced."""
    await db["projects"].update_one(
        {"repo_id": repo_id},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}},
    )