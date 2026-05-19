# AI-Based Volunteer Matching System

A Streamlit-based Final Year Project that connects volunteers with NGOs through an explainable matching engine, optional ML enhancement, Groq-powered AI explanations, OCR-assisted document review, notifications, and admin analytics.

## Project Overview

The system supports three roles: Volunteers, NGOs, and Admins. Volunteers create profiles and apply for suitable opportunities. NGOs create events and manage applications. Admins verify NGOs/documents, monitor activity, and review analytics.

The core recommendation logic remains deterministic and explainable. ML and AI layers are assistive only and never override the deterministic score or manual admin decisions.

## Key Features

- Role-based authentication
- Volunteer profile management
- NGO verification workflow
- Event/opportunity management
- Deterministic volunteer-event matching
- ML-enhanced secondary score
- Application and feedback workflows
- Groq AI explanations and summaries
- OCR-assisted document intelligence
- In-app notification center
- Advanced admin analytics
- Streamlit Cloud deployment readiness

## User Roles

| Role | Main Capabilities |
|---|---|
| Volunteer | Manage profile, upload documents, view recommendations, apply to events, track applications, give feedback |
| NGO | Manage organization profile, create events, review applicants, improve event descriptions with AI |
| Admin | Verify NGOs/documents/events, review profiles, run OCR/AI summaries, view analytics and system health |

## Tech Stack

- Python
- Streamlit
- SQLite
- pandas / numpy
- scikit-learn / joblib
- Groq API for optional AI explanations
- pytesseract, Pillow, pdfplumber, PyMuPDF for OCR/document processing
- passlib/bcrypt for password hashing

## Folder Structure

```text
volunteer_matching/
├── ai/                  # Groq client, prompts, AI services
├── analytics/           # Advanced analytics and insights
├── applications/        # Application workflow services
├── auth/                # Authentication logic
├── data/                # SQLite DB, datasets, ML models
├── db/                  # Database connection and schema
├── documents/           # OCR and document analysis
├── events/              # Event management
├── feedback/            # Feedback services
├── matching/            # Deterministic matching engine
├── ml/                  # ML enhancement layer
├── notifications/       # In-app notifications and optional email wrapper
├── pages/               # Streamlit multipage UI
├── scripts/             # Demo seed, reset, health check
├── ui/                  # Reusable UI components/styles
├── uploads/             # Runtime uploads, ignored except .gitkeep
├── utils/               # Config, session, formatting helpers
├── app.py               # Streamlit entry point
├── requirements.txt
├── packages.txt
└── DEPLOYMENT.md
```

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env    # macOS/Linux
```

Add your Groq key to `.env` only if you want AI features enabled:

```env
GROQ_API_KEY=gsk_your_key_here
```

The app also works without Groq. AI sections will show safe fallback messages.

## Running the App

```bash
streamlit run app.py
```

## Demo Accounts

Run the seed script first:

```bash
python scripts/seed_demo_data.py
```

| Role | Email | Password |
|---|---|---|
| Admin | admin@volmatch.local | Admin@123 |
| Volunteer | volunteer@volmatch.local | Volunteer@123 |
| NGO | ngo@volmatch.local | Ngo@123 |

## Demo Data

The seed script creates:

- demo admin, volunteer, and NGO accounts
- verified volunteer profile
- approved NGO profile
- approved events
- sample application and feedback
- sample match scores
- sample notifications
- sample document metadata

The script is safe to rerun and avoids duplicate accounts.

## Dataset and ML Explanation

The deterministic matching system is the primary scoring engine. It uses explainable weighted criteria such as skills, availability, location, interests, experience level, and volunteering mode.

The ML layer is secondary and advisory. It can display additional predictive scores but does not change rankings, approvals, or application decisions.

## Groq AI Explanation Layer

Groq AI is optional and used only for:

- match explanations
- profile improvement suggestions
- event description improvements
- admin summaries
- OCR text summaries

AI outputs are assistive only. They do not approve/reject users, NGOs, documents, or applications.

## OCR Notes

OCR uses free local/system libraries:

- pytesseract
- Pillow
- pdfplumber
- PyMuPDF

For local Windows development, install Tesseract separately and make sure it is available in PATH.

For Streamlit Community Cloud, `packages.txt` includes:

```text
tesseract-ocr
tesseract-ocr-eng
poppler-utils
```

OCR is assistive only. Admin verification remains manual.

## Health Check

```bash
python scripts/health_check.py
```

The health check verifies database access, required tables, runtime folders, demo accounts, Groq configuration, OCR binary availability, and important Python packages.

## Reset Demo Database

```bash
python scripts/reset_demo_database.py
```

For non-interactive reset:

```bash
python scripts/reset_demo_database.py --force
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for GitHub and Streamlit Community Cloud deployment steps.

## Screenshots

Add final report screenshots here:

- Landing page
- Volunteer dashboard
- Recommendations page
- NGO dashboard
- Admin dashboard
- OCR document review
- Advanced analytics

## Academic Summary

This project demonstrates a complete explainable AI-based volunteer matching workflow. The system combines deterministic scoring, ML enhancement, LLM-powered explanations, OCR-assisted document intelligence, notification workflows, and analytics dashboards while preserving transparency, modularity, and admin control.

## Final QA and Submission Evidence

Phase 16 adds final QA documentation and validation tools for submission readiness.

### Run Final Smoke Test

```bash
python scripts/smoke_test.py
```

This checks required files, pages, imports, database schema, demo accounts, runtime folders, and optional integrations such as Groq, OCR, and ML models.

### Generate Submission Summary

```bash
python scripts/generate_submission_summary.py
```

This creates:

```text
qa/submission_summary.md
```

The generated summary can be used in the final report appendix or supervisor submission.

### QA Documents

```text
qa/test_plan.md              # Full functional test cases
qa/bug_report.md             # Known/fixed issue tracking
qa/submission_checklist.md   # Final submission checklist
qa/demo_script.md            # Step-by-step viva/demo script
```

## Limitations

- SQLite is appropriate for FYP/demo scale but should be replaced by PostgreSQL/MySQL for high-concurrency production deployment.
- OCR accuracy depends on scan quality and the availability of Tesseract system packages.
- Groq AI features require a valid API key for live responses, but the app remains usable without it.
- ML enhancement depends on the quality and availability of the training dataset and saved model.
- Email infrastructure is prepared as a placeholder but is not enabled by default.

## Future Work

- Add optional SMTP email notifications.
- Improve dataset size and quality for stronger ML evaluation.
- Add exportable PDF/CSV reports for analytics.
- Migrate SQLite to a cloud-hosted relational database.
- Add stronger document validation controls while preserving manual admin review.

## Final Demo Checklist

1. Run `python scripts/seed_demo_data.py`.
2. Run `python scripts/health_check.py`.
3. Run `python scripts/smoke_test.py`.
4. Start the app with `streamlit run app.py`.
5. Login as admin, volunteer, and NGO.
6. Capture screenshots for the final report.
7. Complete `qa/submission_checklist.md`.

## ML Dependency Note

The ML Evaluation page requires `joblib` and `scikit-learn`. Install all project dependencies with:

```bash
pip install -r requirements.txt
```

If the ML page reports missing dependencies, run:

```bash
pip install joblib scikit-learn
```

The app is designed to show a clean warning instead of a raw traceback if optional ML dependencies are missing.

## Session Refresh Note

The app uses a random session token stored in the URL query parameters and validated against the local SQLite `Sessions` table. This improves demo stability across browser refreshes without storing passwords or password hashes in the browser. Logout deactivates the token and clears the query parameter.
