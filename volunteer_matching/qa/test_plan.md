# QA Test Plan — AI-Based Volunteer Matching System

Use this document as submission evidence. Mark each test as Pass/Fail after executing it on a fresh local run or deployed demo.

| Test ID | Area | Role | Preconditions | Steps | Expected Result | Pass/Fail |
|---|---|---|---|---|---|---|
| AUTH-01 | Authentication | Admin | Demo data seeded | Open app, login with `admin@volmatch.local` / `Admin@123` | Admin dashboard opens and role is shown correctly | ☐ |
| AUTH-02 | Authentication | Volunteer | Demo data seeded | Login with `volunteer@volmatch.local` / `Volunteer@123` | Volunteer dashboard opens and session remains stable | ☐ |
| AUTH-03 | Authentication | NGO | Demo data seeded | Login with `ngo@volmatch.local` / `Ngo@123` | NGO dashboard opens and organization data appears | ☐ |
| AUTH-04 | Authentication | Any | App running | Enter wrong password | Clean error appears; no traceback is shown | ☐ |
| VOL-01 | Volunteer Profile | Volunteer | Logged in as volunteer | Open Volunteer Dashboard | Profile summary, completeness, verification status appear | ☐ |
| VOL-02 | Volunteer Profile | Volunteer | Logged in as volunteer | Edit profile details and save | Profile updates without duplicate records | ☐ |
| DOC-01 | Document Upload | Volunteer | Logged in as volunteer | Upload supported document | Document appears with pending verification status | ☐ |
| DOC-02 | Document Upload | Volunteer | Existing document uploaded | View document list | Verification status and OCR status appear clearly | ☐ |
| NGO-01 | NGO Profile | NGO | Logged in as NGO | Open NGO Dashboard | NGO profile summary and verification status appear | ☐ |
| NGO-02 | NGO Verification | Admin | Pending NGO exists | Approve NGO from Admin Dashboard | NGO status changes to approved; NGO notification is created | ☐ |
| NGO-03 | NGO Verification | Admin | Pending NGO exists | Reject NGO with reason | NGO status changes to rejected; reason is stored; notification is created | ☐ |
| EVT-01 | Event Creation | NGO | NGO approved | Create new event | Event is saved as pending or approved according to workflow | ☐ |
| EVT-02 | Event Approval | Admin | Pending event exists | Approve event | Event becomes visible/usable in recommendations | ☐ |
| REC-01 | Recommendations | Volunteer | Approved events and completed profile exist | Open Recommendations page | Deterministic score and explanation appear | ☐ |
| REC-02 | Recommendations | Volunteer | Groq key missing | Click AI Match Explanation | Safe fallback warning appears; deterministic result remains visible | ☐ |
| REC-03 | Recommendations | Volunteer | Groq key configured | Click AI Match Explanation | Concise AI explanation appears; ranking does not change | ☐ |
| APP-01 | Applications | Volunteer | Recommendation exists | Apply to event | Application is created once; duplicate application is prevented | ☐ |
| APP-02 | Applications | NGO | Application exists | Accept application | Application status becomes accepted; volunteer notification appears | ☐ |
| APP-03 | Applications | NGO | Application exists | Reject application | Application status becomes rejected; volunteer notification appears | ☐ |
| APP-04 | My Applications | Volunteer | Applications exist | Open My Applications | Status badges and event details render without raw dictionaries | ☐ |
| FB-01 | Feedback | Volunteer/NGO | Accepted/completed application exists | Submit feedback | Feedback is stored and analytics update | ☐ |
| NOTIF-01 | Notifications | Any logged-in user | Notifications exist | Open sidebar notification center | Latest notifications and unread count appear | ☐ |
| NOTIF-02 | Notifications | Any logged-in user | Unread notifications exist | Mark one/all notifications read | Unread count updates correctly | ☐ |
| ML-01 | ML Evaluation | Admin | Logged in as admin | Open ML Evaluation page | Page loads even if model file is missing | ☐ |
| ML-02 | ML Score | Volunteer | Model available or unavailable | Open Recommendations | ML score appears if available; fallback if unavailable | ☐ |
| AI-01 | Groq AI | Any supported role | No Groq key | Trigger any AI feature | App shows clean fallback and does not crash | ☐ |
| AI-02 | Groq AI | Any supported role | Valid Groq key | Trigger AI feature manually | AI response appears only after button click | ☐ |
| OCR-01 | OCR | Admin | Uploaded PDF exists | Click Run OCR | Extracted text preview appears or graceful failure message appears | ☐ |
| OCR-02 | OCR | Admin | Uploaded JPG/PNG exists | Click Run OCR | Extracted text preview appears or clean OCR failure appears | ☐ |
| OCR-03 | OCR AI Summary | Admin | OCR processed document exists | Generate AI Summary | Summary appears if Groq configured; fallback if not | ☐ |
| OCR-04 | Manual Verification | Admin | Document exists | Verify/reject document manually | Status updates; volunteer sees updated status | ☐ |
| ANA-01 | Admin Analytics | Admin | Logged in as admin | Open Advanced Analytics | Executive summary and charts load | ☐ |
| ANA-02 | Admin Analytics | Volunteer/NGO | Logged in as non-admin | Try to access Advanced Analytics directly | Access is blocked or redirected cleanly | ☐ |
| DEP-01 | Deployment | Developer | Fresh virtual environment | Install requirements and run app | App starts using `streamlit run app.py` | ☐ |
| DEP-02 | Health Check | Developer | Project root terminal | Run `python scripts/health_check.py` | PASS/WARNING/FAIL report appears without crashing | ☐ |
| DEP-03 | Smoke Test | Developer | Project root terminal | Run `python scripts/smoke_test.py` | No FAIL entries on a correctly configured project | ☐ |

## Notes

- AI, OCR, and ML model availability are optional integrations; missing keys/binaries/models should produce warnings, not app crashes.
- Deterministic matching remains the primary evaluation criterion throughout testing.
