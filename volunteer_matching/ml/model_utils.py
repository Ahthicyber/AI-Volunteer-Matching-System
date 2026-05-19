"""
ml/model_utils.py — Phase 9
Utility functions: model existence check, metadata reading.
"""

import json
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MODEL_PATH   = _PROJECT_ROOT / "data" / "models" / "match_model.pkl"
_META_PATH    = _PROJECT_ROOT / "data" / "models" / "model_meta.json"


def model_exists() -> bool:
    return _MODEL_PATH.exists()


def load_model_meta() -> dict | None:
    if not _META_PATH.exists():
        return None
    try:
        return json.loads(_META_PATH.read_text())
    except Exception:
        return None


def get_model_status() -> dict:
    exists = model_exists()
    meta   = load_model_meta() if exists else None
    return {
        "exists":     exists,
        "path":       str(_MODEL_PATH),
        "model_name": meta.get("model_name") if meta else None,
        "features":   meta.get("features")   if meta else None,
        "metrics":    meta.get("metrics")    if meta else None,
    }
