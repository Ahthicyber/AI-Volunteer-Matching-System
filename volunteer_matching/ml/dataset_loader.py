"""
ml/dataset_loader.py — Phase 9
Load, validate, and report on the volunteer dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
import logging

logger = logging.getLogger(__name__)

_PROJECT_ROOT  = Path(__file__).resolve().parent.parent
_DATASET_PATH  = _PROJECT_ROOT / "data" / "dataset" / "volunteer_dataset_cleaned_audit.xlsx"
_SHEET_NAME    = "Cleaned Dataset"

REQUIRED_COLUMNS = [
    "Volunteer ID", "Volunteer Name", "Age", "Gender",
    "Skills", "Availability", "Location",
    "Type of Organization", "Age Band", "Skill Count",
]


def load_dataset() -> pd.DataFrame | None:
    print("DATASET PATH:", _DATASET_PATH)
    print("EXISTS:", _DATASET_PATH.exists())
    """
    Load the cleaned volunteer dataset from the Excel file.
    Returns DataFrame or None if file is missing.
    """
    if not _DATASET_PATH.exists():
        logger.warning("Dataset not found at %s", _DATASET_PATH)
        return None
    try:
        df = pd.read_excel(str(_DATASET_PATH), sheet_name=_SHEET_NAME)
        logger.info("Dataset loaded: %d rows × %d cols", *df.shape)
        return df
    except Exception as exc:
        import traceback
    print("\n========== DATASET ERROR ==========")
    traceback.print_exc()
    print("===================================\n")
    raise


def validate_dataset(df: pd.DataFrame) -> dict:
    """
    Run validation checks and return a dict of findings.
    """
    issues = []
    warnings = []

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")

    null_counts = df.isnull().sum()
    for col, n in null_counts.items():
        if n > 0:
            warnings.append(f"'{col}' has {n} null value(s)")

    dups = df.duplicated().sum()
    if dups:
        warnings.append(f"{dups} duplicate row(s) found")

    return {
        "valid":    len(issues) == 0,
        "issues":   issues,
        "warnings": warnings,
        "shape":    df.shape,
    }


def generate_dataset_report(df: pd.DataFrame) -> dict:
    """
    Generate a comprehensive analysis report as a plain dict.
    """
    # Individual skills
    all_skills = []
    for s in df["Skills"].dropna():
        all_skills.extend([x.strip() for x in str(s).split(",")])
    skill_counter = Counter(all_skills)

    # Availability mapping check vs app options
    app_avail_map = {
        "Weekdays":  "Weekdays",
        "Weekends":  "Weekend",
        "Full-Time": "Flexible",
        "Part-Time": "Flexible",
        "Evenings":  "Weekdays",   # evening = weekday evening
        "Flexible":  "Flexible",
    }

    return {
        "shape":           {"rows": df.shape[0], "columns": df.shape[1]},
        "columns":         list(df.columns),
        "dtypes":          {col: str(df[col].dtype) for col in df.columns},
        "null_counts":     {col: int(df[col].isnull().sum()) for col in df.columns},
        "duplicates":      int(df.duplicated().sum()),
        "age_range":       {"min": int(df["Age"].min()), "max": int(df["Age"].max()),
                            "mean": round(float(df["Age"].mean()), 1)},
        "gender_dist":     df["Gender"].value_counts().to_dict(),
        "availability_dist": df["Availability"].value_counts().to_dict(),
        "location_dist":   df["Location"].value_counts().to_dict(),
        "org_type_dist":   df["Type of Organization"].value_counts().to_dict(),
        "age_band_dist":   df["Age Band"].value_counts().to_dict(),
        "skill_count_dist": df["Skill Count"].value_counts().sort_index().to_dict(),
        "top_skills":      dict(skill_counter.most_common(20)),
        "total_skill_tokens": len(all_skills),
        "unique_skills":   len(skill_counter),
        "avail_app_mapping": app_avail_map,
    }
