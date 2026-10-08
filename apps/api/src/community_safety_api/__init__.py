"""Community Safety Lab API."""

import os
from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import uuid7

from flask import Flask

from .report_submission import (
    ReportSubmissionUnavailable,
    SubmitReport,
    SubmitReportCommand,
    SubmitReportResult,
    create_submit_report,
)
from .report_submission.adapters.http import create_report_blueprint
from .report_submission.adapters.postgres import PostgresReportStore


def create_app(
    test_config: Mapping[str, object] | None = None,
    *,
    submit_report: SubmitReport | None = None,
) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(DATABASE_URL=os.environ.get("DATABASE_URL"))

    if test_config is not None:
        app.config.from_mapping(test_config)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if submit_report is None:
        database_url = app.config.get("DATABASE_URL")
        if isinstance(database_url, str):
            submit_report = create_submit_report(
                store=PostgresReportStore(database_url),
                clock=lambda: datetime.now(UTC),
                report_ids=uuid7,
            )
        else:

            def submit_report_without_storage(
                _command: SubmitReportCommand,
            ) -> SubmitReportResult:
                raise ReportSubmissionUnavailable

            submit_report = submit_report_without_storage

    if submit_report is not None:
        app.register_blueprint(create_report_blueprint(submit_report))

    return app
