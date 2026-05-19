# Bug Report — AI-Based Volunteer Matching System

## QA Status Summary

| Category | Status | Notes |
|---|---|---|
| Static compilation | Fixed/Validated | Project files compile with Python compile checks. |
| Required folders | Fixed/Validated | Runtime folders and QA folders are present. |
| Missing dependencies | Watch item | Optional OCR/Groq packages may be warnings depending on environment. |
| Streamlit routing | Validated | Pages remain in the existing Streamlit multipage structure. |
| Deterministic scoring | No change | Matching weights and ranking logic were not modified. |
| ML logic | No change | ML enhancement remains secondary and optional. |
| AI fallback | Validated by design | Missing Groq key returns safe fallback messages. |
| OCR fallback | Validated by design | Missing Tesseract or OCR failure is handled gracefully. |

## Fixed Issues

| ID | Severity | Issue | Resolution | Status |
|---|---|---|---|---|
| BUG-001 | Medium | Potential missing QA evidence for final submission | Added structured QA folder with test plan, bug report, checklist, and demo script | Fixed |
| BUG-002 | Medium | No single smoke-test command for final validation | Added `scripts/smoke_test.py` with file, import, schema, folder, and optional integration checks | Fixed |
| BUG-003 | Low | No generated submission summary artifact | Added `scripts/generate_submission_summary.py` to create `qa/submission_summary.md` | Fixed |
| BUG-004 | Low | README lacked final QA/submission commands | Added final QA and submission evidence references | Fixed |

## Known Issues / Limitations

| ID | Severity | Issue | Impact | Workaround |
|---|---|---|---|---|
| LIM-001 | Low | SQLite is not suitable for high-concurrency production workloads | Fine for FYP/demo; limited for production scale | Migrate to PostgreSQL/MySQL in future work |
| LIM-002 | Low | OCR accuracy depends on Tesseract availability and document quality | Poor scans may produce incomplete text | Admin review remains manual |
| LIM-003 | Low | Groq AI requires an API key for live responses | Without key, AI features show fallbacks | Configure `.env` locally or Streamlit secrets on cloud |
| LIM-004 | Low | ML enhancement depends on dataset/model availability | Missing model should not stop deterministic recommendations | Train/regenerate model if needed |

## Unresolved Issues

No critical unresolved issues are currently documented. Add any supervisor/testing findings below:

| ID | Severity | Issue | Page/Module | Notes | Status |
|---|---|---|---|---|---|
| TBD | TBD |  |  |  | Open |

## Screenshots Placeholder

Attach final report screenshots here or reference them by filename:

- Landing page:
- Volunteer dashboard:
- Recommendations page:
- NGO dashboard:
- Admin dashboard:
- OCR document verification:
- Advanced analytics:
- ML evaluation:

## Testing Notes

- Run `python scripts/health_check.py` before the final demo.
- Run `python scripts/smoke_test.py` after a fresh install.
- Run `python scripts/generate_submission_summary.py` to produce a report-ready summary.
