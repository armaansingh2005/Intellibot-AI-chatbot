"""Administrator authentication and analytics."""

from models import Admin, db


def create_admin(app):
    with app.app_context():
        admin = Admin(username="reviewer")
        admin.set_password("a-long-test-password")
        db.session.add(admin)
        db.session.commit()


def test_unauthorized_admin_api_and_dashboard(client):
    assert client.get("/api/admin/analytics").status_code == 401
    assert client.get("/admin/").status_code == 302


def test_admin_login_form_includes_csrf_protection(app):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    page = client.get("/admin/login")
    assert page.status_code == 200
    assert b'name="csrf_token"' in page.data
    rejected = client.post("/admin/login", data={"username": "admin", "password": "password"})
    assert rejected.status_code == 400


def test_api_csrf_errors_use_json_format(app):
    app.config["WTF_CSRF_ENABLED"] = True
    response = app.test_client().post("/api/chat", json={"message": "hello"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_admin_login_and_invalid_credentials(client, app):
    create_admin(app)
    invalid = client.post("/admin/login", data={"username": "reviewer", "password": "wrong"})
    assert invalid.status_code == 200
    assert b"Invalid username or password" in invalid.data
    valid = client.post("/admin/login", data={
        "username": "reviewer", "password": "a-long-test-password",
    })
    assert valid.status_code == 302
    assert client.get("/api/admin/analytics").status_code == 200


def test_analytics_uses_database_data(client, app):
    create_admin(app)
    client.post("/admin/login", data={"username": "reviewer", "password": "a-long-test-password"})
    client.post("/api/chat", json={"message": "hello"})
    analytics = client.get("/api/admin/analytics").get_json()
    assert analytics["kpis"]["total_conversations"] == 1
    assert analytics["kpis"]["total_messages"] == 2
    assert analytics["kpis"]["average_messages_per_conversation"] == 2


def test_admin_conversation_search_and_csv(client, app):
    create_admin(app)
    client.post("/admin/login", data={"username": "reviewer", "password": "a-long-test-password"})
    client.post("/api/chat", json={"message": "hello"})
    listing = client.get("/api/admin/conversations?q=hello").get_json()
    assert listing["total"] == 1
    conversation_id = listing["conversations"][0]["id"]
    assert client.get(f"/admin/conversations/{conversation_id}").status_code == 200
    export = client.get("/api/admin/conversations.csv")
    assert export.status_code == 200
    assert b"conversation_id" in export.data


def test_admin_conversation_date_filter(client, app):
    from datetime import datetime, timezone

    create_admin(app)
    client.post("/admin/login", data={"username": "reviewer", "password": "a-long-test-password"})
    client.post("/api/chat", json={"message": "hello"})
    today = datetime.now(timezone.utc).date().isoformat()
    assert client.get(f"/api/admin/conversations?date_from={today}&date_to={today}").get_json()["total"] == 1
    invalid = client.get("/api/admin/conversations?date_from=not-a-date")
    assert invalid.status_code == 400


def test_csv_export_neutralizes_spreadsheet_formulas(client, app):
    create_admin(app)
    client.post("/admin/login", data={"username": "reviewer", "password": "a-long-test-password"})
    client.post("/api/chat", json={"message": "=HYPERLINK(\"https://example.test\")"})
    export = client.get("/api/admin/conversations.csv")
    assert b"'=HYPERLINK" in export.data
