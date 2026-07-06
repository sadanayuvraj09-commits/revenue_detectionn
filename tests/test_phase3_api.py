import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_NAME", "unbilled_detective")
os.environ.setdefault("GITHUB_TOKEN", "")
os.environ.setdefault("SLACK_BOT_TOKEN", "")
os.environ.setdefault("JIRA_EMAIL", "")
os.environ.setdefault("JIRA_API_TOKEN", "")
os.environ.setdefault("JIRA_BASE_URL", "")

from src.main import app


class FakeCursor:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, *args, **kwargs):
        return self

    async def to_list(self, limit):
        return self.docs[:limit]

    async def delete_many(self, query):
        deleted = len(self.docs)
        self.docs = []
        return type("DeleteResult", (), {"deleted_count": deleted})()

    async def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.docs[index]
                return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()

    async def update_one(self, query, update, upsert=False):
        existing = None
        for index, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                existing = index
                break

        if existing is None:
            new_doc = {**query, **update.get("$set", {})}
            self.docs.append(new_doc)
            return type("Result", (), {"upserted_id": "new", "modified_count": 0, "matched_count": 0})()

        self.docs[existing] = {**self.docs[existing], **update.get("$set", {})}
        return type("Result", (), {"upserted_id": None, "modified_count": 1, "matched_count": 1})()

    async def insert_many(self, docs):
        self.docs.extend(docs)
        return type("InsertResult", (), {"inserted_ids": list(range(len(docs)))})()

    async def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None


class FakeDb:
    def __init__(self):
        self.timesheets = FakeCursor([])
        self.gaps = FakeCursor([])
        self.collections = {
            "timesheet_entries": self.timesheets,
            "detected_gaps": self.gaps,
        }

    def __getitem__(self, key):
        return self.collections[key]

    async def list_collection_names(self):
        return ["timesheet_entries", "detected_gaps"]


class Phase3ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.fake_db = FakeDb()

    def test_upsert_timesheets_endpoint_normalizes_fields(self):
        with patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/timesheets",
                json={
                    "developer_id": "john doe",
                    "date": "2026-07-01",
                    "hours_logged": "8",
                    "project": "demo",
                    "notes": "ok",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["inserted"], 1)
        self.assertEqual(self.fake_db.timesheets.docs[0]["developer_id"], "JOHN DOE")
        self.assertEqual(self.fake_db.timesheets.docs[0]["hours_logged"], 8.0)

    def test_import_timesheets_endpoint_accepts_csv_upload(self):
        with patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/import_timesheets",
                files={
                    "file": (
                        "timesheets.csv",
                        "developer_id,date,hours_logged,project,notes\njohn doe,2026-07-01,7.5,demo,ok\n",
                        "text/csv",
                    )
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["inserted"], 1)
        self.assertEqual(response.json()["skipped"], 0)
        self.assertEqual(self.fake_db.timesheets.docs[0]["developer_id"], "JOHN DOE")

    def test_refresh_gaps_endpoint_runs_gap_detection(self):
        with patch("src.main.db", self.fake_db), patch("src.main.run_gap_detection", return_value={"total_gaps": 1, "new_gaps_saved": 1, "detected_gaps": []}):
            response = self.client.post("/refresh_gaps")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_total_gaps"], 1)
        self.assertEqual(response.json()["new_gaps_saved"], 1)

    def test_classify_gap_endpoint_returns_classification(self):
        with patch("src.main.generate_gap_priority", return_value="High priority: missing timesheet"), patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/classify_gap",
                json={
                    "developer_id": "JANE DOE",
                    "date": "2026-07-01",
                    "github_count": 2,
                    "slack_count": 1,
                    "jira_count": 0,
                    "hours_logged": 0,
                    "reason": "Missing timesheet",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["classification"], "High priority: missing timesheet")

    def test_suggest_timesheet_endpoint_returns_suggestion(self):
        expected = {"hours": 2, "project": "Client Bugfix", "note": "Log work on bug fix."}
        with patch("src.main.suggest_timesheet_entry", return_value=expected), patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/suggest_timesheet",
                json={
                    "developer_id": "JANE DOE",
                    "date": "2026-07-01",
                    "github_count": 2,
                    "slack_count": 1,
                    "jira_count": 0,
                    "hours_logged": 2,
                    "activity_summary": "Fixed customer bug.",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggested_timesheet"], expected)

    def test_match_activity_endpoint_returns_project_match(self):
        with patch("src.main.match_activity_to_project", return_value="Client Project - Critical Bug"), patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/match_activity",
                json={
                    "developer_id": "JANE DOE",
                    "date": "2026-07-01",
                    "commit_messages": "Fix login issue",
                    "slack_messages": "Reviewed deployment",
                    "jira_issues": "BUG-8989",
                    "current_projects": "Project Alpha",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["match"], "Client Project - Critical Bug")

    def test_ask_endpoint_returns_answer(self):
        with patch("src.main.answer_gap_question", return_value="This gap is due to unlogged hours."), patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/ask",
                json={
                    "developer_id": "JANE DOE",
                    "date": "2026-07-01",
                    "github_count": 2,
                    "slack_count": 1,
                    "jira_count": 0,
                    "hours_logged": 0,
                    "reason": "Missing timesheet",
                    "details": "Developer had commits but no timesheet entry.",
                    "question": "Why do we have a gap?",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "This gap is due to unlogged hours.")

    def test_ask_endpoint_rejects_missing_question(self):
        with patch("src.main.db", self.fake_db):
            response = self.client.post(
                "/ask",
                json={
                    "developer_id": "JANE DOE",
                    "date": "2026-07-01",
                    "github_count": 2,
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "question is required")


if __name__ == "__main__":
    unittest.main()
