import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    mongo_uri: str | None = os.getenv("MONGO_URI")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "unbilled_detective")

    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_owner: str | None = os.getenv("GITHUB_OWNER")
    github_repo: str | None = os.getenv("GITHUB_REPO")

    slack_bot_token: str | None = os.getenv("SLACK_BOT_TOKEN")
    slack_channel_ids: str = os.getenv("SLACK_CHANNEL_IDS", "")

    jira_base_url: str | None = os.getenv("JIRA_BASE_URL")
    jira_email: str | None = os.getenv("JIRA_EMAIL")
    jira_api_token: str | None = os.getenv("JIRA_API_TOKEN")
    jira_project_key: str | None = os.getenv("JIRA_PROJECT_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
