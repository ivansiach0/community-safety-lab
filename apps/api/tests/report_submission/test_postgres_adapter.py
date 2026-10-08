import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from community_safety_api import create_app
from community_safety_api.report_submission import ReportCategory
from community_safety_api.report_submission.adapters import ReportStoreError, StoredReport
from community_safety_api.report_submission.adapters.postgres import PostgresReportStore


def test_postgres_store_rejects_a_duplicate_report_id() -> None:
    database_url = os.environ.get("COMMUNITY_SAFETY_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("COMMUNITY_SAFETY_TEST_DATABASE_URL is required")

    store = PostgresReportStore(database_url)
    report = StoredReport(
        report_id=uuid4(),
        category=ReportCategory.THREAT_OR_VIOLENCE,
        description="A sufficiently detailed community safety report.",
        occurred_at=datetime(2026, 10, 8, 23, 30, tzinfo=UTC),
        location="Community entrance",
        status="received",
        submitted_at=datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
    )
    store.save(report)

    with pytest.raises(ReportStoreError):
        store.save(report)


def test_application_uses_the_configured_postgres_store() -> None:
    database_url = os.environ.get("COMMUNITY_SAFETY_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("COMMUNITY_SAFETY_TEST_DATABASE_URL is required")

    app = create_app({"TESTING": True, "DATABASE_URL": database_url})

    with app.test_client() as client:
        response = client.post(
            "/reports",
            json={
                "category": "other",
                "description": "A detailed report persisted by the configured application.",
                "occurred_at": "2026-10-07T23:30:00Z",
            },
        )

    assert response.status_code == 201
    assert response.get_json()["status"] == "received"
