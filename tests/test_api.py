"""HTTP API behavior and conversation access checks."""


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_chat_rejects_malformed_and_empty_messages(client):
    assert client.post("/api/chat", data="not json", content_type="application/json").status_code == 400
    empty = client.post("/api/chat", json={"message": "  "})
    assert empty.status_code == 400
    assert empty.get_json()["error"]["code"] == "empty_message"


def test_chat_rejects_overlong_message(client):
    response = client.post("/api/chat", json={"message": "x" * 2001})
    assert response.status_code == 413


def test_chat_persists_messages_and_returns_response(client):
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["conversation_id"]
    assert payload["response"]
    detail = client.get(f"/api/conversations/{payload['conversation_id']}")
    assert detail.status_code == 200
    messages = detail.get_json()["conversation"]["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "hello"


def test_conversation_is_not_visible_to_another_session(client, app):
    response = client.post("/api/conversations")
    conversation_id = response.get_json()["conversation"]["id"]
    other = app.test_client()
    assert other.get(f"/api/conversations/{conversation_id}").status_code == 404
    assert other.delete(f"/api/conversations/{conversation_id}").status_code == 404


def test_conversation_list_create_and_delete(client):
    created = client.post("/api/conversations")
    conversation_id = created.get_json()["conversation"]["id"]
    assert created.status_code == 201
    assert client.get("/api/conversations").get_json()["conversations"][0]["id"] == conversation_id
    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 200
    assert client.get(f"/api/conversations/{conversation_id}").status_code == 404
