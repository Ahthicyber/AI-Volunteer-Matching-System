# Deployment Guide — AI-Based Volunteer Matching System

This guide prepares the project for GitHub and Streamlit Community Cloud deployment.

## 1. GitHub Setup

1. Ensure your real `.env` file is not committed.
2. Confirm `.gitignore` includes `.env`, real database files, uploads, cached model files, and `.streamlit/secrets.toml`.
3. Commit only example configuration files:
   - `.env.example`
   - `.streamlit/secrets.toml.example`
4. Push the project to GitHub.

## 2. Local Verification Before Deployment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_demo_data.py
python scripts/health_check.py
streamlit run app.py
```

## 3. Streamlit Community Cloud Deployment

1. Open Streamlit Community Cloud.
2. Create a new app from your GitHub repository.
3. Select the branch and `app.py` as the main file.
4. Deploy.

Streamlit will install Python dependencies from `requirements.txt` and system packages from `packages.txt`.

## 4. Secrets Setup

In Streamlit Cloud, open app settings and add secrets:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

Optional future placeholders:

```toml
SMTP_HOST = ""
SMTP_PORT = ""
SMTP_USER = ""
SMTP_PASSWORD = ""
```

The app works without Groq; AI features will show fallback messages.

## 5. OCR Packages Setup

`packages.txt` includes:

```text
tesseract-ocr
tesseract-ocr-eng
poppler-utils
```

These packages support OCR on Streamlit Cloud. If OCR still fails, run `python scripts/health_check.py` locally and check the deployment logs in Streamlit Cloud.

## 6. Dataset and Model Notes

- Keep datasets in `data/dataset/`.
- Runtime or cached models in `data/models/` are ignored by default.
- Missing ML models must not crash the app; the system should fall back to deterministic recommendations.

## 7. SQLite Limitations

SQLite is suitable for final-year demos and lightweight deployments. On Streamlit Cloud, the filesystem can be reset during redeploys or app restarts. For production-scale use, migrate to a managed database such as PostgreSQL.

## 8. Demo Data

Seed demo data locally:

```bash
python scripts/seed_demo_data.py
```

Reset demo database:

```bash
python scripts/reset_demo_database.py --force
```

Demo accounts:

| Role | Email | Password |
|---|---|---|
| Admin | admin@volmatch.local | Admin@123 |
| Volunteer | volunteer@volmatch.local | Volunteer@123 |
| NGO | ngo@volmatch.local | Ngo@123 |

## 9. Troubleshooting

### Groq key not detected

- Check `.env` locally or Streamlit Cloud Secrets.
- Use `GROQ_API_KEY=gsk_...` with no spaces around `=`.
- Run:

```bash
python -c "from utils.config import get_groq_api_key; print(bool(get_groq_api_key()))"
```

### OCR unavailable

- Local Windows: install Tesseract separately and add it to PATH.
- Streamlit Cloud: confirm `packages.txt` exists.
- OCR failures should not crash the app.

### Database errors

Run:

```bash
python scripts/health_check.py
```

Then reset demo data if needed:

```bash
python scripts/reset_demo_database.py --force
```

### App starts but pages are empty

Run seed data and login with demo accounts.

## 10. Final Demo Checklist

- App opens with `streamlit run app.py`.
- Demo accounts can log in.
- Volunteer recommendations render.
- NGO event/application workflow works.
- Admin verification screens load.
- OCR buttons fail gracefully if Tesseract is missing.
- Groq AI works if key is configured and falls back safely if missing.
- Notifications appear in sidebar.
- Advanced Analytics page loads for admin only.
- No real secrets are committed.
