import httpx
from pymongo import UpdateOne

from .activity_utils import normalize_activity_date, normalize_repo_id, resolve_developer_id
from .alias_service import load_developer_aliases
from .config import get_settings
from .database import db


settings = get_settings()


def _github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def fetch_commits(repo_owner: str, repo_name: str, user_id: str) -> dict:
    repo_id = normalize_repo_id(repo_owner, repo_name)
    aliases = await load_developer_aliases(repo_id)
    count = 0
    total_fetched = 0
    page = 1
    developer_contacts: dict[str, dict] = {}   # NEW — collects email/name per developer_id this run

    async with httpx.AsyncClient() as http_client:
        while True:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
            response = await http_client.get(
                url, headers=_github_headers(),
                params={"per_page": 100, "page": page}, timeout=30,
            )

            if response.status_code != 200:
                return {
                    "saved": count, "fetched": total_fetched,
                    "error": f"GitHub API returned {response.status_code}",
                    "details": response.text,
                }

            commits = response.json()
            if not commits:
                break

            total_fetched += len(commits)
            operations = []

            for commit in commits:
                commit_data = commit.get("commit", {})
                author_data = commit_data.get("author", {})
                developer_name = author_data.get("name", "Unknown")
                developer_email = author_data.get("email")
                timestamp = author_data.get("date", None)
                commit_id = commit.get("sha")

                if not commit_id:
                    continue

                developer_id = resolve_developer_id(developer_name, aliases)

                # NEW — track contact info per developer for the batch upsert below
                if developer_email:
                    developer_contacts[developer_id] = {
                        "email": developer_email,
                        "name": developer_name,
                    }

                operations.append(
                    UpdateOne(
                        {"repo_id": repo_id, "user_id": user_id, "source": "github", "activity_type": "commit", "commit_id": commit_id},
                        {
                            "$set": {
                                "repo_id": repo_id,
                                "user_id": user_id,
                                "developer_id": developer_id,
                                "developer_name": developer_name,
                                "developer_email": developer_email,
                                "source": "github",
                                "activity_type": "commit",
                                "commit_id": commit_id,
                                "message": commit_data.get("message"),
                                "author": developer_name,
                                "timestamp": timestamp,
                                "date": normalize_activity_date(timestamp),
                                "project": repo_name,
                                "repo_owner": repo_owner,
                            }
                        },
                        upsert=True,
                    )
                )

                if len(operations) >= 100:
                    result = await db.activity_logs.bulk_write(operations, ordered=False)
                    count += (result.upserted_count or 0) + (result.modified_count or 0)
                    operations.clear()

            if operations:
                result = await db.activity_logs.bulk_write(operations, ordered=False)
                count += (result.upserted_count or 0) + (result.modified_count or 0)

            if len(commits) < 100:
                break
            page += 1

    # NEW — auto-populate developers.email from what we just saw, without
    # overwriting any manually-curated fields (role, team, etc.) that already exist.
    if developer_contacts:
        contact_ops = [
            UpdateOne(
                {"repo_id": repo_id, "user_id": user_id, "developer_id": dev_id},
                {
                    "$set": {"repo_id": repo_id, "user_id": user_id, "developer_id": dev_id, "email": info["email"], "name": info["name"]},
                    "$setOnInsert": {"source": "github_auto"},
                },
                upsert=True,
            )
            for dev_id, info in developer_contacts.items()
        ]
        await db["developers"].bulk_write(contact_ops, ordered=False)

    return {"saved": count, "fetched": total_fetched, "repo": f"{repo_owner}/{repo_name}", "repo_id": repo_id}