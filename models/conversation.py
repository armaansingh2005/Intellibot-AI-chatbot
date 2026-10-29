"""Conversation persistence model."""

from datetime import datetime, timezone

from models.database import db


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_activity = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    messages = db.relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def to_dict(self, include_messages: bool = False) -> dict:
        result = {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.messages),
        }
        if include_messages:
            result["messages"] = [message.to_dict() for message in self.messages]
        return result
