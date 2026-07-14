from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .activity_utils import normalize_activity_date, normalize_developer_id, DEFAULT_REPO_ID
from .config import get_settings
from .database import db


settings = get_settings()


def _jira_auth() -> tuple[str, str]:
    if not settings.jira_email or not settings.jira_api_token:
        raise RuntimeError("JIRA_EMAIL and JIRA_API_TOKEN must be configured in .env.")
    return settings.jira_email, settings.jira_api_token


def _jira_base_url() -> str:
    if not settings.jira_base_url:
        raise RuntimeError("JIRA_BASE_URL must be configured in .env.")
    return settings.jira_base_url.rstrip("/")


def _updated_jql(start_date: str, end_date: str | None, project_key: str | None) -> str:
    start = normalize_activity_date(start_date)
    end = normalize_activity_date(end_date or start_date)
    next_day = (datetime.fromisoformat(end).replace(tzinfo=timezone.utc) + timedelta(days=1)).date().isoformat()
    clauses = [f'updated >= "{start}"', f'updated < "{next_day}"']
    if project_key:
        clauses.insert(0, f'project = "{project_key}"')
    return " AND ".join(clauses) + " ORDER BY updated ASC"


async def _resolve_developer_id(account_id: str, display_name: str | None) -> str:
    developer = await db.developers.find_one(
        {"$or": [{"jira_account_id": account_id}, {"jira_display_name": display_name}]}
    )
    if developer:
        return normalize_developer_id(developer.get("developer_id"))
    return normalize_developer_id(display_name or account_id)


def _issue_updated_at(issue: dict[str, Any]) -> str:
    fields = issue.get("fields", {})
    return fields.get("updated") or fields.get("created")


async def fetch_jira_updates(
    start_date: str,
    end_date: str | None = None,
    project_key: str | None = None,
    max_results: int = 100,
    repo_id: str = DEFAULT_REPO_ID,   # NEW
) -> dict:
    """Fetch Jira issue updates and upsert them into activity_logs."""
    project = project_key or settings.jira_project_key
    jql = _updated_jql(start_date, end_date, project)
    base_url = _jira_base_url()

    total_fetched = 0
    total_saved = 0
    next_page_token = None

    async with httpx.AsyncClient(auth=_jira_auth(), timeout=30) as http_client:
        while True:
            params = {
                "jql": jql, "maxResults": max_results,
                "fields": "summary,status,assignee,updated,created,project",
            }
            if next_page_token:
                params["nextPageToken"] = next_page_token

            response = await http_client.get(
                f"{base_url}/rest/api/3/search/jql", params=params,
                headers={"Accept": "application/json"},
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Jira API returned {response.status_code}: {response.text}")

            payload = response.json()
            issues = payload.get("issues", [])
            total_fetched += len(issues)

            for issue in issues:
                fields = issue.get("fields", {})
                assignee = fields.get("assignee") or {}
                account_id = assignee.get("accountId") or "UNKNOWN"
                display_name = assignee.get("displayName")
                updated_at = _issue_updated_at(issue)
                if not updated_at:
                    continue

                developer_id = await _resolve_developer_id(account_id, display_name)
                issue_key = issue.get("key")
                issue_project = (fields.get("project") or {}).get("key") or project or "jira"

                result = await db.activity_logs.update_one(
                    {
                        "repo_id": repo_id,
                        "source": "jira",
                        "activity_type": "issue_update",
                        "issue_key": issue_key,
                        "timestamp": updated_at,
                    },
                    {
                        "$set": {
                            "repo_id": repo_id,
                            "developer_id": developer_id,
                            "source": "jira",
                            "activity_type": "issue_update",
                            "timestamp": updated_at,
                            "date": normalize_activity_date(updated_at),
                            "project": issue_project,
                            "issue_key": issue_key,
                            "summary": fields.get("summary"),
                            "status": (fields.get("status") or {}).get("name"),
                            "jira_account_id": account_id,
                            "jira_display_name": display_name,
                            "changelog_count": 0,
                        }
                    },
                    upsert=True,
                )
                if result.upserted_id or result.modified_count:
                    total_saved += 1

            next_page_token = payload.get("nextPageToken")
            is_last = payload.get("isLast", not next_page_token)
            if is_last or not issues:
                break

    return {
        "source": "jira", "fetched": total_fetched, "saved": total_saved,
        "project_key": project, "repo_id": repo_id,
        "start_date": normalize_activity_date(start_date),
        "end_date": normalize_activity_date(end_date or start_date),
    }