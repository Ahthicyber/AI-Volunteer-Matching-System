"""
ml/ml_matcher.py — Phase 9
Load saved model and predict ML match score for a volunteer–event pair.
Graceful fallback if model is not available — app never crashes.
"""

import logging
import json
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MODEL_PATH   = _PROJECT_ROOT / "data" / "models" / "match_model.pkl"
_META_PATH    = _PROJECT_ROOT / "data" / "models" / "model_meta.json"

_cached_model = None
_model_loaded = False


def load_ml_model():
    """
    Load the saved model (cached after first load).
    Returns (model, meta_dict) or (None, None) if unavailable.
    """
    global _cached_model, _model_loaded
    if _model_loaded:
        return _cached_model

    if not _MODEL_PATH.exists():
        logger.info("ML model not found at %s — deterministic scoring only", _MODEL_PATH)
        _model_loaded = True
        _cached_model = None
        return None

    try:
        import joblib
        model = joblib.load(str(_MODEL_PATH))
        _cached_model = model
        _model_loaded = True
        logger.info("ML model loaded from %s", _MODEL_PATH)
        return model
    except Exception as exc:
        logger.warning("ML model load failed: %s", exc)
        _model_loaded = True
        _cached_model = None
        return None


def reload_ml_model():
    """Force reload — called after training a new model."""
    global _cached_model, _model_loaded
    _cached_model = None
    _model_loaded = False
    return load_ml_model()


def _build_feature_vector(volunteer_profile: dict, event: dict) -> np.ndarray:
    """
    Convert a volunteer profile + event dict into the 6-feature vector
    expected by the trained model.
    Mirrors the deterministic engine logic exactly.
    """
    from ml.preprocessing import (
        normalize_list, _skill_org_overlap, _avail_org_match,
        _interest_org_match, _experience_match, _mode_match,
        _ORG_CAUSE_MAP, _AGE_EXP_MAP,
    )

    # Skills overlap — volunteer skills vs event required skills
    vol_skills_str  = volunteer_profile.get("skills", "")
    ev_skills_str   = event.get("required_skills", "")
    vol_skills      = normalize_list(vol_skills_str)
    ev_skills       = normalize_list(ev_skills_str)

    if ev_skills:
        skill_overlap = sum(1 for s in ev_skills if s in set(vol_skills)) / len(ev_skills)
    else:
        # Fall back to org-based skill overlap
        org_type  = event.get("cause_area", "") or event.get("type_of_organization", "")
        skill_overlap = _skill_org_overlap(vol_skills_str, org_type)

    # Availability
    vol_avail = volunteer_profile.get("availability", "Flexible")
    org_type  = event.get("cause_area", "NGO")
    avail_score = _avail_org_match(vol_avail, org_type)

    # Location
    vol_city  = (volunteer_profile.get("city", "") or "").strip().lower()
    ev_city   = (event.get("city", "") or "").strip().lower()
    loc_score = 1.0 if (vol_city and ev_city and vol_city == ev_city) else (0.3 if vol_city and ev_city else 0.0)

    # Interest / cause match
    vol_interests = normalize_list(volunteer_profile.get("interests", ""))
    ev_cause      = normalize_list(event.get("cause_area", ""))
    if vol_interests and ev_cause:
        interest_score = sum(1 for i in ev_cause if i in set(vol_interests)) / len(ev_cause)
    else:
        interest_score = _interest_org_match(org_type, vol_interests)

    # Experience
    vol_exp   = volunteer_profile.get("experience_level", "Intermediate")
    ev_exp    = event.get("experience_level", "Anyone")
    age_band  = "25-29"   # default mid-range if no age band
    exp_score = _experience_match(age_band, org_type)
    # Refine with actual experience levels
    exp_rank  = {"Beginner":1, "Intermediate":2, "Experienced":3}
    if ev_exp != "Anyone" and vol_exp in exp_rank and ev_exp in exp_rank:
        v_rank = exp_rank[vol_exp]
        e_rank = exp_rank[ev_exp]
        if v_rank >= e_rank:  exp_score = 1.0
        elif v_rank == e_rank - 1: exp_score = 0.7
        else: exp_score = 0.4

    # Mode
    vol_mode  = (volunteer_profile.get("preferred_mode", "On-site") or "On-site").lower()
    ev_mode   = (event.get("mode", "On-site") or "On-site").lower()
    if vol_mode == ev_mode:       mode_score = 1.0
    elif "hybrid" in (vol_mode, ev_mode): mode_score = 0.9
    else:                          mode_score = 0.4

    return np.array([[
        skill_overlap, avail_score, loc_score,
        interest_score, exp_score, mode_score,
    ]], dtype=float)


def predict_ml_match(volunteer_profile: dict, event: dict) -> dict:
    """
    Return ML prediction for a volunteer–event pair.

    Always returns a dict with:
      - ml_score_percentage : float | None
      - ml_prediction       : bool  | None  (True = good match)
      - model_available     : bool
      - explanation         : str
    """
    model = load_ml_model()

    if model is None:
        return {
            "ml_score_percentage": None,
            "ml_prediction":       None,
            "model_available":     False,
            "explanation":         "ML model not trained yet. Using deterministic scoring only.",
        }

    try:
        X = _build_feature_vector(volunteer_profile, event)

        # Probability of class 1 (good match)
        proba = model.predict_proba(X)[0]
        classes = list(model.classes_)
        pos_idx = classes.index(1) if 1 in classes else -1
        ml_prob = float(proba[pos_idx]) if pos_idx >= 0 else float(proba[1])

        ml_score_pct = round(ml_prob * 100, 1)
        prediction   = ml_prob >= 0.50

        # Human-readable explanation
        if ml_score_pct >= 80:
            qual = "strong"
        elif ml_score_pct >= 60:
            qual = "moderate"
        elif ml_score_pct >= 40:
            qual = "weak"
        else:
            qual = "poor"

        explanation = (
            f"ML model predicts a {qual} match ({ml_score_pct:.0f}% confidence). "
            f"Based on skill overlap, availability, location, interest, experience, and mode."
        )

        return {
            "ml_score_percentage": ml_score_pct,
            "ml_prediction":       prediction,
            "model_available":     True,
            "explanation":         explanation,
        }

    except Exception as exc:
        logger.error("predict_ml_match error: %s", exc)
        return {
            "ml_score_percentage": None,
            "ml_prediction":       None,
            "model_available":     False,
            "explanation":         f"ML prediction failed: {exc}",
        }
