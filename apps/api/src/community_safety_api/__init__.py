"""Community Safety Lab API."""

from collections.abc import Mapping

from flask import Flask


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if test_config is not None:
        app.config.from_mapping(test_config)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
