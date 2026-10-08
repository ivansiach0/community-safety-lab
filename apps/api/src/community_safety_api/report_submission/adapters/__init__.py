"""Adapters used by report submission."""

from .._model import StoredReport
from .._store import ReportStoreError

__all__ = ["ReportStoreError", "StoredReport"]
