"""Small, explicit follow-up rules backed by recent conversation messages."""

from datetime import datetime, timezone


class ContextManager:
    CONTEXT_TTL_SECONDS = 2 * 60 * 60

    def interpret(self, text: str, predicted_intent: str, messages: list) -> tuple[str, str | None]:
        if not messages:
            return predicted_intent, None
        latest = messages[-1]
        activity = latest.created_at
        if activity.tzinfo is None:
            activity = activity.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - activity).total_seconds() > self.CONTEXT_TTL_SECONDS:
            return predicted_intent, None
        query = text.lower().strip().rstrip("?.! ")
        previous_intent = latest.intent
        if previous_intent in {"shipping", "delivery"}:
            if any(phrase in query for phrase in ("how much", "what does delivery cost", "delivery price")):
                return "shipping", "shipping_cost_followup"
            if any(phrase in query for phrase in ("how long", "when will", "delivery time")):
                return "shipping", "shipping_followup"
        return predicted_intent, None
