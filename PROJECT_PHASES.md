# Unbilled Revenue Detective Phase Map

This file documents which project phase each source, script, and test file serves.
It is intentionally a documentation tag map, not a file move, so existing imports
and commands keep working.

## Phase Tags

- P1: Data Collection
- P2: Digital Footprint Building
- P3: Timesheet Comparison
- P4: AI Analysis and Alerts
- SUPPORT: Configuration, database, utilities, local scripts, and manual tests

## Source Files

| File | Tags | Purpose |
| --- | --- | --- |
| `src/main.py` | P1, P2, P3, P4 | FastAPI route layer for ingestion, gap detection, summary generation, and verification. |
| `src/github_service.py` | P1 | Fetches GitHub commits and stores them in `activity_logs`. |
| `src/slack_service.py` | P1 | Fetches Slack messages and stores them in `activity_logs`. |
| `src/jira_service.py` | P1 | Fetches Jira issue activity and stores it in `activity_logs`. |
| `src/footprint_service.py` | P2 | Aggregates GitHub, Slack, and Jira activity into a developer/day footprint. |
| `src/ai_service.py` | P4 | Generates natural language summaries with Gemini. |
| `src/activity_utils.py` | SUPPORT | Shared date and developer normalization helpers. |
| `src/config.py` | SUPPORT | Environment variable configuration. |
| `src/database.py` | SUPPORT | Shared MongoDB client and database handle. |
| `src/__init__.py` | SUPPORT | Marks `src` as an importable package. |

## Scripts

| File | Tags | Purpose |
| --- | --- | --- |
| `scripts/insert_developers.py` | SUPPORT, P3 | Seeds developer records used for matching activity to timesheets. |
| `scripts/check_gaps.py` | SUPPORT, P3, P4 | Inspects persisted detected gaps. |
| `scripts/reset_gaps.py` | SUPPORT, P3 | Clears gap detection output for reruns. |
| `scripts/fix_dates.py` | SUPPORT, P3 | Repairs missing dates in gap records. |
| `scripts/fix_summaries.py` | SUPPORT, P4 | Repairs malformed AI summary text. |
| `scripts/summarize_gaps.py` | SUPPORT, P4 | Local summary generation helper. |
| `scripts/cleanup_commits.py` | SUPPORT, P1 | Removes old malformed activity records. |
| `scripts/check_git_path.py` | SUPPORT | Local Git installation diagnostic. |
| `scripts/bootstrap.py` | SUPPORT | Makes direct script execution import project modules. |

## Tests

| File | Tags | Purpose |
| --- | --- | --- |
| `tests/test_github.py` | P1 | Manual GitHub ingestion test. |
| `tests/test_fetch_commits.py` | P1 | Manual API test for `/fetch_commits`. |
| `tests/test_mongo.py` | SUPPORT | Manual MongoDB connectivity test. |
| `tests/bootstrap.py` | SUPPORT | Makes direct test execution import project modules. |

## Other Files

| File | Tags | Purpose |
| --- | --- | --- |
| `requirements.txt` | SUPPORT | Python dependency list. |
| `.env` | SUPPORT | Local secrets and integration configuration. |
| `revenue_detective_test/` | P1, SUPPORT | Local/sample GitHub repository content. |
