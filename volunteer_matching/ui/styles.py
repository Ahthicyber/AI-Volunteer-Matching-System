"""
ui/styles.py
────────────
Centralized Streamlit styling for Phase 14 UI/UX polish.

The CSS is intentionally lightweight and Streamlit-native friendly. It keeps
existing workflows unchanged while improving cards, badges, spacing, and mobile
responsiveness across pages.
"""
from __future__ import annotations

import streamlit as st

GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

    :root {
        --vm-bg: #0d1117;
        --vm-surface: #161b22;
        --vm-surface-2: #1f2937;
        --vm-border: #30363d;
        --vm-text: #e6edf3;
        --vm-muted: #8b949e;
        --vm-blue: #58a6ff;
        --vm-green: #3fb950;
        --vm-orange: #f0883e;
        --vm-red: #f85149;
        --vm-purple: #a371f7;
    }

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background: var(--vm-bg); color: var(--vm-text); }
    .main .block-container { padding: 2rem 3rem; max-width: 1280px; }

    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        color: var(--vm-text) !important;
        letter-spacing: -0.02em;
    }

    [data-testid="stSidebar"] {
        background: var(--vm-surface) !important;
        border-right: 1px solid var(--vm-border);
    }
    [data-testid="stSidebar"] * { color: var(--vm-text) !important; }
    /* Hide Streamlit's automatic multipage navigation so role-based links remain clear. */
    [data-testid="stSidebarNav"] { display: none !important; }

    .vm-page-title { margin-bottom: 1rem; }
    .vm-page-title h1 { font-size: clamp(1.8rem, 4vw, 2.7rem); margin-bottom: 0.25rem; }
    .vm-page-subtitle { color: var(--vm-muted); font-size: 1rem; line-height: 1.6; margin-top: 0; }

    .vm-card, .vm-info-card, .vm-warning-card, .vm-success-card, .vm-empty-state,
    .vm-notification-card, .vm-profile-card, .vm-event-card, .vm-application-card {
        background: linear-gradient(180deg, rgba(22,27,34,0.98), rgba(13,17,23,0.98));
        border: 1px solid var(--vm-border);
        border-radius: 16px;
        padding: 1.1rem 1.25rem;
        margin: 0.75rem 0;
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.18);
    }
    .vm-card:hover, .vm-event-card:hover, .vm-application-card:hover { border-color: rgba(88,166,255,0.75); }

    .vm-info-card { border-left: 4px solid var(--vm-blue); }
    .vm-warning-card { border-left: 4px solid var(--vm-orange); }
    .vm-success-card { border-left: 4px solid var(--vm-green); }
    .vm-empty-state { text-align: center; color: var(--vm-muted); padding: 1.75rem; border-style: dashed; }

    .vm-section-header { margin: 1.35rem 0 0.75rem; }
    .vm-section-header h2, .vm-section-header h3 { margin-bottom: 0.2rem; }
    .vm-section-header p { color: var(--vm-muted); margin-top: 0; line-height: 1.55; }

    .vm-divider { border: none; border-top: 1px solid var(--vm-border); margin: 1.5rem 0; }

    .vm-badge, .stat-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid #374151;
        background: #1f2937;
        color: #c9d1d9;
        margin: 0.15rem 0.2rem 0.15rem 0;
    }
    .badge-green, .vm-badge-success { background:#0d4429; border-color:#1a7f37; color:#3fb950; }
    .badge-blue, .vm-badge-info { background:#0c2d6b; border-color:#1f6feb; color:#58a6ff; }
    .badge-orange, .vm-badge-warning { background:#3d1f00; border-color:#9e4a00; color:#f0883e; }
    .badge-red, .vm-badge-danger { background:#3d0e0e; border-color:#9e1515; color:#f85149; }
    .vm-badge-muted { background:#1f2937; border-color:#374151; color:#9ca3af; }

    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid #2ea043 !important;
        background: #238636 !important;
        color: #fff !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.1rem !important;
    }
    .stButton > button:hover { background: #2ea043 !important; border-color: #3fb950 !important; }

    [data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(22,27,34,0.96), rgba(13,17,23,0.96));
        border: 1px solid var(--vm-border);
        border-radius: 14px;
        padding: 1rem;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Syne', sans-serif !important;
        color: var(--vm-blue) !important;
        font-size: clamp(1.35rem, 3vw, 2rem) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--vm-muted) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stTextInput > div > input, .stTextArea textarea, .stNumberInput input {
        background: #0d1117 !important;
        border: 1px solid var(--vm-border) !important;
        color: var(--vm-text) !important;
        border-radius: 10px !important;
    }
    [data-baseweb="select"] > div {
        background: #0d1117 !important;
        border-color: var(--vm-border) !important;
        color: var(--vm-text) !important;
        border-radius: 10px !important;
    }

    .stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid var(--vm-border); }
    .stTabs [data-baseweb="tab"] { color: var(--vm-muted) !important; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: var(--vm-blue) !important; border-bottom: 2px solid var(--vm-blue) !important; }

    .stDataFrame, div[data-testid="stDataFrame"] { border-radius: 12px; overflow: auto; }

    .vm-footer {
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--vm-border);
        color: #6e7681;
        font-size: 0.78rem;
        text-align: center;
    }

    @media (max-width: 768px) {
        .main .block-container { padding: 1.1rem 1rem; }
        .vm-card, .vm-info-card, .vm-warning-card, .vm-success-card,
        .vm-empty-state, .vm-notification-card, .vm-profile-card,
        .vm-event-card, .vm-application-card { padding: 0.9rem; border-radius: 13px; }
        .vm-page-title h1 { font-size: 1.8rem; }
        [data-testid="stMetric"] { padding: 0.8rem; }
        .stButton > button { width: 100%; }
    }

    @keyframes vmFadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .vm-fade-in { animation: vmFadeIn 0.55s ease-out both; }

    .vm-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(88,166,255,0.22);
        border-radius: 26px;
        padding: clamp(1.4rem, 5vw, 3.2rem);
        margin: 0.5rem 0 1.5rem;
        background:
            radial-gradient(circle at top left, rgba(88,166,255,0.20), transparent 35%),
            radial-gradient(circle at bottom right, rgba(163,113,247,0.18), transparent 30%),
            linear-gradient(135deg, rgba(22,27,34,0.98), rgba(13,17,23,0.98));
        box-shadow: 0 22px 60px rgba(0,0,0,0.32);
    }
    .vm-hero h1 {
        font-size: clamp(2rem, 6vw, 4.2rem) !important;
        line-height: 1.02;
        margin: 0 0 0.8rem;
    }
    .vm-hero p {
        color: var(--vm-muted);
        font-size: clamp(0.95rem, 2vw, 1.16rem);
        line-height: 1.7;
        max-width: 760px;
        margin: 0;
    }
    .vm-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        color: var(--vm-blue);
        background: rgba(88,166,255,0.10);
        border: 1px solid rgba(88,166,255,0.22);
        border-radius: 999px;
        padding: 0.35rem 0.85rem;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .vm-role-card, .vm-feature-card, .vm-action-card {
        background: linear-gradient(180deg, rgba(22,27,34,0.96), rgba(13,17,23,0.98));
        border: 1px solid var(--vm-border);
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        min-height: 150px;
        transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
    }
    .vm-role-card:hover, .vm-feature-card:hover, .vm-action-card:hover {
        transform: translateY(-3px);
        border-color: rgba(88,166,255,0.70);
        box-shadow: 0 18px 45px rgba(0,0,0,0.28);
    }
    .vm-role-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .vm-role-title, .vm-feature-title { font-weight: 800; color: var(--vm-text); margin-bottom: 0.35rem; }
    .vm-role-text, .vm-feature-text { color: var(--vm-muted); font-size: 0.88rem; line-height: 1.6; }

    @media (max-width: 768px) {
        .vm-hero { padding: 1.25rem; border-radius: 18px; }
        .vm-role-card, .vm-feature-card, .vm-action-card { min-height: unset; }
    }

</style>
"""


def apply_global_styles() -> None:
    """Apply the shared VolunteerAI visual system once per page render."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
