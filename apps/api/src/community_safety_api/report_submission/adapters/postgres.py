from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
    Uuid,
    create_engine,
    insert,
)
from sqlalchemy.exc import SQLAlchemyError

from .._model import StoredReport
from .._store import ReportStoreError

metadata = MetaData()

reports = Table(
    "reports",
    metadata,
    Column("id", Uuid(), primary_key=True),
    Column("category", String(64), nullable=False),
    Column("description", Text(), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("location", String(200)),
    Column("status", String(32), nullable=False),
    Column("submitted_at", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "category IN ('harassment', 'threat_or_violence', 'property_damage', "
        "'environmental_hazard', 'other')",
        name="ck_reports_category",
    ),
    CheckConstraint("status IN ('received')", name="ck_reports_status"),
)


class PostgresReportStore:
    """Persist reports in PostgreSQL through SQLAlchemy."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)

    def save(self, report: StoredReport) -> None:
        """Persist one report in a transaction."""
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(reports).values(
                        id=report.report_id,
                        category=report.category.value,
                        description=report.description,
                        occurred_at=report.occurred_at,
                        location=report.location,
                        status=report.status,
                        submitted_at=report.submitted_at,
                    )
                )
        except SQLAlchemyError:
            raise ReportStoreError from None
