from datetime import datetime
from typing import cast

from flask import Blueprint, request

from .._model import (
    InvalidReport,
    ReportCategory,
    ReportSubmissionUnavailable,
    SubmitReportCommand,
)
from .._submit import SubmitReport

_VIOLATION_MESSAGES = {
    ("category", "invalid_category"): "Select a valid category.",
    ("description", "too_short"): "Enter at least 20 characters.",
    ("description", "too_long"): "Enter no more than 2,000 characters.",
    ("description", "invalid_type"): "Enter a valid description.",
    ("occurred_at", "timezone_required"): "Include a timezone.",
    ("occurred_at", "in_future"): "Enter a time that is not in the future.",
    ("occurred_at", "invalid_type"): "Enter a valid date and time.",
    ("location", "too_long"): "Enter no more than 200 characters.",
    ("location", "invalid_type"): "Enter a valid location.",
}


def create_report_blueprint(submit_report: SubmitReport) -> Blueprint:
    """Create the Flask adapter for report submission."""
    blueprint = Blueprint("report_submission", __name__)

    @blueprint.post("/reports")
    def post_report() -> tuple[dict[str, object], int]:
        payload = request.get_json()
        if not isinstance(payload, dict):
            payload = {}
        transport_fields: dict[str, list[dict[str, str]]] = {}
        if "category" in payload and not isinstance(payload["category"], str):
            transport_fields["category"] = [
                {
                    "code": "invalid_category",
                    "message": _VIOLATION_MESSAGES[("category", "invalid_category")],
                }
            ]
        if "description" in payload and not isinstance(payload["description"], str):
            transport_fields["description"] = [
                {
                    "code": "invalid_type",
                    "message": _VIOLATION_MESSAGES[("description", "invalid_type")],
                }
            ]
        if "occurred_at" in payload and not isinstance(payload["occurred_at"], str):
            transport_fields["occurred_at"] = [
                {
                    "code": "invalid_type",
                    "message": _VIOLATION_MESSAGES[("occurred_at", "invalid_type")],
                }
            ]
        if (
            "location" in payload
            and payload["location"] is not None
            and not isinstance(payload["location"], str)
        ):
            transport_fields["location"] = [
                {
                    "code": "invalid_type",
                    "message": _VIOLATION_MESSAGES[("location", "invalid_type")],
                }
            ]
        if transport_fields:
            return (
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "Correct the highlighted fields.",
                        "fields": transport_fields,
                    }
                },
                422,
            )
        raw_category = payload.get("category")
        if isinstance(raw_category, str):
            try:
                category = ReportCategory(raw_category)
            except ValueError:
                category = cast(ReportCategory, raw_category)
        else:
            category = cast(ReportCategory, raw_category)
        raw_occurred_at = payload.get("occurred_at")
        try:
            occurred_at = (
                datetime.fromisoformat(raw_occurred_at)
                if isinstance(raw_occurred_at, str)
                else datetime.min
            )
        except ValueError:
            occurred_at = datetime.min
        try:
            result = submit_report(
                SubmitReportCommand(
                    category=category,
                    description=payload.get("description", ""),
                    occurred_at=occurred_at,
                    location=payload.get("location"),
                )
            )
        except InvalidReport as error:
            fields: dict[str, list[dict[str, str]]] = {}
            for violation in error.violations:
                fields.setdefault(violation.field, []).append(
                    {
                        "code": violation.code,
                        "message": _VIOLATION_MESSAGES[(violation.field, violation.code)],
                    }
                )
            return (
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "Correct the highlighted fields.",
                        "fields": fields,
                    }
                },
                422,
            )
        except ReportSubmissionUnavailable:
            return (
                {
                    "error": {
                        "code": "submission_unavailable",
                        "message": "The report could not be submitted. Try again.",
                    }
                },
                503,
            )
        return (
            {
                "report_id": str(result.report_id),
                "status": result.status,
                "submitted_at": result.submitted_at.isoformat().replace("+00:00", "Z"),
            },
            201,
        )

    return blueprint
