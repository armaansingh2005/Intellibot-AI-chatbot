"""Build safe, policy-grounded chatbot replies."""


class ResponseManager:
    CONFIDENCE_THRESHOLD = 0.14
    SUGGESTIONS = [
        "What are your delivery options?",
        "What is your return policy?",
        "How can I contact support?",
    ]

    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base

    def respond(self, text: str, intent: str, confidence: float, context_reply: str | None = None) -> tuple[str, str]:
        if context_reply == "shipping_followup":
            faq = self.knowledge_base.answer("delivery time shipping duration", "shipping")
            if faq:
                return faq["answer"], intent
        if context_reply == "shipping_cost_followup":
            faq = self.knowledge_base.answer("delivery cost shipping price", "shipping")
            if faq:
                return faq["answer"], intent
        if confidence < self.CONFIDENCE_THRESHOLD or intent == "unknown":
            return (
                "I’m not quite sure I understood that. You could ask about delivery, returns, payments, or contact options.",
                "fallback",
            )
        direct = {
            "greeting": "Hello! I’m IntelliBot, your support assistant. What can I help you with?",
            "goodbye": "Goodbye! If another question comes up, I’m here to help.",
            "gratitude": "You’re welcome! Is there anything else I can help with?",
            "bot_identity": "I’m IntelliBot, an automated customer-support assistant. I can help with common questions about our services and policies.",
            "general_help": "I can help with product information, pricing, delivery, returns, payments, accounts, or support. What would you like to know?",
            "order_status": "I can’t access live order records here. Please check your order confirmation or contact support with your order number.",
            "human_agent": "I can’t transfer chats directly, but our team can help through the contact options listed in our support information.",
            "complaint": "I’m sorry this hasn’t gone smoothly. Please contact our support team with a brief description of the issue so they can review it.",
            "technical_support": "Try refreshing the page and checking your connection. If the issue continues, contact support and include the steps that led to it.",
            "business_hours": "Our support team is available Monday through Friday, 9:00 AM–5:00 PM local time.",
            "contact": "You can reach our support team at support@example.com, Monday through Friday, 9:00 AM–5:00 PM local time.",
            "account": "For account help, use the account settings page to update your details or reset your password. Never share your password with support.",
        }
        if intent in direct:
            return direct[intent], intent
        faq = self.knowledge_base.answer(text, intent)
        if faq:
            return faq["answer"], intent
        return (
            "I don’t have a verified answer for that yet. Please contact support@example.com and our team can help.",
            "fallback",
        )
