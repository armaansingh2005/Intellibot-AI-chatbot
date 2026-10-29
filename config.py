"""Application configuration."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///intellibot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30
    WTF_CSRF_TIME_LIMIT = 60 * 60 * 24
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    MODEL_PATH = BASE_DIR / "instance" / "models" / "intent_classifier.joblib"
    INTENTS_PATH = BASE_DIR / "data" / "intents.json"
    FAQ_PATH = BASE_DIR / "data" / "faqs.json"


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-only-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    RATELIMIT_ENABLED = False
