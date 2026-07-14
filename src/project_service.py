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


class ProjectAccessError(Exception):
    """Raised when a user requests a repo_id that isn't one of their own registered projects."""


async def resolve_scoped_repo_id(user_id: str, repo_id: str | None = None) -> str | None:
    """
    Return the repo_id a request should actually be scoped to for this user.

    - If repo_id is explicitly passed, verify the user owns it. Raise
      ProjectAccessError if it belongs to someone else (or doesn't exist),
      so we never silently serve another user's data.
    - If no repo_id is passed, use the user's active project.
    - If the user has no active project and passed no repo_id, return None
      (caller should return empty results, NOT fall back to a global default).
    """
    if repo_id:
        owned = await db["projects"].find_one({"repo_id": repo_id, "user_id": user_id})
        if not owned:
            raise ProjectAccessError(f"repo_id '{repo_id}' is not registered to this user")
        return repo_id

    active_project = await get_active_project(user_id)
    return active_project["repo_id"] if active_project else None


async def touch_last_synced(user_id: str, repo_id: str) -> None:
    """Called after a successful fetch to record when this repo was last synced."""
    await db["projects"].update_one(
        {"repo_id": repo_id, "user_id": user_id},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}},
    )