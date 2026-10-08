from datetime import UTC, datetime, timedelta, timezone
from typing import cast
from uuid import UUID

import pytest

from community_safety_api.report_submission import (
    InvalidReport,
    ReportCategory,
    ReportSubmissionUnavailable,
    SubmitReportCommand,
    create_submit_report,
)
from community_safety_api.report_submission.adapters import ReportStoreError
from community_safety_api.report_submission.adapters.memory import InMemoryReportStore


def test_submits_a_valid_report() -> None:
    report_id = UUID("0199c5c0-7d70-7000-8000-000000000001")
    submitted_at = datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC)
    store = InMemoryReportStore()
    submit_report = create_submit_report(
        store=store,
        clock=lambda: submitted_at,
        report_ids=lambda: report_id,
    )

    result = submit_report(
        SubmitReportCommand(
            category=ReportCategory.ENVIRONMENTAL_HAZARD,
            description="Broken lighting in the west stairwell.",
            occurred_at=datetime(2026, 10, 8, 23, 30, tzinfo=UTC),
            location="Second floor",
        )
    )

    assert result.report_id == report_id
    assert result.status == "received"
    assert result.submitted_at == submitted_at
    assert store.get_saved(report_id).description == "Broken lighting in the west stairwell."


def test_normalizes_report_values_before_storage() -> None:
    report_id = UUID("0199c5c0-7d70-7000-8000-000000000002")
    submitted_at = datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC)
    store = InMemoryReportStore()
    submit_report = create_submit_report(
        store=store,
        clock=lambda: submitted_at,
        report_ids=lambda: report_id,
    )

    submit_report(
        SubmitReportCommand(
            category=ReportCategory.HARASSMENT,
            description="  Repeated threatening messages were left on my door.  ",
            occurred_at=datetime(
                2026,
                10,
                8,
                19,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            location="   ",
        )
    )

    stored = store.get_saved(report_id)
    assert stored.description == "Repeated threatening messages were left on my door."
    assert stored.occurred_at == datetime(2026, 10, 8, 23, 30, tzinfo=UTC)
    assert stored.location is None


def test_rejects_all_invalid_fields_without_saving() -> None:
    store = InMemoryReportStore()
    submit_report = create_submit_report(
        store=store,
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000003"),
    )

    with pytest.raises(InvalidReport) as raised:
        submit_report(
            SubmitReportCommand(
                category=cast(ReportCategory, "unknown"),
                description="   ",
                occurred_at=datetime(2026, 10, 8, 23, 30),
                location="x" * 201,
            )
        )

    assert [(item.field, item.code) for item in raised.value.violations] == [
        ("category", "invalid_category"),
        ("description", "too_short"),
        ("occurred_at", "timezone_required"),
        ("location", "too_long"),
    ]
    assert store.saved_count == 0


def test_rejects_an_occurred_time_beyond_the_future_tolerance() -> None:
    submitted_at = datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC)
    store = InMemoryReportStore()
    submit_report = create_submit_report(
        store=store,
        clock=lambda: submitted_at,
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000004"),
    )

    with pytest.raises(InvalidReport) as raised:
        submit_report(
            SubmitReportCommand(
                category=ReportCategory.OTHER,
                description="A detailed report of an event that just occurred.",
                occurred_at=submitted_at + timedelta(minutes=5, seconds=1),
            )
        )

    assert [(item.field, item.code) for item in raised.value.violations] == [
        ("occurred_at", "in_future")
    ]
    assert store.saved_count == 0


def test_reports_when_persistence_is_unavailable() -> None:
    class UnavailableStore:
        def save(self, report: object) -> None:
            raise ReportStoreError

    submit_report = create_submit_report(
        store=UnavailableStore(),
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000005"),
    )

    with pytest.raises(ReportSubmissionUnavailable):
        submit_report(
            SubmitReportCommand(
                category=ReportCategory.PROPERTY_DAMAGE,
                description="A window was broken beside the community entrance.",
                occurred_at=datetime(2026, 10, 8, 23, 30, tzinfo=UTC),
            )
        )
