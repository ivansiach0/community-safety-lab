from uuid import UUID

from .._model import StoredReport
from .._store import ReportStoreError


class InMemoryReportStore:
    """Store reports in memory for interface tests."""

    def __init__(self) -> None:
        self._reports: dict[UUID, StoredReport] = {}

    def save(self, report: StoredReport) -> None:
        """Store one report."""
        if report.report_id in self._reports:
            raise ReportStoreError
        self._reports[report.report_id] = report

    def get_saved(self, report_id: UUID) -> StoredReport:
        """Return a stored report for test observation."""
        return self._reports[report_id]

    @property
    def saved_count(self) -> int:
        """Return the number of stored reports for test observation."""
        return len(self._reports)
