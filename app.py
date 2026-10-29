"""Flask application factory and local CLI commands."""

import os
from getpass import getpass
from pathlib import Path

import click
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect

from chatbot.nlp_engine import NLPEngine
from config import Config
from models import Admin, db
from routes.admin_routes import admin_api_bp, admin_bp
from routes.chat_routes import chat_bp

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp)
    app.view_functions["admin.login"] = limiter.limit("5 per minute", methods=["POST"])(
        app.view_functions["admin.login"]
    )

    app.extensions["nlp_engine"] = NLPEngine(
        app.config["MODEL_PATH"], app.config["INTENTS_PATH"], app.config["FAQ_PATH"],
    )

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": {"code": "not_found", "message": "Resource not found."}}), 404
        return render_template("404.html"), 404

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": {"code": "csrf_failed", "message": "Refresh the page and try again."}}), 400
        return render_template("400.html"), 400

    @app.errorhandler(413)
    def payload_too_large(_error):
        return jsonify({"error": {"code": "request_too_large", "message": "Request is too large."}}), 413

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        app.logger.exception("Unhandled application error.")
        if request.path.startswith("/api/"):
            return jsonify({"error": {"code": "internal_error", "message": "An unexpected error occurred."}}), 500
        return render_template("500.html"), 500

    @app.cli.command("init-db")
    def init_db():
        """Create the database tables."""
        with app.app_context():
            db.create_all()
        click.echo("Database tables are ready.")

    @app.cli.command("create-admin")
    @click.option("--username", default=None, help="Administrator username.")
    def create_admin(username):
        """Create the first administrator using a securely hashed password."""
        username = (username or app.config["ADMIN_USERNAME"]).strip()
        if not username or len(username) > 80:
            raise click.ClickException("Username must contain 1–80 characters.")
        with app.app_context():
            if Admin.query.filter_by(username=username).first():
                raise click.ClickException(f"Administrator {username!r} already exists.")
            password = getpass("New administrator password (12+ characters): ")
            confirm = getpass("Confirm password: ")
            if password != confirm or len(password) < 12:
                raise click.ClickException("Passwords must match and be at least 12 characters.")
            admin = Admin(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
        click.echo(f"Administrator {username!r} created.")

    @app.cli.command("run-local")
    def run_local():
        """Run the Flask development server for local use only."""
        app.run(
            host="127.0.0.1", port=int(os.getenv("PORT", "5000")),
            debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        )

    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1", port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
