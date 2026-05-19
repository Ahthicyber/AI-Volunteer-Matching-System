# Submission Summary — AI-Based Volunteer Matching System

Generated: 2026-05-14 17:10

## Project Title

AI-Based Volunteer Matching System

## Technology Stack

- Python
- Streamlit
- SQLite
- pandas / numpy
- scikit-learn / joblib
- Groq API for optional AI explanations and summaries
- pytesseract, Pillow, pdfplumber, PyMuPDF for OCR-assisted document review
- passlib/bcrypt for password hashing

## Implemented Features

- Role-based authentication for Volunteers, NGOs, and Admins
- Volunteer profile management with verification status
- NGO profile workflow with admin approval/rejection
- Event/opportunity creation and moderation
- Deterministic volunteer-event recommendation engine
- Optional ML enhancement layer displayed separately
- Applications workflow with accept/reject/cancel status handling
- Feedback and rating workflow
- Groq AI match explanations, profile suggestions, event improvements, and admin summaries
- OCR-assisted document intelligence with manual admin verification
- In-app notification center and communication history
- Advanced analytics and evaluation dashboards
- Deployment-ready configuration for local use and Streamlit Community Cloud

## User Roles

| Role | Main Workflow |
|---|---|
| Admin | Verify NGOs, events, documents, volunteers; review analytics; monitor system health |
| Volunteer | Create profile, upload documents, receive recommendations, apply to events, give feedback |
| NGO | Create organization profile, post events, manage applicants, review feedback |

## Deterministic Matching Explanation

The deterministic matching engine remains the primary recommendation mechanism. It uses explainable weighted criteria such as skills, availability, location, interests, experience level, and volunteering mode. This keeps recommendations transparent, auditable, and suitable for academic defense.

## ML Enhancement Explanation

The ML layer is secondary and advisory. It can display additional predictive scores where a trained model is available, but it does not change ranking, application decisions, or admin approvals.

## Groq AI Explanation

Groq AI is optional and assistive only. It is used to generate readable explanations, suggestions, summaries, and OCR content summaries. The app continues to run without a Groq key by showing safe fallback messages.

## OCR / Document Intelligence Explanation

OCR extracts text from supported PDF/JPG/PNG uploads and stores extracted text for admin review. AI summaries may summarize extracted text, but OCR and AI do not verify authenticity or approve/reject documents. Admin verification remains manual.

## Evaluation Metrics Snapshot

| Table | Current Count |
|---|---:|
| Users | Not available |
| VolunteerProfiles | Not available |
| NGOProfiles | Not available |
| Events | Not available |
| Applications | Not available |
| Feedback | Not available |
| VolunteerDocuments | Not available |
| Notifications | Not available |

## Deployment Instructions

1. Create a virtual environment.
2. Install requirements using `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` for local configuration.
4. Run `python scripts/seed_demo_data.py` to populate demo data.
5. Start the app using `streamlit run app.py`.
6. For Streamlit Cloud, add secrets using `.streamlit/secrets.toml.example` as a template.

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@volmatch.local | Admin@123 |
| Volunteer | volunteer@volmatch.local | Volunteer@123 |
| NGO | ngo@volmatch.local | Ngo@123 |

## Limitations

- SQLite is suitable for FYP/demo scale but not high-concurrency production traffic.
- OCR accuracy depends on file quality and local/system Tesseract availability.
- Groq AI is optional and requires a valid API key for live responses.
- ML enhancement depends on the availability and quality of training data.

## Future Work

- Email notifications with SMTP configuration
- More robust model training/evaluation pipeline
- Cloud database migration for production-scale deployment
- Improved document verification workflows with stronger validation controls
- More advanced reporting/export features
