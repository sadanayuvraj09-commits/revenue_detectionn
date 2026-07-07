from datetime import datetime, timezone

from src.activity_utils import normalize_activity_date, normalize_developer_id


def test_normalize_developer_id_uppercases():
    assert normalize_developer_id("dev002") == "DEV002"


def test_normalize_developer_id_strips_whitespace():
    assert normalize_developer_id("  dev003  ") == "DEV003"


def test_normalize_developer_id_none_returns_unknown():
    assert normalize_developer_id(None) == "UNKNOWN"


def test_normalize_developer_id_empty_string_returns_unknown():
    assert normalize_developer_id("   ") == "UNKNOWN"


def test_normalize_activity_date_none_returns_unknown():
    assert normalize_activity_date(None) == "UNKNOWN"


def test_normalize_activity_date_unknown_string_returns_unknown():
    assert normalize_activity_date("unknown") == "UNKNOWN"


def test_normalize_activity_date_iso_string_with_time():
    assert normalize_activity_date("2026-06-23T10:00:00Z") == "2026-06-23"


def test_normalize_activity_date_plain_date_string():
    assert normalize_activity_date("2026-06-23") == "2026-06-23"


def test_normalize_activity_date_datetime_object():
    dt = datetime(2026, 6, 23, 10, 0, 0, tzinfo=timezone.utc)
    assert normalize_activity_date(dt) == "2026-06-23"