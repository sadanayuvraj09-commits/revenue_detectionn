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

## Project Structure

- src/ - core application logic (services, database, config, main API)
- scripts/ - one-off maintenance and setup scripts
- tests/ - test scripts
- PROJECT_PHASES.md - detailed phase-by-phase breakdown of what was built

## Development Phases

See PROJECT_PHASES.md for a detailed breakdown of each development phase.
