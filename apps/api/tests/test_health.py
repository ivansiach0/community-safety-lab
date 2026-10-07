from community_safety_api import create_app


def test_health_endpoint_reports_ok() -> None:
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
