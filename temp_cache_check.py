import asyncio
from unittest.mock import AsyncMock, patch
from src.main import run_gap_detection
from tests.test_phase3 import FakeDb

async def main():
    fake_db = FakeDb(timesheets=[{'developer_id': 'JOHN DOE', 'date': '2026-07-01', 'hours_logged': 0}])
    footprints = [{'developer_id': 'JOHN DOE', 'date': '2026-07-01', 'github_count': 1, 'slack_count': 0, 'jira_count': 0, 'total_activity_count': 1}]
    with patch('src.main.db', fake_db), patch('src.main.build_all_footprints', new=AsyncMock(return_value=footprints)) as build_mock:
        first = await run_gap_detection(10)
        second = await run_gap_detection(10)
        print(first['new_gaps_saved'], second['new_gaps_saved'], build_mock.await_count)
        import src.main as main_module
        print(main_module._gap_detection_cache)
        print(main_module._gap_detection_cache_timestamp)

asyncio.run(main())
