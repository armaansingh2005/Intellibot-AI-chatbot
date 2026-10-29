"""Chat UI and conversation APIs."""

import logging
import time
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, render_template, request, session
from sqlalchemy import desc

from chatbot.response_manager import ResponseManager
from models import Conversation, Message, db

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)
MAX_MESSAGE_LENGTH = 2000


def owner_id() -> str:
    if "owner_id" not in session:
        import secrets
        session["owner_id"] = secrets.token_urlsafe(32)
    session.permanent = True
    return session["owner_id"]


def owned_conversation(conversation_id: int):
    return Conversation.query.filter_by(id=conversation_id, owner_id=owner_id()).first()


@chat_bp.get("/")
def index():
    owner_id()
    return render_template("index.html")


@chat_bp.get("/history")
def history_page():
    owner_id()
    return render_template("history.html")


@chat_bp.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "IntelliBot AI"})


@chat_bp.route("/api/conversations", methods=["GET", "POST"])
def conversations():
    user_id = owner_id()
    if request.method == "POST":
        conversation = Conversation(owner_id=user_id)
        db.session.add(conversation)
        db.session.commit()
        return jsonify({"conversation": conversation.to_dict()}), 201
    items = (
        Conversation.query.filter_by(owner_id=user_id)
        .order_by(desc(Conversation.last_activity)).limit(100).all()
    )
    return jsonify({"conversations": [item.to_dict() for item in items]})


@chat_bp.get("/api/conversations/<int:conversation_id>")
def conversation_detail(conversation_id: int):
    conversation = owned_conversation(conversation_id)
    if conversation is None:
        return jsonify({"error": {"code": "not_found", "message": "Conversation not found."}}), 404
    return jsonify({"conversation": conversation.to_dict(include_messages=True)})


@chat_bp.delete("/api/conversations/<int:conversation_id>")
def delete_conversation(conversation_id: int):
    conversation = owned_conversation(conversation_id)
    if conversation is None:
        return jsonify({"error": {"code": "not_found", "message": "Conversation not found."}}), 404
    db.session.delete(conversation)
    db.session.commit()
    return jsonify({"message": "Conversation deleted."})


@chat_bp.post("/api/chat")
def chat():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": {"code": "invalid_json", "message": "Send a JSON object."}}), 400
    text = body.get("message")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": {"code": "empty_message", "message": "Please enter a message."}}), 400
    text = text.strip()
    if len(text) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": {"code": "message_too_long", "message": f"Messages must be {MAX_MESSAGE_LENGTH} characters or fewer."}}), 413
    user_id = owner_id()
    conversation_id = body.get("conversation_id")
    if conversation_id is None:
        conversation = Conversation(owner_id=user_id)
        db.session.add(conversation)
        db.session.flush()
    elif isinstance(conversation_id, int) and not isinstance(conversation_id, bool):
        conversation = Conversation.query.filter_by(id=conversation_id, owner_id=user_id).first()
        if conversation is None:
            return jsonify({"error": {"code": "not_found", "message": "Conversation not found."}}), 404
    else:
        return jsonify({"error": {"code": "invalid_conversation", "message": "conversation_id must be an integer."}}), 400

    started = time.perf_counter()
    try:
        prior_messages = (
            Message.query.filter_by(conversation_id=conversation.id)
            .order_by(desc(Message.created_at)).limit(8).all()
        )
        result = current_app.extensions["nlp_engine"].process(text, list(reversed(prior_messages)))
    except Exception:
        db.session.rollback()
        logger.exception("Chat processing failed.")
        return jsonify({"error": {"code": "processing_error", "message": "Sorry, I couldn't process that. Please try again."}}), 500
    elapsed_ms = (time.perf_counter() - started) * 1000
    user_message = Message(
        conversation=conversation, role="user", content=text,
        intent=result["intent"], confidence=result["confidence"],
        response_time_ms=elapsed_ms,
    )
    bot_message = Message(
        conversation=conversation, role="assistant", content=result["response"],
        intent=result["intent"], confidence=result["confidence"],
        response_time_ms=elapsed_ms,
    )
    conversation.last_activity = datetime.now(timezone.utc)
    db.session.add_all([user_message, bot_message])
    db.session.commit()
    return jsonify({
        "conversation_id": conversation.id,
        "response": result["response"],
        "intent": result["intent"],
        "confidence": round(result["confidence"], 4),
        "suggestions": result["suggestions"],
        "created_at": bot_message.created_at.isoformat(),
        "response_time_ms": round(elapsed_ms, 2),
    })
