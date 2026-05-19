"""
ai/prompts.py
─────────────
Centralized prompt templates for the optional Groq explanation layer.

Important architecture rule: these prompts are guidance-only. They must never
replace deterministic matching, ML scoring, admin decisions, NGO decisions, or
application outcomes.
"""

AI_SYSTEM_GUARDRAILS = """
You are an assistant inside an AI-Based Volunteer Matching System.
The deterministic matching engine is authoritative and remains the primary source of truth.
ML scores are secondary reference signals only.
Your role is explanation, summarization, and wording support only.
Do not approve or reject users, NGOs, events, applications, or matches.
Do not override, recalculate, or dispute deterministic scores.
Do not invent facts, guarantees, outcomes, credentials, or eligibility.
If information is missing, say that the available profile/event data is limited.
Keep responses concise, professional, and suitable for a university project demo.
""".strip()

MATCH_EXPLANATION_PROMPT = """
Create a concise volunteer-facing explanation for this existing recommendation.

Mandatory rules:
- The deterministic score is authoritative and remains the primary decision signal.
- AI provides guidance only; it must not change ranking, scores, applications, approvals, or outcomes.
- Do not invent missing information. If a field is missing, say the available data is limited.
- Do not promise acceptance, selection, impact, safety, payment, or any guaranteed outcome.
- Use only the provided volunteer profile, event details, deterministic score, deterministic breakdown, and optional ML score.

Explain briefly:
1. Why the event appears suitable.
2. Relevant strengths from skills, interests, location, availability, experience, and mode when provided.
3. Any possible gaps or limitations if visible from the score breakdown or event requirements.
4. A balanced final suitability note.

Style requirements:
- Professional, supportive, and clear.
- 150-250 words maximum.
- No headings longer than a few words.
- Avoid excessive markdown.

Volunteer profile:
{volunteer_profile}

Event details:
{event_details}

Deterministic score: {deterministic_score}

Deterministic score breakdown:
{score_breakdown}

ML score, if available: {ml_score}
""".strip()

PROFILE_IMPROVEMENT_PROMPT = """
Review this volunteer profile and provide constructive improvement suggestions.

Mandatory rules:
- AI provides guidance only and must not guarantee better matches, acceptance, selection, or outcomes.
- Do not invent experience, qualifications, education, languages, certificates, skills, or achievements.
- Use only the provided profile data. If something is missing, identify it as missing rather than assuming it.
- Keep the tone supportive, practical, and suitable for a university project demo.

Suggest concise improvements for:
1. Profile completeness and missing information.
2. Skills section strength and useful skills to consider learning, if relevant.
3. Interests/cause areas clarity.
4. Bio/about-me wording.
5. Availability, location, education, languages, or document details if missing or weak.

Style requirements:
- 150-300 words maximum.
- Use short, readable bullet points.
- Avoid excessive markdown.

Volunteer profile:
{volunteer_profile}
""".strip()

EVENT_IMPROVEMENT_PROMPT = """
Improve this NGO event description so it is clearer, more professional, and easier for volunteers to understand.

Mandatory rules:
- AI provides wording guidance only and must not approve, reject, rank, or auto-edit any record.
- Preserve the original event intent and requirements.
- Do not invent dates, locations, benefits, safety claims, compensation, eligibility, capacity, or impact.
- Do not drastically change requirements or add new responsibilities not present in the event data.
- If important details are missing, mention them as optional details the NGO may add manually.

Produce:
1. A polished event description volunteers can read.
2. A short optional note listing missing details the NGO may consider adding.

Style requirements:
- 150-300 words maximum.
- Professional, welcoming, and concise.
- Avoid excessive markdown.

Event data:
{event_data}
""".strip()

ADMIN_SUMMARY_PROMPT = """
Summarize the provided platform information for an admin dashboard.
This is informational only and must not make approval, rejection, moderation, or ranking decisions.
Do not invent numbers or trends.
If data is limited, clearly state that.
Keep the summary concise and presentation-ready.

Platform information:
{platform_data}
""".strip()


ADMIN_PROFILE_SUMMARY_PROMPT = """
Create a concise admin-facing profile summary for a {profile_type} profile.

Mandatory rules:
- AI is assistive only and must not approve, reject, verify, disqualify, or moderate this profile.
- Do not invent facts, credentials, verification outcomes, experience, documents, or missing details.
- Use only the provided profile data. If information is missing, state that the data is limited or incomplete.
- Do not claim that the profile is verified unless the provided data explicitly says so.

Summarize briefly:
1. Main profile overview.
2. Visible strengths or professionalism indicators.
3. Completeness observations and missing information.
4. Admin review considerations, phrased as observations only.

Style requirements:
- 150-250 words maximum.
- Clear, professional, and neutral.
- Avoid excessive markdown.

Profile data:
{profile_data}
""".strip()

DOCUMENT_METADATA_SUMMARY_PROMPT = """
Create a concise admin-facing summary of uploaded document metadata only.

Mandatory rules:
- Summarize metadata only: document type, filename, volunteer/user details, upload timing, verification status, reviewer notes, and admin notes if provided.
- Do not pretend to read the document contents.
- Do not perform OCR, extract text, validate authenticity, or claim the document is genuine.
- Do not approve, reject, verify, or recommend a final decision.
- If metadata is limited, clearly state that the metadata is limited.

Include a short note that OCR-based document content analysis is planned for a future phase.

Style requirements:
- 100-180 words maximum.
- Clear, professional, and neutral.
- Avoid excessive markdown.

Document metadata:
{document_data}
""".strip()

SYSTEM_INSIGHTS_PROMPT = """
Generate lightweight admin insights from the provided aggregate platform metrics.

Mandatory rules:
- AI is assistive only and must not make approvals, rejections, moderation decisions, or policy decisions.
- Do not invent numbers, trends, categories, or analytics not present in the data.
- If the data is too limited, clearly state that insights are limited.
- Keep observations explainable and suitable for a Final Year Project admin dashboard.

Possible insight areas:
- common volunteer skills or profile gaps if provided
- NGO/event review workload if provided
- participation/application observations if provided
- document review status if provided

Style requirements:
- 150-250 words maximum.
- Use concise bullets or short paragraphs.
- Avoid excessive markdown.

Aggregate platform metrics:
{metrics_data}
""".strip()

DOCUMENT_OCR_SUMMARY_PROMPT = """
Summarize the extracted OCR text from an uploaded volunteer/NGO document.

Mandatory rules:
- Summarize only the extracted text provided below.
- OCR may be incomplete or inaccurate; mention uncertainty if the text is unclear, fragmented, or limited.
- Do not invent missing names, dates, IDs, qualifications, institutions, or document details.
- Do not verify authenticity, detect fraud, approve, reject, or recommend a final decision.
- Do not claim the document is genuine or valid.
- Keep the summary concise and useful for manual admin review.

Document type: {document_type}

Extracted OCR text:
{extracted_text}
""".strip()
