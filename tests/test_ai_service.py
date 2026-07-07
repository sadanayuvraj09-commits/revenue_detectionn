from unittest.mock import patch

from src.ai_service import (
    generate_ai_summary,
    generate_gap_priority,
    suggest_timesheet_entry,
)


def test_generate_ai_summary_uses_gemini_response():
    gap = {"developer_id": "DEV002", "date": "2026-07-01", "github_count": 3}
    with patch("src.ai_service._call_gemini", return_value="Developer made 3 commits but logged no hours."):
        result = generate_ai_summary(gap)
        assert result == "Developer made 3 commits but logged no hours."


def test_generate_ai_summary_falls_back_when_gemini_unavailable():
    gap = {"developer_id": "DEV002", "date": "2026-07-01", "github_count": 3}
    with patch("src.ai_service._call_gemini", return_value=None):
        result = generate_ai_summary(gap)
        assert isinstance(result, str)
        assert len(result) > 0


def test_generate_gap_priority_uses_gemini_response():
    gap = {"developer_id": "DEV002", "github_count": 0, "slack_count": 0, "jira_count": 0}
    with patch("src.ai_service._call_gemini", return_value="High priority: no activity recorded."):
        result = generate_gap_priority(gap)
        assert result == "High priority: no activity recorded."


def test_generate_gap_priority_falls_back_when_gemini_unavailable():
    gap = {"developer_id": "DEV002", "github_count": 0, "slack_count": 0, "jira_count": 0}
    with patch("src.ai_service._call_gemini", return_value=None):
        result = generate_gap_priority(gap)
        assert isinstance(result, str)
        assert len(result) > 0


def test_suggest_timesheet_entry_returns_dict_with_expected_keys():
    activity = {"developer_id": "DEV002", "date": "2026-07-01", "github_count": 2}
    with patch("src.ai_service._call_gemini", return_value='{"hours": 4, "project": "Backend", "note": "Worked on API"}'):
        result = suggest_timesheet_entry(activity)
        assert "hours" in result
        assert "project" in result
        assert "note" in result