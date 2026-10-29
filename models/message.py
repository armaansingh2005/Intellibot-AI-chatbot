"""Chat message persistence model."""

from datetime import datetime, timezone

from models.database import db


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role = db.Column(db.String(16), nullable=False)
    content = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(64))
    confidence = db.Column(db.Float)
    response_time_ms = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    conversation = db.relationship("Conversation", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "confidence": self.confidence,
            "response_time_ms": self.response_time_ms,
            "created_at": self.created_at.isoformat(),
        }
