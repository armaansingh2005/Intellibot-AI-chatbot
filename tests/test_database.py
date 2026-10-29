"""Database model operations."""

from models import Conversation, Message, db


def test_conversation_cascades_message_deletion(app):
    with app.app_context():
        conversation = Conversation(owner_id="owner")
        conversation.messages.append(Message(role="user", content="hello"))
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
        assert Message.query.count() == 1
        db.session.delete(db.session.get(Conversation, conversation_id))
        db.session.commit()
        assert Message.query.count() == 0
