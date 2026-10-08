from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID


class ReportCategory(StrEnum):
    """Supported report categories."""

    HARASSMENT = "harassment"
    THREAT_OR_VIOLENCE = "threat_or_violence"
    PROPERTY_DAMAGE = "property_damage"
    ENVIRONMENTAL_HAZARD = "environmental_hazard"
    OTHER = "other"


@dataclass(frozen=True)
class SubmitReportCommand:
    """Information supplied by a person submitting a report."""

    category: ReportCategory
    description: str
    occurred_at: datetime
    location: str | None = None


@dataclass(frozen=True)
class SubmitReportResult:
    """Confirmation returned after a report is stored."""

    report_id: UUID
    status: Literal["received"]
    submitted_at: datetime


@dataclass(frozen=True)
class ReportViolation:
    """Stable field-level validation failure."""

    field: str
    code: str


class InvalidReport(Exception):
    """A submitted report violates one or more input rules."""

    def __init__(self, violations: tuple[ReportViolation, ...]) -> None:
        super().__init__("The report is invalid.")
        self.violations = violations


class ReportSubmissionUnavailable(Exception):
    """A report could not be stored at this time."""


@dataclass(frozen=True)
class StoredReport:
    """Normalized report passed to a storage adapter."""

    report_id: UUID
    category: ReportCategory
    description: str
    occurred_at: datetime
    location: str | None
    status: Literal["received"]
    submitted_at: datetime
