from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from ._model import (
    InvalidReport,
    ReportCategory,
    ReportSubmissionUnavailable,
    ReportViolation,
    StoredReport,
    SubmitReportCommand,
    SubmitReportResult,
)
from ._store import ReportStore, ReportStoreError

type Clock = Callable[[], datetime]
type ReportIdGenerator = Callable[[], UUID]


class SubmitReport(Protocol):
    """Submit a report through the application seam."""

    def __call__(self, command: SubmitReportCommand, /) -> SubmitReportResult:
        """Store a report and return its receipt."""


def create_submit_report(
    *, store: ReportStore, clock: Clock, report_ids: ReportIdGenerator
) -> SubmitReport:
    """Bind external dependencies to the report submission seam."""

    def submit_report(command: SubmitReportCommand, /) -> SubmitReportResult:
        submitted_at = clock()
        description = command.description.strip()
        location = command.location.strip() if command.location is not None else None
        violations: list[ReportViolation] = []

        if not isinstance(command.category, ReportCategory):
            violations.append(ReportViolation("category", "invalid_category"))
        if len(description) < 20:
            violations.append(ReportViolation("description", "too_short"))
        elif len(description) > 2_000:
            violations.append(ReportViolation("description", "too_long"))
        if command.occurred_at.tzinfo is None or command.occurred_at.utcoffset() is None:
            violations.append(ReportViolation("occurred_at", "timezone_required"))
        elif command.occurred_at.astimezone(UTC) > submitted_at.astimezone(UTC) + timedelta(
            minutes=5
        ):
            violations.append(ReportViolation("occurred_at", "in_future"))
        if location is not None and len(location) > 200:
            violations.append(ReportViolation("location", "too_long"))

        if violations:
            raise InvalidReport(tuple(violations))

        report_id = report_ids()
        report = StoredReport(
            report_id=report_id,
            category=command.category,
            description=description,
            occurred_at=command.occurred_at.astimezone(UTC),
            location=location or None,
            status="received",
            submitted_at=submitted_at,
        )
        try:
            store.save(report)
        except ReportStoreError:
            raise ReportSubmissionUnavailable from None
        return SubmitReportResult(
            report_id=report_id,
            status="received",
            submitted_at=submitted_at,
        )

    return submit_report
