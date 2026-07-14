"""
Timesheet stub generator — Step 5.

Whenever new activity lands in activity_logs for a developer/date that
doesn't already have a timesheet_entries row, create a stub (0 hours,
status "unfilled"). This guarantees every timesheet row traces back to
real tracked activity — no more free-typed developer_id values that
never touched the repo.
"""

from .activity_utils import normalize_activity_date, resolve_developer_id
from .alias_service import load_developer_aliases
from .database import db


async def generate_timesheet_stubs(repo_id: str) -> dict:
    """Ensure every (developer_id, date) pair present in activity_logs
    for this repo has a corresponding timesheet_entries row."""
    aliases = await load_developer_aliases(repo_id)

    activity_pairs = await db["activity_logs"].distinct(
        "developer_id", {"repo_id": repo_id}
    )
    # distinct() only gives developer_ids, not (developer_id, date) pairs —
    # so pull the actual pairs directly instead.
    cursor = db["activity_logs"].find(
        {"repo_id": repo_id},
        {"developer_id": 1, "date": 1},
    )
    seen_pairs: set[tuple[str, str]] = set()
    async for doc in cursor:
        developer_id = resolve_developer_id(doc.get("developer_id"), aliases)
        date = normalize_activity_date(doc.get("date"))
        if date == "UNKNOWN":
            continue
        seen_pairs.add((developer_id, date))

    created = 0
    for developer_id, date in seen_pairs:
        result = await db["timesheet_entries"].update_one(
            {"repo_id": repo_id, "developer_id": developer_id, "date": date},
            {
                "$setOnInsert": {
                    "repo_id": repo_id,
                    "developer_id": developer_id,
                    "date": date,
                    "hours_logged": 0,
                    "status": "unfilled",
                    "project": None,
                    "notes": None,
                }
            },
            upsert=True,
        )
        if result.upserted_id:
            created += 1

    return {"repo_id": repo_id, "checked_pairs": len(seen_pairs), "stubs_created": created}