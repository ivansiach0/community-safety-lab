from datetime import UTC, datetime
from uuid import UUID

import pytest

from community_safety_api.report_submission import ReportCategory
from community_safety_api.report_submission.adapters import ReportStoreError, StoredReport
from community_safety_api.report_submission.adapters.memory import InMemoryReportStore


def test_memory_store_rejects_a_duplicate_report_id() -> None:
    store = InMemoryReportStore()
    report = StoredReport(
        report_id=UUID("0199c5c0-7d70-7000-8000-000000000020"),
        category=ReportCategory.OTHER,
        description="A sufficiently detailed community safety report.",
        occurred_at=datetime(2026, 10, 8, 23, 30, tzinfo=UTC),
        location=None,
        status="received",
        submitted_at=datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
    )
    store.save(report)

    with pytest.raises(ReportStoreError):
        store.save(report)
