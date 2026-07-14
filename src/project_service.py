"""
Project registry service — now scoped per user_id.

Each user has their own set of registered projects and their own
"active project" pointer, so two different people can register the
same GitHub repo without ever seeing each other's data.
"""

from datetime import datetime, timezone
from typing import Any

from .activity_utils import normalize_repo_id
from .database import db


async def register_project(
    user_id: str,
    owner: str,
    repo: str,
    github_token_override: str | None = None,
    make_active: bool = True,
) -> dict[str, Any]:
    """Create (or update) a project record for a given owner/repo, scoped to user_id."""
    repo_id = normalize_repo_id(owner, repo)

    doc = {
        "repo_id": repo_id,
        "user_id": user_id,
        "owner": owner,
        "repo": repo,
        "github_token_override": github_token_override,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db["projects"].update_one(
        {"repo_id": repo_id, "user_id": user_id},
        {
            "$set": doc,
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat(), "last_synced_at": None},
        },
        upsert=True,
    )

    if make_active:
        await set_active_project(user_id, repo_id)

    return await db["projects"].find_one({"repo_id": repo_id, "user_id": user_id}, {"_id": 0})


async def set_active_project(user_id: str, repo_id: str) -> bool:
    """Mark exactly one project as active for this user; unset all their others."""
    existing = await db["projects"].find_one({"repo_id": repo_id, "user_id": user_id})
    if not existing:
        return False

    await db["projects"].update_many({"user_id": user_id}, {"$set": {"is_active": False}})
    await db["projects"].update_one({"repo_id": repo_id, "user_id": user_id}, {"$set": {"is_active": True}})
    return True


async def get_active_project(user_id: str) -> dict[str, Any] | None:
    """Return this user's currently active project doc, or None if none is set."""
    return await db["projects"].find_one({"is_active": True, "user_id": user_id}, {"_id": 0})


async def list_projects(user_id: str) -> list[dict[str, Any]]:
    projects = await db["projects"].find({"user_id": user_id}, {"_id": 0}).to_list(200)
    return projects


async def touch_last_synced(user_id: str, repo_id: str) -> None:
    """Called after a successful fetch to record when this repo was last synced."""
    await db["projects"].update_one(
        {"repo_id": repo_id, "user_id": user_id},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}},
    )