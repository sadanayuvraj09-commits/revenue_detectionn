# Unbilled Revenue Detective

Detects gaps between developer activity and logged timesheet hours, using AI to summarize, classify, and explain those gaps.

## Quick start

1. Create and activate a virtual environment
   - `python -m venv venv`
   - Windows: `venv\Scripts\Activate.ps1`
2. Install dependencies
   - `pip install -r requirements.txt`
3. Copy the sample environment file and fill in your values
   - `copy .env.example .env`
4. Start the API
   - `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`
5. Open the docs
   - `http://127.0.0.1:8000/docs`

## What changed for speed

- AI calls now use fewer retries and no artificial waits.
- GitHub imports are batched to reduce MongoDB write overhead.
- Gap summarization uses footprint data more efficiently so dashboard requests are lighter.
- Database connections use a smaller, more stable pool for faster startup and predictable behavior.

## Features

- Activity ingestion from GitHub, Slack, and Jira
- Digital footprint aggregation per developer per day
- Timesheet create, update, delete, and CSV import
- Gap detection and automatic summarization
- AI-powered summaries, priorities, suggestions, and gap answering
- Alert creation and Slack notifications

## Project structure

- `src/` - core API and service logic
- `scripts/` - maintenance and data scripts
- `tests/` - automated test coverage
- `PROJECT_PHASES.md` - implementation history
