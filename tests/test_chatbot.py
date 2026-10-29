"""NLP pipeline and knowledge-base behavior."""

from chatbot.response_manager import ResponseManager


def test_greeting_is_classified_and_answered(client):
    result = client.post("/api/chat", json={"message": "hello"}).get_json()
    assert result["intent"] == "greeting"
    assert "Hello" in result["response"]


def test_faq_delivery_answer_is_grounded_in_config(client):
    result = client.post("/api/chat", json={"message": "What are your delivery options?"}).get_json()
    assert result["intent"] == "shipping"
    assert "3–5 business days" in result["response"]


def test_unknown_question_uses_safe_fallback(client):
    result = client.post("/api/chat", json={"message": "What is the weather tomorrow on Mars?"}).get_json()
    assert result["intent"] == "fallback"
    assert "not quite sure" in result["response"]


def test_followup_uses_recent_delivery_context(client):
    first = client.post("/api/chat", json={"message": "What are your delivery options?"}).get_json()
    second = client.post("/api/chat", json={
        "message": "How long does it take?",
        "conversation_id": first["conversation_id"],
    }).get_json()
    assert "3–5 business days" in second["response"]


def test_delivery_cost_followup_uses_shipping_faq(client):
    first = client.post("/api/chat", json={"message": "What are your delivery options?"}).get_json()
    second = client.post("/api/chat", json={
        "message": "And how much does it cost?",
        "conversation_id": first["conversation_id"],
    }).get_json()
    assert "free for eligible orders" in second["response"]


def test_order_status_never_claims_live_access(client):
    result = client.post("/api/chat", json={"message": "Where is my order?"}).get_json()
    assert "can’t access live order records" in result["response"]


def test_low_confidence_response_is_safe():
    manager = ResponseManager(None)
    text, intent = manager.respond("unrelated", "unknown", 0.99)
    assert intent == "fallback"
    assert "not quite sure" in text
