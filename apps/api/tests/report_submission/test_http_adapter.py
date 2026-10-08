from datetime import UTC, datetime
from uuid import UUID

from community_safety_api import create_app
from community_safety_api.report_submission import create_submit_report
from community_safety_api.report_submission.adapters import ReportStoreError
from community_safety_api.report_submission.adapters.memory import InMemoryReportStore


def test_post_reports_returns_a_receipt() -> None:
    report_id = UUID("0199c5c0-7d70-7000-8000-000000000010")
    submitted_at = datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC)
    submit_report = create_submit_report(
        store=InMemoryReportStore(),
        clock=lambda: submitted_at,
        report_ids=lambda: report_id,
    )
    app = create_app({"TESTING": True}, submit_report=submit_report)

    with app.test_client() as client:
        response = client.post(
            "/reports",
            json={
                "category": "environmental_hazard",
                "description": "Broken lighting has left the west stairwell dark.",
                "occurred_at": "2026-10-08T19:30:00-04:00",
                "location": "West stairwell, second floor",
            },
        )

    assert response.status_code == 201
    assert response.get_json() == {
        "report_id": str(report_id),
        "status": "received",
        "submitted_at": "2026-10-08T23:34:12Z",
    }


def test_post_reports_returns_all_field_violations() -> None:
    submit_report = create_submit_report(
        store=InMemoryReportStore(),
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000011"),
    )
    app = create_app({"TESTING": True}, submit_report=submit_report)

    with app.test_client() as client:
        response = client.post(
            "/reports",
            json={
                "category": "unknown",
                "description": "short",
                "occurred_at": "2026-10-08T23:30:00",
                "location": "x" * 201,
            },
        )

    assert response.status_code == 422
    assert response.get_json() == {
        "error": {
            "code": "validation_failed",
            "message": "Correct the highlighted fields.",
            "fields": {
                "category": [{"code": "invalid_category", "message": "Select a valid category."}],
                "description": [{"code": "too_short", "message": "Enter at least 20 characters."}],
                "occurred_at": [{"code": "timezone_required", "message": "Include a timezone."}],
                "location": [{"code": "too_long", "message": "Enter no more than 200 characters."}],
            },
        }
    }


def test_post_reports_treats_missing_required_fields_as_validation_errors() -> None:
    submit_report = create_submit_report(
        store=InMemoryReportStore(),
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000013"),
    )
    app = create_app({"TESTING": True}, submit_report=submit_report)

    with app.test_client() as client:
        response = client.post("/reports", json={})

    assert response.status_code == 422
    assert response.get_json() == {
        "error": {
            "code": "validation_failed",
            "message": "Correct the highlighted fields.",
            "fields": {
                "category": [{"code": "invalid_category", "message": "Select a valid category."}],
                "description": [{"code": "too_short", "message": "Enter at least 20 characters."}],
                "occurred_at": [{"code": "timezone_required", "message": "Include a timezone."}],
            },
        }
    }


def test_post_reports_returns_service_unavailable_without_database_configuration() -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": None})

    with app.test_client() as client:
        response = client.post(
            "/reports",
            json={
                "category": "other",
                "description": "A detailed report submitted without database configuration.",
                "occurred_at": "2026-10-08T23:30:00Z",
            },
        )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": {
            "code": "submission_unavailable",
            "message": "The report could not be submitted. Try again.",
        }
    }


def test_post_reports_returns_validation_errors_for_a_non_object_json_payload() -> None:
    submit_report = create_submit_report(
        store=InMemoryReportStore(),
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000014"),
    )
    app = create_app({"TESTING": True}, submit_report=submit_report)

    with app.test_client() as client:
        response = client.post("/reports", json=[])

    assert response.status_code == 422
    assert response.get_json() == {
        "error": {
            "code": "validation_failed",
            "message": "Correct the highlighted fields.",
            "fields": {
                "category": [{"code": "invalid_category", "message": "Select a valid category."}],
                "description": [{"code": "too_short", "message": "Enter at least 20 characters."}],
                "occurred_at": [{"code": "timezone_required", "message": "Include a timezone."}],
            },
        }
    }


def test_post_reports_returns_validation_errors_for_invalid_field_types() -> None:
    submit_report = create_submit_report(
        store=InMemoryReportStore(),
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000015"),
    )
    app = create_app({"TESTING": True}, submit_report=submit_report)

    with app.test_client() as client:
        response = client.post(
            "/reports",
            json={
                "category": None,
                "description": None,
                "occurred_at": None,
                "location": 42,
            },
        )

    assert response.status_code == 422
    assert response.get_json() == {
        "error": {
            "code": "validation_failed",
            "message": "Correct the highlighted fields.",
            "fields": {
                "category": [{"code": "invalid_category", "message": "Select a valid category."}],
                "description": [{"code": "invalid_type", "message": "Enter a valid description."}],
                "occurred_at": [
                    {"code": "invalid_type", "message": "Enter a valid date and time."}
                ],
                "location": [{"code": "invalid_type", "message": "Enter a valid location."}],
            },
        }
    }


def test_post_reports_returns_service_unavailable_when_storage_fails() -> None:
    class UnavailableStore:
        def save(self, report: object) -> None:
            raise ReportStoreError

    submit_report = create_submit_report(
        store=UnavailableStore(),
        clock=lambda: datetime(2026, 10, 8, 23, 34, 12, tzinfo=UTC),
        report_ids=lambda: UUID("0199c5c0-7d70-7000-8000-000000000012"),
    )
    app = create_app({"TESTING": True}, submit_report=submit_report)

    with app.test_client() as client:
        response = client.post(
            "/reports",
            json={
                "category": "property_damage",
                "description": "A window was broken beside the community entrance.",
                "occurred_at": "2026-10-08T23:30:00Z",
            },
        )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": {
            "code": "submission_unavailable",
            "message": "The report could not be submitted. Try again.",
        }
    }
