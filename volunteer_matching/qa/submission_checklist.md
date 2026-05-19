# Final Submission Checklist

## Code and Repository

- [ ] Project opens in a fresh virtual environment.
- [ ] `pip install -r requirements.txt` completes successfully.
- [ ] App starts with `streamlit run app.py`.
- [ ] No real API keys are committed.
- [ ] `.env` is ignored by Git.
- [ ] `.streamlit/secrets.toml` is ignored by Git.
- [ ] `.env.example` is included.
- [ ] `.streamlit/secrets.toml.example` is included.
- [ ] `uploads/.gitkeep` is included, but user uploads are ignored.

## Database and Demo Data

- [ ] Database initializes successfully.
- [ ] `python scripts/seed_demo_data.py` runs successfully.
- [ ] Demo admin account works.
- [ ] Demo volunteer account works.
- [ ] Demo NGO account works.
- [ ] Demo events, applications, feedback, notifications, and match scores exist.

## Functional Testing

- [ ] Authentication tested for admin, volunteer, and NGO.
- [ ] Volunteer profile flow tested.
- [ ] NGO profile and event flow tested.
- [ ] Admin verification workflows tested.
- [ ] Recommendations tested.
- [ ] Applications tested.
- [ ] Feedback tested.
- [ ] Notifications tested.
- [ ] OCR document workflow tested or fallback confirmed.
- [ ] Groq AI fallback tested without API key.
- [ ] Groq AI live response tested with API key, if available.
- [ ] Advanced Analytics page loads.
- [ ] Evaluation and ML Evaluation pages load.

## Evidence and Documentation

- [ ] README finalized.
- [ ] DEPLOYMENT guide finalized.
- [ ] QA test plan included.
- [ ] Bug report included.
- [ ] Demo script included.
- [ ] Submission summary generated using `python scripts/generate_submission_summary.py`.
- [ ] Screenshots captured for report.
- [ ] Dataset included or explained.
- [ ] ML model included or training instructions explained.
- [ ] Limitations and future work documented.

## Deployment

- [ ] GitHub repository cleaned.
- [ ] Streamlit Cloud app connected.
- [ ] Streamlit secrets configured if Groq AI is demonstrated.
- [ ] OCR system packages configured through `packages.txt`.
- [ ] Deployed app starts successfully.
- [ ] Deployed app tested with demo accounts.

## Viva / Supervisor Demo

- [ ] Demo script practiced.
- [ ] Project problem statement prepared.
- [ ] Deterministic matching explanation prepared.
- [ ] ML enhancement explanation prepared.
- [ ] AI/OCR limitations prepared.
- [ ] Final benefits and future improvements prepared.
