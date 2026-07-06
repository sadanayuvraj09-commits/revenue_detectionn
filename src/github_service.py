import httpx

from .activity_utils import normalize_activity_date, normalize_developer_id
from .config import get_settings
from .database import db


settings = get_settings()


def _github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def fetch_commits(repo_owner: str, repo_name: str) -> dict:
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url, headers=_github_headers(), timeout=30)

        if response.status_code != 200:
            return {
                "saved": 0,
                "error": f"GitHub API returned {response.status_code}",
                "details": response.text,
            }

        commits = response.json()
        count = 0

        for commit in commits:
            commit_data = commit.get("commit", {})
            author_data = commit_data.get("author", {})
            developer_name = author_data.get("name", "Unknown")
            timestamp = author_data.get("date", None)
            commit_id = commit.get("sha")

            if not commit_id:
                continue

            result = await db.activity_logs.update_one(
                {"source": "github", "activity_type": "commit", "commit_id": commit_id},
                {
                    "$set": {
                        "developer_id": normalize_developer_id(developer_name),
                        "developer_name": developer_name,
                        "source": "github",
                        "activity_type": "commit",
                        "commit_id": commit_id,
                        "message": commit_data.get("message"),
                        "author": author_data.get("name", "Unknown"),
                        "timestamp": timestamp,
                        "date": normalize_activity_date(timestamp),
                        "project": repo_name,
                        "repo_owner": repo_owner,
                    }
                },
                upsert=True,
            )
            if result.upserted_id or result.modified_count:
                count += 1

        return {"saved": count, "fetched": len(commits), "repo": f"{repo_owner}/{repo_name}"}
