from typing import Protocol

from ._model import StoredReport


class ReportStore(Protocol):
    """Store normalized reports."""

    def save(self, report: StoredReport) -> None:
        """Persist one report."""


class ReportStoreError(Exception):
    """A storage adapter could not persist a report."""
