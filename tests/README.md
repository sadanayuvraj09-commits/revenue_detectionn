# Unbilled Revenue Detective

Detects gaps between developer activity (GitHub commits, Slack messages, Jira updates) and logged timesheet hours, using AI to summarize and prioritize the gaps found.

## Setup

1. Clone the repo:
   git clone https://github.com/sadanayuvraj09-commits/internship-complete-project.git
   cd internship-complete-project

2. Create a virtual environment and install dependencies:
   python -m venv venv
   source venv/bin/activate   (on Windows: venv\Scripts\activate)
   pip install -r requirements.txt

3. Create a .env file in the root with your real values (see .env.example for the list of variables needed).

4. Run the API:
   uvicorn src.main:app --reload

5. Open http://127.0.0.1:8000/docs in your browser to see and test all endpoints interactively.

## Features

- Activity ingestion: pulls developer activity from GitHub, Slack, and Jira into a shared database
- Digital footprint: aggregates each developer's daily activity across all three sources
- Timesheet management: create, update, delete, and bulk-import (CSV) timesheet entries
- Gap detection: compares logged hours against real activity to detect gaps, runs automatically on a schedule
- AI analysis: uses Gemini to summarize gaps, classify priority, suggest timesheet entries, match activity to projects, and answer questions about a gap
- Alerts: detects significant gaps and sends Slack notifications, with alert history and resolution tracking

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| / | GET | Root health message |
| /health | GET | Health check |
| /fetch_commits | POST | Pull latest commits from GitHub |
| /commits | GET | List stored commits |
| /fetch_slack_messages | POST | Pull latest messages from Slack |
| /slack_activity | GET | List stored Slack activity |
| /fetch_jira_updates | POST | Pull latest issues from Jira |
| /jira_activity | GET | List stored Jira activity |
| /developers | GET | List developers |
| /timesheets | GET | List timesheets |
| /timesheets | POST | Add/update one or more timesheet entries |
| /timesheets/{developer_id}/{date} | PUT | Update a specific timesheet entry |
| /timesheets/{developer_id}/{date} | DELETE | Delete a specific timesheet entry |
| /import_timesheets | POST | Bulk-import timesheets from a CSV file |
| /detected_gaps | GET | List detected gaps |
| /check_gaps | GET | Check current gaps |
| /refresh_gaps | POST | Re-run gap detection |
| /gaps/clear | DELETE | Clear all detected gaps |
| /summarize_gaps | GET | Generate AI summaries for pending gaps |
| /classify_gap | POST | Get AI priority classification for a gap |
| /suggest_timesheet | POST | Get AI-suggested timesheet entry for a gap |
| /match_activity | POST | Match activity to a likely project using AI |
| /ask | POST | Ask a free-form question about a gap |
| /analyze_and_alert | POST | Run AI analysis and send alerts for significant gaps |
| /alerts/pending | GET | List pending alerts |
| /alerts/history | GET | List alert history |
| /alerts/{alert_id}/mark_notified | POST | Mark an alert as notified |
| /alerts/{alert_id}/resolve | POST | Resolve an alert |

## Project Structure

- src/ — core application logic (services, database, config, main API)
- scripts/ — one-off maintenance and setup scripts
- tests/ — test scripts
- PROJECT_PHASES.md — detailed phase-by-phase breakdown of what was built

## Development Phases

See PROJECT_PHASES.md for a detailed breakdown of each development phase.