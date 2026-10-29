# IntelliBot AI

An offline-first customer-support chatbot portfolio project. IntelliBot uses a scikit-learn TF-IDF/logistic-regression intent classifier, configurable FAQ retrieval, explicitly limited short-term context, SQLite-backed conversations, and a password-protected analytics dashboard.

> **Sample business data:** the policies and `support@example.com` contact in `data/faqs.json` and the response manager are illustrative. Replace them with approved business content before presenting this as a real support channel.

## Quick start (Windows PowerShell)

From the project directory, create the environment, install dependencies, and prepare local configuration:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `SECRET_KEY` in `.env`, then initialize the database and start the development server:

```powershell
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000`. See [Installation and environment](#6-installation-and-environment) for macOS/Linux instructions, admin setup, and deployment notes.

## What this project demonstrates

- A complete Flask application with browser chat, JSON APIs, conversation history, and an administrator dashboard.
- A reproducible scikit-learn text-classification baseline paired with configurable FAQ retrieval and explicit safe fallbacks.
- Practical application engineering: CSRF protection, password hashing, rate limiting, access checks, SQLite persistence, and automated tests.
- Evaluation and project-report documentation that distinguishes measured results from illustrative data and known limitations.

This is an educational portfolio project, not a production customer-support service. It does not connect to live orders, payments, or support agents.

## 1. Project overview

Small support teams receive repeat questions about products, delivery, returns, payments, and account access. IntelliBot demonstrates how a local NLP baseline can recognize a curated set of common intents, retrieve approved FAQ text, retain recent conversation history, and expose unanswered questions for review—without a paid AI API.

### Objectives and key features

- Classify 19 supported intents with a reproducible TF-IDF and logistic-regression pipeline.
- Retrieve configurable, intent-scoped FAQs and use a confidence threshold plus a safe fallback.
- Persist conversations and messages in SQLite; support same-browser history and conversation deletion.
- Apply narrow, documented follow-up rules with a two-hour context lifetime.
- Provide an authenticated admin dashboard with live KPIs, charts, search, pagination, transcript views, fallback questions, and CSV export.
- Switch between accessible light and dark themes, with system-preference detection and a saved browser preference.
- Protect browser POST requests with CSRF, hash administrator passwords, limit login attempts, validate inputs, and enforce conversation ownership.
- Deliver a responsive, accessible chat experience with timestamps, typing feedback, suggested prompts, and safe text rendering.

## 2. Technology stack

Python 3.11+ (verified during development with Python 3.12.10), Flask, Flask-SQLAlchemy / SQLAlchemy, SQLite, Werkzeug password hashing, Flask-WTF CSRF, Flask-Limiter, NLTK's resource-free `RegexpTokenizer`, scikit-learn, joblib, pytest, HTML, custom CSS, JavaScript, and Chart.js.

## 3. Architecture

```text
Browser ── HTML / CSS / JavaScript ── Flask routes
   │          CSRF token + signed session      │
   ├── Chat / history API ── NLP facade ── intent classifier
   │                              ├────────── FAQ retrieval
   │                              └────────── follow-up rules
   └── Admin UI / API ─────────── SQLAlchemy ── SQLite
                                      └──────── intents / FAQ JSON
```

- `app.py` creates the Flask application, installs extensions, registers routes, and defines database/admin CLI commands.
- `chatbot/` contains the classifier, FAQ retrieval, context rules, and response selection.
- `models/` defines conversations, messages, and administrators.
- `routes/` contains user-facing and administrator endpoints.
- `data/` separates editable sample intent and FAQ data from implementation.
- The application loads a saved local model when present. If absent or unreadable, it trains an in-memory model from the bundled examples; it does not retrain per request.

## 4. Project structure

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── .editorconfig
├── .gitattributes
├── .gitignore
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── SUPPORT.md
├── app.py
├── config.py
├── wsgi.py
├── requirements.txt
├── .env.example
├── README.md
├── chatbot/
├── data/
├── docs/
│   └── INTERNSHIP_REPORT_OUTLINE.md
├── models/
├── routes/
├── scripts/
├── static/
│   ├── css/
│   └── js/
├── templates/
└── tests/
```

## 5. Prerequisites

- Python 3.11 or later (3.12 recommended).
- Git, optionally, to manage a project repository.
- A modern browser. Chart.js is loaded from jsDelivr for the admin charts; the rest of the application and NLP model run locally.

## 6. Installation and environment

From the project directory, create and activate a virtual environment.

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set a unique secret key. Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set `SECRET_KEY` to that output. `SESSION_COOKIE_SECURE=false` is suitable only for local HTTP development; set it to `true` behind HTTPS. Configuration is read from environment variables / `.env`. Never commit `.env`.

## 7. Database initialization

The default SQLite database is `instance/intellibot.db`; the `instance/` directory is created automatically and local database files are ignored by Git.

```bash
flask --app app init-db
```

## 8. Train and evaluate the intent model

```bash
python scripts/train_model.py
```

The script validates `data/intents.json`, performs a reproducible stratified 75/25 holdout split, prints observed accuracy / precision / recall / F1, then fits the production artifact on all examples at `instance/models/intent_classifier.joblib`. Retrain after changing the intent patterns. This is a small, curated demonstration dataset: its holdout metrics are not a substitute for evaluation on representative, independently collected production queries. The response confidence threshold is 0.14; confidence is not calibrated and should be re-evaluated against representative data before changing this value.

Without that artifact, startup validates and fits the same bundled examples in memory. The app remains usable if a model file is missing. The saved joblib file should only be loaded from a trusted source.

## 9. Create an administrator

Initialize the database first, then run:

```bash
flask --app app create-admin --username admin
```

The command prompts for a password without echoing it, requires at least 12 characters, and stores a Werkzeug password hash. There is no default admin account or hard-coded password. `ADMIN_USERNAME` in `.env` is the default CLI username when `--username` is omitted.

Open `/admin/login` to sign in. The login endpoint allows five attempts per minute per remote address using the in-process Flask-Limiter store. For multiple production workers, configure a shared rate-limit backend and review the deployment security model.

## 10. Run the application

Local development:

```bash
flask --app app run --host 127.0.0.1 --port 5000
```

Then visit `http://127.0.0.1:5000`. `python app.py` is also available for local development. Do not use Flask's development server for production.

Production WSGI example on Linux:

```bash
gunicorn --workers 2 --bind 0.0.0.0:8000 wsgi:app
```

Set `SECRET_KEY`, `DATABASE_URL`, and `SESSION_COOKIE_SECURE=true` in the hosting environment. Use a persistent disk for SQLite, or choose a managed database and configure its SQLAlchemy URL after evaluating operational needs. Hosts with ephemeral filesystems lose SQLite data on restart/redeploy. SQLite here is for local development and small demonstrations; assess backup, concurrency, retention, privacy, and scale requirements before production use.

## 11. Run tests

```bash
pytest -q
```

Tests create an isolated temporary SQLite database and disable browser CSRF enforcement within the test app. They cover startup/health, validation, intent and FAQ replies, safe fallback, contextual follow-up, persistence, session ownership, deletion, admin authentication/authorization, analytics, search, export, and cascade behavior.

## 12. Pages

- `/` — chatbot.
- `/history` — current browser session's conversation list and transcript viewer.
- `/admin/login` — administrator sign-in.
- `/admin/` — analytics and conversation management.
- `/admin/conversations/<id>` — an authorized transcript view.

The dashboard is protected server-side. User conversation IDs are checked against a random owner identifier in the signed browser session, so changing an ID does not grant access. Anonymous history is tied to that browser session; this project does not implement customer accounts or cross-device identity.

The header theme toggle follows the operating-system appearance on first visit and saves a manual choice in browser `localStorage` for later pages and visits. Chat, history, login, and admin screens support both themes.

## 13. REST API

Browser POST requests require the CSRF token in the `X-CSRFToken` header (or as a form token). Responses use JSON error envelopes with an `error.code` and `error.message`; invalid CSRF on API requests returns `400` with `csrf_failed`.

### User endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Basic health status; no secrets are returned. |
| `POST` | `/api/chat` | Process and persist a chat turn. |
| `GET` | `/api/conversations` | List conversations for the current browser session (up to 100). |
| `POST` | `/api/conversations` | Create an empty conversation. |
| `GET` | `/api/conversations/<id>` | Retrieve an owned conversation and its messages. |
| `DELETE` | `/api/conversations/<id>` | Delete an owned conversation and its messages. |

Example chat request:

```json
{"message":"What are your delivery options?","conversation_id":12}
```

`conversation_id` may be omitted to create a conversation automatically. Example success:

```json
{
  "conversation_id": 12,
  "response": "We offer standard delivery, which generally takes 3–5 business days...",
  "intent": "shipping",
  "confidence": 0.81,
  "suggestions": ["What are your delivery options?", "What is your return policy?", "How can I contact support?"],
  "created_at": "2026-01-01T12:00:00+00:00",
  "response_time_ms": 3.2
}
```

Values above are illustrative, not captured evaluation output. Common errors: `400` malformed/empty input, `404` missing or not-owned conversation, `413` oversized payload/message, and `500` internal failure with a generic user-safe message.

### Administrator endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/admin/login` | Authenticate an administrator using form fields `username` and `password`. |
| `POST` | `/admin/logout` | Clear the authenticated session. |
| `GET` | `/api/admin/analytics` | Return database-backed KPI, trend, intent, FAQ, and fallback data. |
| `GET` | `/api/admin/conversations?page=1&q=term&intent=shipping&date_from=2026-01-01&date_to=2026-01-31` | Search/filter paginated conversations (20 per page); dates are inclusive `YYYY-MM-DD` creation dates. |
| `GET` | `/api/admin/conversations.csv` | Export up to 5,000 conversations and their messages. |

Admin APIs return `401` when unauthenticated. CSV exports contain visitor-provided content; treat and share them as private data.

## 14. Example conversations

```text
Visitor: What are your delivery options?
IntelliBot: We offer standard delivery, which generally takes 3–5 business days...
Visitor: How long does it take?
IntelliBot: [Uses the recent delivery topic to retrieve the configured delivery FAQ.]
```

```text
Visitor: Where is my order?
IntelliBot: I can’t access live order records here. Please check your order confirmation...
```

The intent classifier only predicts among the included examples. Follow-up interpretation is a small set of explicit rules, not general reasoning. FAQ retrieval compares TF-IDF text only within the predicted intent and does not establish factual correctness. Review and update policy content before use.

## 15. Model evaluation methodology

Training uses a fixed seed (`42`), a stratified holdout split, and the same word/character TF-IDF plus logistic-regression pipeline for evaluation and final training. The evaluation examples are excluded from fitting the reported split model; the final artifact is then fit on all examples for deployment. In the verified run on Python 3.12.10 with 342 curated examples, the 86-example holdout reported **accuracy 0.8140**, **macro precision 0.85**, **macro recall 0.81**, and **macro F1 0.81** (weighted F1 0.82). These are observed results for this fixed small sample, not a production-quality guarantee; the estimate is noisy and may not generalize.

## 16. Screenshots

Screenshots are not included yet. Add genuine captures of the running application here before using the repository in a presentation; remove any real customer data, credentials, or personal information first.

## 17. Security, privacy, and limitations

- Secrets are environment-based; `.env` is ignored. An ephemeral random development key is used if `SECRET_KEY` is absent, invalidating sessions at restart. Configure a stable secret for all deployed workers.
- Admin credentials use Werkzeug's password hashing. Admin access uses a signed session and all admin views/APIs enforce authorization.
- Forms and JSON browser POSTs use Flask-WTF CSRF protection. Login is rate limited in memory; production multi-worker setups need a shared limiter store.
- User content is rendered with text nodes in JavaScript and autoescaped Jinja templates. Message length is limited to 2,000 characters and the overall request body to 16 KB.
- Conversation history is associated with a signed, random browser-session owner ID, not a login. It is not an identity system and is not suitable for highly sensitive data.
- The bot does not integrate with a live order database, payment provider, ticket system, or human-agent queue. It must not claim live order access.
- The example FAQ/policies/contact information are fictional. No FAQ-management UI or automatic model updates are included.
- The model is a small bag-of-words baseline; intent confidence is not calibrated, and out-of-domain queries can be misclassified.
- Chart.js is fetched from a CDN. Without internet access, the charts may not render; server APIs and the chat remain locally hosted.
- SQLite is intended for local and small demonstrations only. Evaluate persistence, backups, concurrency, privacy, and deployment filesystem behavior before production.

## 18. Troubleshooting

- **`ModuleNotFoundError`:** activate `.venv`, then run `python -m pip install -r requirements.txt`.
- **Admin login fails:** run `flask --app app init-db`, create an account with `flask --app app create-admin`, and ensure the `.env` secret remains stable.
- **Changes to intent examples do not appear:** restart the server; if `instance/models/intent_classifier.joblib` exists, retrain with `python scripts/train_model.py`.
- **Lost conversations after deployment restart:** the hosting filesystem may be ephemeral; attach persistent storage or configure a suitable production database.
- **CSRF error for browser requests:** include the `csrf-token` meta value as the `X-CSRFToken` header.
- **Charts are blank:** check CDN connectivity and browser developer-console errors. The dashboard KPIs and data API are independent of the chart library.

## 19. GitHub setup

This project includes GitHub issue templates, a pull-request template, contribution and security guidance, and a CI workflow. To publish it, create an empty GitHub repository, review the files selected for commit, and then run:

```bash
git add .
git commit -m "Build IntelliBot AI support chatbot"
git branch -M main
git remote add origin https://github.com/<your-account>/<your-repository>.git
git push -u origin main
```

Review `git status` and the staged diff before committing or pushing. `.env`, SQLite databases, and generated model artifacts are excluded by `.gitignore`; never force-add them. This workspace has not been connected to a remote or published.

## 20. Internship-project report

See [docs/INTERNSHIP_REPORT_OUTLINE.md](docs/INTERNSHIP_REPORT_OUTLINE.md) for a fill-in outline. It intentionally does not assume an institution, company, internship outcome, or unmeasured result.

## 21. Future enhancements

Consider user accounts and account recovery, reviewed FAQ management, feedback collection, multilingual evaluation, improved/curated training examples, calibrated confidence, a human-support ticket integration, background analytics aggregation, shared production rate limiting, persistent production database deployment, and accessibility/usability testing.

## 22. License

No open-source license is included. Ask the project owner before reusing or distributing this work.
