from datetime import datetime, time, timezone

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from .activity_utils import normalize_activity_date, normalize_developer_id
from .config import get_settings
from .database import db


settings = get_settings()


def _slack_client() -> AsyncWebClient:
    if not settings.slack_bot_token:
        raise RuntimeError("SLACK_BOT_TOKEN is not configured. Add it to your .env file.")
    return AsyncWebClient(token=settings.slack_bot_token)


def _configured_channels() -> list[str]:
    return [
        channel.strip()
        for channel in settings.slack_channel_ids.split(",")
        if channel.strip()
    ]


def _to_slack_ts(date_text: str, end_of_day: bool = False) -> str:
    date_value = datetime.fromisoformat(normalize_activity_date(date_text)).date()
    day_time = time.max if end_of_day else time.min
    return str(datetime.combine(date_value, day_time, tzinfo=timezone.utc).timestamp())


async def _resolve_developer_id(slack_user_id: str, cache: dict[str, str]) -> str:
    if slack_user_id in cache:
        return cache[slack_user_id]

    developer = await db.developers.find_one(
        {"$or": [{"slack_user_id": slack_user_id}, {"slack_id": slack_user_id}]}
    )
    developer_id = (
        normalize_developer_id(developer.get("developer_id"))
        if developer
        else normalize_developer_id(slack_user_id)
    )
    cache[slack_user_id] = developer_id
    return developer_id


async def fetch_slack_messages(
    channel_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    project: str = "slack",
) -> dict:
    """Fetch Slack channel messages and upsert them into activity_logs."""
    channels = channel_ids or _configured_channels()
    if not channels:
        raise RuntimeError("No Slack channels provided. Pass channel_ids or set SLACK_CHANNEL_IDS.")
    if not start_date:
        raise RuntimeError("start_date is required for Slack ingestion.")

    latest_date = end_date or start_date
    oldest = _to_slack_ts(start_date)
    latest = _to_slack_ts(latest_date, end_of_day=True)

    client = _slack_client()
    developer_cache: dict[str, str] = {}
    total_fetched = 0
    total_saved = 0

    for channel_id in channels:
        cursor = None
        while True:
            try:
                response = await client.conversations_history(
                    channel=channel_id,
                    oldest=oldest,
                    latest=latest,
                    limit=200,
                    inclusive=True,
                    cursor=cursor,
                )
            except SlackApiError as exc:
                error = exc.response.get("error", "Slack API request failed.")
                raise RuntimeError(error) from exc

            messages = response.get("messages", [])
            total_fetched += len(messages)

            for message in messages:
                user = message.get("user") or message.get("bot_id") or "UNKNOWN"
                timestamp = message.get("ts")
                if not timestamp:
                    continue

                developer_id = await _resolve_developer_id(user, developer_cache)
                message_date = normalize_activity_date(
                    datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
                )

                result = await db.activity_logs.update_one(
                    {
                        "source": "slack",
                        "activity_type": "message",
                        "channel_id": channel_id,
                        "message_ts": timestamp,
                    },
                    {
                        "$set": {
                            "developer_id": developer_id,
                            "source": "slack",
                            "activity_type": "message",
                            "timestamp": timestamp,
                            "date": message_date,
                            "project": project,
                            "slack_user_id": user,
                            "channel_id": channel_id,
                            "message_ts": timestamp,
                            "text": message.get("text", ""),
                            "thread_ts": message.get("thread_ts"),
                            "message_type": message.get("type", "message"),
                        }
                    },
                    upsert=True,
                )
                if result.upserted_id or result.modified_count:
                    total_saved += 1

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

    return {
        "source": "slack",
        "fetched": total_fetched,
        "saved": total_saved,
        "channels": channels,
        "start_date": normalize_activity_date(start_date),
        "end_date": normalize_activity_date(latest_date),
    }
