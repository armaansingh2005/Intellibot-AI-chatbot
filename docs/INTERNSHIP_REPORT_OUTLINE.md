# IntelliBot AI — Internship Project Report Outline

> Complete the bracketed fields using verified project and internship details. Do not infer company or internship information, and report only metrics actually measured.

## Abstract

Summarize the customer-support problem, the offline-first chatbot approach, the implementation, how it was evaluated, and the principal measured results. State the evaluation dataset and limitations.

## 1. Introduction

- Background on repetitive customer-support enquiries.
- Motivation for a lightweight, locally runnable conversational support tool.
- Scope of the project and intended users.
- Internship context: `[institution / organization / dates — fill only if applicable]`.

## 2. Problem statement

Describe the specific support workflow or information-access problem addressed. Distinguish the demonstrated sample application from any deployed business system.

## 3. Objectives

- Recognize common support intents using a local NLP baseline.
- Answer supported policy questions using a configurable FAQ source.
- Maintain short-term context and persistent conversation records.
- Provide administrative visibility into conversations and unanswered questions.
- Evaluate the implementation with automated tests and held-out model data.

## 4. Existing system

Document the existing process, tools, and evidenced limitations relevant to the project. If no real organization workflow was studied, label this section as a general background rather than claiming observed facts.

## 5. Proposed system

Describe the intended user flow, supported intents, FAQ retrieval, fallback behavior, context rules, history, administration, and trust/safety boundaries.

## 6. Requirements analysis

### Functional requirements

Chat, intent prediction, FAQ retrieval, contextual follow-ups, history, ownership checks, administrator authentication, analytics, search, pagination, and CSV export.

### Non-functional requirements

Local operation without paid AI services, responsive layout, safe input/output handling, maintainable modularity, persistence, and testability.

### Tools and technologies

Python, Flask, SQLAlchemy, SQLite, NLTK, scikit-learn, HTML/CSS/JavaScript, Chart.js, pytest, and the actual development environment used.

## 7. System architecture

Include a labeled architecture diagram showing browser, Flask routes, NLP services, FAQ/intent data, ORM models, and SQLite. Explain trust boundaries and which parts require network access (Chart.js CDN).

## 8. Methodology

- Intent dataset design and validation.
- Text normalization/tokenization and TF-IDF features.
- Stratified holdout split, seed, classifier, and evaluation metrics.
- FAQ retrieval and confidence threshold.
- Explicit context interpretation and expiry.
- Database schema and conversation ownership approach.
- Security and privacy considerations.

## 9. Implementation

Describe modules and their responsibilities. Include representative UI screenshots and API examples only after capturing them from a running version. Identify sample policies/contact details as placeholders.

## 10. Testing

Record the Python/dependency versions, command run, test count, pass/fail status, and any limitations. Include test coverage for APIs, conversation isolation, database behavior, NLP fallback, and admin authorization.

## 11. Results and discussion

Report actual output from `python scripts/train_model.py` and `pytest -q`. State evaluation set size and discuss class-wise errors, small-dataset uncertainty, and the difference between classification scores and real customer-support quality. Do not insert estimated or fabricated results.

## 12. Limitations

Discuss the small curated dataset, bag-of-words model, uncalibrated confidence, explicit rather than general context handling, sample FAQ policies, lack of live integrations, anonymous browser-session identity, in-memory rate limiting, SQLite deployment constraints, and CDN chart dependency.

## 13. Future scope

Describe selected next steps with practical dependencies: reviewed FAQ administration, feedback, representative datasets, multilingual testing, calibrated abstention, ticketing integration, user accounts, shared rate limiting, and persistent production infrastructure.

## 14. Conclusion

Summarize what was implemented and verified, what remains a prototype, and the most important next step.

## References

Add the actual documentation, textbooks, papers, and package references used. Suggested official references to verify and cite:

- Flask documentation: <https://flask.palletsprojects.com/>
- Flask-SQLAlchemy documentation: <https://flask-sqlalchemy.palletsprojects.com/>
- scikit-learn documentation: <https://scikit-learn.org/stable/>
- NLTK documentation: <https://www.nltk.org/>
- OWASP Cheat Sheet Series: <https://cheatsheetseries.owasp.org/>
