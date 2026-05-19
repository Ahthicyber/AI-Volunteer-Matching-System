# Viva / Demo Script — AI-Based Volunteer Matching System

Use this as a live demonstration guide. Keep the demo focused on the main academic contribution: explainable volunteer-event matching with assistive AI/ML/OCR layers.

## 1. Introduction

“Good morning/afternoon. My project is an AI-Based Volunteer Matching System. It helps connect volunteers with NGOs by recommending suitable volunteering opportunities based on skills, availability, location, interests, experience level, and preferred mode. The system includes admin verification, NGO workflows, applications, feedback, AI explanations, OCR-assisted document review, notifications, and analytics.”

## 2. Project Problem

Explain:

- NGOs often struggle to find suitable volunteers.
- Volunteers may not know which opportunities fit their profile.
- Manual matching is slow and inconsistent.
- The project provides explainable, structured, and auditable matching.

## 3. Login and Roles

Show the login page and explain the three roles:

- Admin
- Volunteer
- NGO

Use demo credentials:

| Role | Email | Password |
|---|---|---|
| Admin | admin@volmatch.local | Admin@123 |
| Volunteer | volunteer@volmatch.local | Volunteer@123 |
| NGO | ngo@volmatch.local | Ngo@123 |

## 4. Volunteer Profile Flow

Login as volunteer and show:

1. Volunteer dashboard
2. Profile details
3. Skills, interests, availability, city, experience level, preferred mode
4. Document status
5. Recent notifications
6. AI profile suggestions, if Groq is configured

Explain that a strong volunteer profile improves recommendation quality.

## 5. NGO Workflow

Login as NGO and show:

1. NGO dashboard
2. Organization profile
3. Event management
4. Applicant management
5. AI event description improvement, if Groq is configured

Explain that NGOs create opportunities and review applications manually.

## 6. Admin Verification

Login as admin and show:

1. Admin dashboard
2. NGO verification
3. Volunteer/document verification
4. Event approval/rejection
5. Admin AI summaries

Emphasize: AI is assistive only. Admin decisions remain manual.

## 7. Deterministic Recommendations

Login as volunteer and open Recommendations.

Explain the deterministic criteria:

- Skills: 40%
- Availability: 20%
- Location: 15%
- Interests: 15%
- Experience: 5%
- Mode: 5%

Show the score breakdown and deterministic explanation.

Key line:

“The deterministic score is the primary recommendation score because it is explainable and academically defensible.”

## 8. ML Enhancement

Show ML score if available.

Explain:

- ML is secondary.
- It enhances insight but does not change ranking.
- Deterministic logic remains authoritative.

## 9. AI Explanation

Click “Generate AI Match Explanation,” if Groq is configured.

Explain:

- AI explains why a match is suitable.
- It does not approve, reject, or change scores.
- The app works even without a Groq key through fallback messages.

## 10. Application Workflow

Show:

1. Volunteer applies to an event.
2. NGO reviews the application.
3. NGO accepts or rejects.
4. Volunteer receives a notification.
5. My Applications page updates status.

## 11. Feedback Workflow

Show feedback section after accepted/completed application.

Explain:

- Feedback supports evaluation.
- Ratings help measure satisfaction and match quality.

## 12. OCR / Document Verification

Open Admin document verification section.

Show:

1. Uploaded document metadata
2. Run OCR button
3. Extracted text preview
4. Optional AI summary
5. Manual verify/reject buttons

Key line:

“OCR and AI summaries are assistive and may contain errors. Admin verification remains manual.”

## 13. Notifications

Show sidebar notification center and dashboard notifications.

Explain:

- Users receive updates for approvals, applications, document decisions, OCR status, and system messages.
- Notifications are informational only.

## 14. Admin Analytics

Open Advanced Analytics.

Show:

- Executive summary
- User analytics
- NGO/event analytics
- Application conversion rates
- Match quality distribution
- Feedback satisfaction
- Document/OCR metrics
- ML/Groq/OCR system health
- Rule-based admin insights

Explain how this supports final report evidence and system evaluation.

## 15. Evaluation Results

Open Evaluation and ML Evaluation pages.

Explain:

- The evaluation dashboard provides project evidence.
- ML evaluation is separate from deterministic recommendations.

## 16. Limitations

Mention honestly:

- SQLite is suitable for demo scale, not high-concurrency production.
- OCR accuracy depends on document quality.
- Groq AI needs an API key for live responses.
- ML quality depends on available dataset quality.

## 17. Future Work

Possible improvements:

- Cloud database migration
- Email notifications
- Improved ML training data
- More advanced reporting exports
- Enhanced document validation

## 18. Conclusion

“This project provides a complete, explainable, and modular volunteer matching platform. It combines deterministic scoring, ML enhancement, AI explanations, OCR assistance, notifications, and analytics while preserving human control and transparency.”
