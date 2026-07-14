"""
One-time fix: drop the stale `developer_id_1_date_1` unique index on
detected_gaps. That index predates per-project (repo_id) scoping, so it
still enforces "one gap per developer+date across the whole database" —
which now collides as soon as more than one project/user hits the same
developer_id + date. The correct index (repo_id, developer_id, date) is
created automatically by main.py on startup; this script just clears the
old one out of the way.

Run once with:
    python scripts/drop_legacy_gap_index.py
"""
import asyncio

import bootstrap
from src.database import db


async def main():
    existing = await db["detected_gaps"].index_information()
    print("Current indexes on detected_gaps:")
    for name, info in existing.items():
        print(f"  {name}: {info.get('key')}")

    legacy_name = "developer_id_1_date_1"
    if legacy_name in existing:
        await db["detected_gaps"].drop_index(legacy_name)
        print(f"\nDropped legacy index: {legacy_name}")
    else:
        print(f"\nNo legacy index named '{legacy_name}' found — nothing to drop.")

    print("\nIndexes after cleanup:")
    for name, info in (await db["detected_gaps"].index_information()).items():
        print(f"  {name}: {info.get('key')}")


if __name__ == "__main__":
    asyncio.run(main())