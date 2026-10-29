"""Administrator authentication, dashboard, and analytics endpoints."""

import csv
import io
from datetime import date, datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from models import Admin, Conversation, Message, db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")
_DUMMY_PASSWORD_HASH = generate_password_hash("not-a-real-password")


def admin_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        admin_id = session.get("admin_id")
        if not admin_id or db.session.get(Admin, admin_id) is None:
            session.pop("admin_id", None)
            if request.path.startswith("/api/"):
                return jsonify({"error": {"code": "unauthorized", "message": "Administrator login required."}}), 401
            return redirect(url_for("admin.login"))
        return function(*args, **kwargs)
    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session.clear()
            session["admin_id"] = admin.id
            session.permanent = True
            return redirect(url_for("admin.dashboard"))
        # Verify the same operation shape for unknown usernames without disclosing which field failed.
        if admin is None:
            check_password_hash(_DUMMY_PASSWORD_HASH, password or " ")
        error = "Invalid username or password."
    return render_template("admin_login.html", error=error)


@admin_bp.post("/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
@admin_required
def dashboard():
    return render_template("admin_dashboard.html")


@admin_bp.get("/conversations/<int:conversation_id>")
@admin_required
def conversation_page(conversation_id: int):
    conversation = db.session.get(Conversation, conversation_id)
    if conversation is None:
        return render_template("404.html"), 404
    return render_template("conversation_detail.html", conversation=conversation)


@admin_api_bp.get("/analytics")
@admin_required
def analytics():
    total_conversations = Conversation.query.count()
    total_messages = Message.query.count()
    user_count = Message.query.filter_by(role="user").count()
    assistant_count = Message.query.filter_by(role="assistant").count()
    fallback_count = Message.query.filter_by(role="assistant", intent="fallback").count()
    avg_messages = total_messages / total_conversations if total_conversations else 0
    avg_response = db.session.query(func.avg(Message.response_time_ms)).filter(
        Message.role == "assistant", Message.response_time_ms.isnot(None),
    ).scalar() or 0
    intent_rows = (
        db.session.query(Message.intent, func.count(Message.id))
        .filter(Message.role == "user", Message.intent.isnot(None))
        .group_by(Message.intent).order_by(func.count(Message.id).desc()).all()
    )
    daily = []
    for days_ago in range(6, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=days_ago)).date()
        start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        daily.append({
            "date": day.isoformat(),
            "conversations": Conversation.query.filter(
                Conversation.created_at >= start, Conversation.created_at < end,
            ).count(),
            "messages": Message.query.filter(
                Message.created_at >= start, Message.created_at < end,
            ).count(),
        })
    frequent = (
        db.session.query(Message.content, func.count(Message.id).label("count"))
        .filter(Message.role == "user")
        .group_by(Message.content).order_by(func.count(Message.id).desc()).limit(5).all()
    )
    return jsonify({
        "kpis": {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": round(avg_messages, 2),
            "most_frequent_intent": intent_rows[0][0] if intent_rows else "—",
            "fallback_rate": round(fallback_count / assistant_count, 4) if assistant_count else 0,
            "average_response_time_ms": round(float(avg_response), 2),
            "user_messages": user_count,
        },
        "daily": daily,
        "intent_distribution": [{"intent": name or "unknown", "count": count} for name, count in intent_rows],
        "frequent_questions": [{"question": text, "count": count} for text, count in frequent],
        "fallback_queries": [
            {"question": user_message.content, "created_at": user_message.created_at.isoformat()}
            for user_message in Message.query.filter(
                Message.role == "user",
                Message.conversation_id.in_(
                    db.session.query(Message.conversation_id)
                    .filter(Message.role == "assistant", Message.intent == "fallback")
                ),
            ).order_by(Message.created_at.desc()).limit(10)
        ],
    })


@admin_api_bp.get("/conversations")
@admin_required
def conversation_list():
    page = request.args.get("page", 1, type=int)
    page = max(page, 1)
    query = Conversation.query
    search = request.args.get("q", "").strip()[:100]
    intent = request.args.get("intent", "").strip()[:64]
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    if search:
        query = query.join(Message).filter(Message.content.ilike(f"%{search}%")).distinct()
    if intent:
        query = query.join(Message, isouter=not bool(search)).filter(Message.intent == intent).distinct()
    try:
        if date_from:
            start_date = date.fromisoformat(date_from)
            if start_date.isoformat() != date_from:
                raise ValueError("Date must use YYYY-MM-DD.")
            query = query.filter(
                Conversation.created_at >= datetime.combine(
                    start_date, datetime.min.time(), tzinfo=timezone.utc,
                )
            )
        if date_to:
            parsed_end_date = date.fromisoformat(date_to)
            if parsed_end_date.isoformat() != date_to:
                raise ValueError("Date must use YYYY-MM-DD.")
            end_date = parsed_end_date + timedelta(days=1)
            query = query.filter(
                Conversation.created_at < datetime.combine(
                    end_date, datetime.min.time(), tzinfo=timezone.utc,
                )
            )
    except ValueError:
        return jsonify({"error": {"code": "invalid_date", "message": "Use YYYY-MM-DD for date filters."}}), 400
    pagination = query.order_by(Conversation.last_activity.desc()).paginate(
        page=page, per_page=20, error_out=False,
    )
    return jsonify({
        "conversations": [
            {
                "id": item.id,
                "created_at": item.created_at.isoformat(),
                "last_activity": item.last_activity.isoformat(),
                "message_count": len(item.messages),
                "preview": next((message.content for message in reversed(item.messages) if message.role == "user"), ""),
            }
            for item in pagination.items
        ],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
    })


@admin_api_bp.get("/conversations.csv")
@admin_required
def export_conversations():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["conversation_id", "created_at", "last_activity", "role", "intent", "message", "timestamp"])

    def safe_cell(value):
        text = str(value)
        if text.startswith(("=", "+", "-", "@", "\t", "\r")):
            return f"'{text}"
        return text

    for conversation in Conversation.query.order_by(Conversation.created_at.desc()).limit(5000):
        for message in conversation.messages:
            writer.writerow([
                conversation.id, conversation.created_at.isoformat(),
                conversation.last_activity.isoformat(), message.role, message.intent or "",
                safe_cell(message.content), message.created_at.isoformat(),
            ])
    return Response(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=intellibot-conversations.csv"},
    )
