"""
ml/preprocessing.py — Phase 9
Data cleaning, normalization, and feature engineering.

Feature engineering aligns with the deterministic engine weights:
  Skills       40%  → skill_overlap_score
  Availability 20%  → availability_match
  Location     15%  → location_match
  Interests    15%  → interest_match  (org type as proxy)
  Experience    5%  → experience_match
  Mode          5%  → mode_match
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

# ── Normalization mappings ────────────────────────────────────────────────────

# Dataset availability → app availability slots
_AVAIL_NORM = {
    "weekdays":  "Weekdays",
    "weekends":  "Weekend",
    "full-time": "Flexible",
    "part-time": "Flexible",
    "evenings":  "Weekdays",
    "flexible":  "Flexible",
}

# Org type → cause areas (mirrors deterministic interest matching)
_ORG_CAUSE_MAP = {
    "School":               ["Education", "Youth Development"],
    "Hospital":             ["Health"],
    "Healthcare":           ["Health"],
    "Community Center":     ["Education", "Environment", "Poverty Relief"],
    "NGO":                  ["Education", "Health", "Environment",
                             "Poverty Relief", "Disaster Relief"],
    "Relief Organization":  ["Disaster Relief", "Poverty Relief"],
    "Youth Development":    ["Youth Development", "Education"],
    "Pet and Animal Service": ["Animal Welfare"],
}

# Org type → mode tendency
_ORG_MODE_MAP = {
    "School":               "On-site",
    "Hospital":             "On-site",
    "Healthcare":           "On-site",
    "Community Center":     "On-site",
    "NGO":                  "Hybrid",
    "Relief Organization":  "On-site",
    "Youth Development":    "On-site",
    "Pet and Animal Service": "On-site",
}

# Skill → org type alignment (for label synthesis)
_SKILL_ORG_MATCH = {
    "Teaching":           ["School", "Youth Development"],
    "Tutoring":           ["School", "Youth Development"],
    "Youth Mentoring":    ["Youth Development", "School"],
    "Leadership Development": ["Youth Development", "School"],
    "Data Entry":         ["NGO", "Community Center", "Relief Organization", "School"],
    "Event Management":   ["NGO", "Community Center", "Relief Organization", "School"],
    "Fundraising":        ["NGO", "Relief Organization", "Community Center"],
    "Logistics":          ["Relief Organization", "NGO", "Community Center"],
    "Community Outreach": ["NGO", "Community Center", "Relief Organization"],
    "Marketing":          ["NGO", "Community Center"],
    "Photography":        ["NGO", "Community Center"],
    "Counseling":         ["Healthcare", "Hospital", "Youth Development", "Community Center"],
    "Healthcare":         ["Hospital", "Healthcare"],
    "First Aid":          ["Hospital", "Healthcare", "Relief Organization"],
    "Medical Camp Support": ["Hospital", "Healthcare", "Relief Organization"],
    "Patient Support":    ["Hospital", "Healthcare"],
    "Emergency Response": ["Relief Organization", "Hospital", "Healthcare"],
    "Communication":      ["School", "NGO", "Community Center"],
    "Animal Care":        ["Pet and Animal Service"],
    "Customer Service":   ["Pet and Animal Service", "Community Center"],
    "Pet Grooming":       ["Pet and Animal Service"],
    "Mental Health Support": ["Hospital", "Healthcare", "Community Center"],
    "Sports Coaching":    ["School", "Youth Development"],
    "Creative Design":    ["NGO", "Community Center"],
    "Crisis Intervention": ["Hospital", "Healthcare", "Relief Organization"],
}

# Experience level mapping: dataset age-band → app experience levels
_AGE_EXP_MAP = {
    "18-24": "Beginner",
    "25-29": "Intermediate",
    "30-35": "Experienced",
}


# ── Pure text helpers ─────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """Lowercase, strip whitespace, normalize internal spacing."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_list(text: str) -> list[str]:
    """Parse comma-separated text into cleaned lowercase list."""
    if not isinstance(text, str) or not text.strip():
        return []
    return [item.strip().lower() for item in text.split(",") if item.strip()]


# ── Dataset cleaning ──────────────────────────────────────────────────────────

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all normalization steps to the raw dataset.
    Returns a cleaned copy.
    """
    df = df.copy()

    # Normalize all string columns
    for col in ["Gender", "Availability", "Location", "Type of Organization", "Age Band"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Normalize Skills: strip extra spaces around commas
    df["Skills"] = df["Skills"].astype(str).apply(
        lambda s: ", ".join(p.strip() for p in s.split(",") if p.strip())
    )

    # Derive normalized availability (mapped to app slots)
    df["avail_normalized"] = df["Availability"].str.lower().map(
        lambda x: _AVAIL_NORM.get(x, "Flexible")
    )

    # Derive experience level from age band
    df["experience_level"] = df["Age Band"].map(_AGE_EXP_MAP).fillna("Intermediate")

    # Drop rows missing required fields
    required = ["Skills", "Availability", "Location", "Type of Organization"]
    before = len(df)
    df = df.dropna(subset=required)
    df = df[df[required].apply(lambda r: all(str(v).strip() for v in r), axis=1)]
    if len(df) < before:
        import logging
        logging.getLogger(__name__).info("Dropped %d rows with missing required fields", before - len(df))

    df = df.reset_index(drop=True)
    return df


# ── Feature engineering ────────────────────────────────────────────────────────

def _skill_org_overlap(skills_str: str, org_type: str) -> float:
    """Return 0–1: fraction of volunteer skills that match the org's expected skills."""
    vol_skills = normalize_list(skills_str)
    if not vol_skills:
        return 0.0
    matched = 0
    for skill in vol_skills:
        # title-case lookup
        skill_title = skill.title()
        expected_orgs = _SKILL_ORG_MATCH.get(skill_title, [])
        if org_type in expected_orgs:
            matched += 1
    return matched / len(vol_skills)


def _avail_org_match(avail: str, org_type: str) -> float:
    """Return 0–1: how well the availability fits the org type."""
    avail_lower = avail.lower()
    # Hospitals/schools need weekday or full-time
    weekday_orgs = {"School", "Hospital", "Healthcare", "Community Center"}
    # Relief orgs often need flexible/weekend responders
    flexible_orgs = {"Relief Organization", "NGO"}

    if avail_lower in ("full-time", "flexible"):
        return 1.0
    if avail_lower == "weekdays" and org_type in weekday_orgs:
        return 1.0
    if avail_lower == "weekends" and org_type in flexible_orgs:
        return 0.8
    if avail_lower == "evenings":
        return 0.6
    if avail_lower == "part-time":
        return 0.7
    return 0.5


def _interest_org_match(org_type: str, causes: list[str]) -> float:
    """Return 0–1: how many of the org's cause areas are covered by volunteer interests."""
    org_causes = _ORG_CAUSE_MAP.get(org_type, [])
    if not org_causes:
        return 0.5
    if not causes:
        return 0.0
    causes_lower = set(c.lower() for c in causes)
    org_causes_lower = set(c.lower() for c in org_causes)
    overlap = len(causes_lower & org_causes_lower)
    return overlap / len(org_causes_lower)


def _experience_match(age_band: str, org_type: str) -> float:
    """Return 0–1 based on age/experience level fitness."""
    exp = _AGE_EXP_MAP.get(age_band, "Intermediate")
    # Hospitals and Relief orgs prefer more experienced
    if org_type in ("Hospital", "Healthcare", "Relief Organization"):
        if exp == "Experienced":   return 1.0
        if exp == "Intermediate":  return 0.7
        return 0.4
    # Schools and Youth prefer younger/beginner
    if org_type in ("School", "Youth Development"):
        if exp == "Beginner":      return 1.0
        if exp == "Intermediate":  return 0.8
        return 0.7
    return 0.7  # neutral


def _mode_match(org_type: str) -> float:
    """Return 0–1: mode compatibility (most volunteer activities are on-site in this dataset)."""
    # Dataset doesn't have volunteer mode preference — we treat all as compatible
    # On-site orgs = 1.0, Hybrid NGOs = 0.9
    mode = _ORG_MODE_MAP.get(org_type, "On-site")
    return 1.0 if mode == "On-site" else 0.9


def _synthesize_label(row: pd.Series) -> int:
    """
    Synthesize match label: 1 = good match, 0 = poor match.
    Based on skill–org alignment (primary signal).
    """
    overlap = _skill_org_overlap(row["Skills"], row["Type of Organization"])
    avail   = _avail_org_match(row["Availability"], row["Type of Organization"])
    return 1 if (overlap >= 0.5 and avail >= 0.6) or overlap == 1.0 else 0


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add ML feature columns to a cleaned dataset.
    Also synthesizes a binary match label for supervised training.
    """
    df = df.copy()

    df["skill_overlap_score"]  = df.apply(
        lambda r: _skill_org_overlap(r["Skills"], r["Type of Organization"]), axis=1
    )
    df["availability_match"]   = df.apply(
        lambda r: _avail_org_match(r["Availability"], r["Type of Organization"]), axis=1
    )
    # Interest match: we use the org-type cause areas as a proxy
    # (volunteers don't have explicit cause fields in this dataset)
    df["interest_match"]       = df["Type of Organization"].apply(
        lambda org: _interest_org_match(org, _ORG_CAUSE_MAP.get(org, []))
    )
    df["experience_match"]     = df.apply(
        lambda r: _experience_match(r["Age Band"], r["Type of Organization"]), axis=1
    )
    df["location_match"]       = 1.0   # same-city assumed in dataset (no event city col)
    df["mode_match"]           = df["Type of Organization"].apply(_mode_match)

    # Synthesized weighted score (mirrors deterministic weights)
    df["synthetic_score"] = (
        df["skill_overlap_score"]  * 0.40 +
        df["availability_match"]   * 0.20 +
        df["location_match"]       * 0.15 +
        df["interest_match"]       * 0.15 +
        df["experience_match"]     * 0.05 +
        df["mode_match"]           * 0.05
    )

    # Clip to [0,1] range (floating point safety)
    df["synthetic_score"] = df["synthetic_score"].clip(0.0, 1.0)
    # Binary label: 1 = good match
    df["match_label"] = df.apply(_synthesize_label, axis=1)

    return df


FEATURE_COLS = [
    "skill_overlap_score",
    "availability_match",
    "location_match",
    "interest_match",
    "experience_match",
    "mode_match",
]
