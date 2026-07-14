"""
Repo-scoped alias registry — Step 4.

Replaces the hardcoded global DEVELOPER_ALIASES dict with a MongoDB
collection keyed by repo_id, so each connected repo has its own
alias map instead of sharing one hardcoded, person-specific dict.
"""

from .database import db
from .activity_utils import normalize_developer_id


async def load_developer_aliases(repo_id: str) -> dict[str, str]:
    """Load this repo's full alias map in ONE query (avoids N+1 lookups,
    matching the pattern already used in footprint_service.build_all_footprints)."""
    docs = await db["developer_aliases"].find({"repo_id": repo_id}).to_list(1000)
    return {doc["alias_id"]: doc["canonical_id"] for doc in docs}


async def add_developer_alias(repo_id: str, alias_id: str, canonical_id: str) -> None:
    alias_id = normalize_developer_id(alias_id)
    canonical_id = normalize_developer_id(canonical_id)
    await db["developer_aliases"].update_one(
        {"repo_id": repo_id, "alias_id": alias_id},
        {"$set": {"repo_id": repo_id, "alias_id": alias_id, "canonical_id": canonical_id}},
        upsert=True,
    )


async def list_developer_aliases(repo_id: str) -> list[dict]:
    return await db["developer_aliases"].find({"repo_id": repo_id}, {"_id": 0}).to_list(1000)