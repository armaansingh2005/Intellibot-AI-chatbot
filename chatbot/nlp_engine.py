"""Facade for intent classification, contextual interpretation, and replies."""

from chatbot.context_manager import ContextManager
from chatbot.intent_classifier import IntentClassifier
from chatbot.knowledge_base import KnowledgeBase
from chatbot.response_manager import ResponseManager


class NLPEngine:
    def __init__(self, model_path, intents_path, faq_path):
        self.classifier = IntentClassifier(model_path, intents_path)
        self.knowledge_base = KnowledgeBase(faq_path)
        self.context = ContextManager()
        self.responses = ResponseManager(self.knowledge_base)

    def process(self, text: str, recent_messages: list) -> dict:
        predicted_intent, confidence = self.classifier.predict(text)
        intent, context_reply = self.context.interpret(text, predicted_intent, recent_messages)
        response, response_intent = self.responses.respond(
            text, intent, confidence, context_reply,
        )
        return {
            "response": response,
            "intent": response_intent,
            "predicted_intent": intent,
            "confidence": confidence,
            "suggestions": self.responses.SUGGESTIONS,
        }
