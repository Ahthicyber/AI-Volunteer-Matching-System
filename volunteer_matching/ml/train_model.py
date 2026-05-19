"""
ml/train_model.py — Phase 9
Train, evaluate, compare, and save ML matching models.
"""

import logging, json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MODEL_DIR    = _PROJECT_ROOT / "data" / "models"
_MODEL_PATH   = _MODEL_DIR / "match_model.pkl"
_META_PATH    = _MODEL_DIR / "model_meta.json"

from ml.preprocessing import FEATURE_COLS


# ── Evaluation helper ─────────────────────────────────────────────────────────

def evaluate_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    cm     = confusion_matrix(y_test, y_pred)
    return {
        "accuracy":         round(float(accuracy_score(y_test, y_pred)), 4),
        "precision":        round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall":           round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score":         round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "confusion_matrix": cm.tolist(),
        "report":           classification_report(y_test, y_pred, zero_division=0),
    }


# ── Logistic Regression ───────────────────────────────────────────────────────

def train_logistic_regression(X_train, y_train) -> Pipeline:
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(max_iter=1000, random_state=42, C=1.0)),
    ])
    pipe.fit(X_train, y_train)
    return pipe


# ── Random Forest ─────────────────────────────────────────────────────────────

def train_random_forest(X_train, y_train) -> Pipeline:
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    RandomForestClassifier(
            n_estimators=100, max_depth=6, random_state=42,
            class_weight="balanced",
        )),
    ])
    pipe.fit(X_train, y_train)
    return pipe


# ── Save / Load ───────────────────────────────────────────────────────────────

def save_model(model, model_name: str, metrics: dict) -> None:
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, str(_MODEL_PATH))
    meta = {
        "model_name": model_name,
        "features":   FEATURE_COLS,
        "metrics":    {k: v for k, v in metrics.items() if k != "report"},
    }
    _META_PATH.write_text(json.dumps(meta, indent=2))
    logger.info("Model saved: %s → %s", model_name, _MODEL_PATH)


# ── Main training pipeline ────────────────────────────────────────────────────

def train_best_model(df_engineered: pd.DataFrame) -> dict:
    """
    Train both models, compare, save the best one.
    Returns a full result dict with metrics for both models.
    """
    X = df_engineered[FEATURE_COLS].values
    y = df_engineered["match_label"].values

    # Check class balance
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    logger.info("Class distribution — match=1: %d, match=0: %d", n_pos, n_neg)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    logs = [
        f"Dataset: {len(df_engineered)} samples | Features: {len(FEATURE_COLS)}",
        f"Class balance: match=1 → {n_pos} ({n_pos/len(y)*100:.1f}%), "
        f"match=0 → {n_neg} ({n_neg/len(y)*100:.1f}%)",
        f"Train/Test split: {len(X_train)}/{len(X_test)} (80/20)",
    ]

    # ── Train ──────────────────────────────────────────────────────────────────
    logs.append("\n--- Logistic Regression ---")
    lr_model  = train_logistic_regression(X_train, y_train)
    lr_metrics = evaluate_model(lr_model, X_test, y_test)
    cv_lr      = cross_val_score(lr_model, X, y, cv=5, scoring="f1")
    lr_metrics["cv_f1_mean"] = round(float(cv_lr.mean()), 4)
    lr_metrics["cv_f1_std"]  = round(float(cv_lr.std()), 4)
    logs.append(f"  Accuracy:  {lr_metrics['accuracy']:.4f}")
    logs.append(f"  Precision: {lr_metrics['precision']:.4f}")
    logs.append(f"  Recall:    {lr_metrics['recall']:.4f}")
    logs.append(f"  F1-Score:  {lr_metrics['f1_score']:.4f}")
    logs.append(f"  CV F1:     {lr_metrics['cv_f1_mean']:.4f} ± {lr_metrics['cv_f1_std']:.4f}")

    logs.append("\n--- Random Forest ---")
    rf_model   = train_random_forest(X_train, y_train)
    rf_metrics = evaluate_model(rf_model, X_test, y_test)
    cv_rf      = cross_val_score(rf_model, X, y, cv=5, scoring="f1")
    rf_metrics["cv_f1_mean"] = round(float(cv_rf.mean()), 4)
    rf_metrics["cv_f1_std"]  = round(float(cv_rf.std()), 4)
    logs.append(f"  Accuracy:  {rf_metrics['accuracy']:.4f}")
    logs.append(f"  Precision: {rf_metrics['precision']:.4f}")
    logs.append(f"  Recall:    {rf_metrics['recall']:.4f}")
    logs.append(f"  F1-Score:  {rf_metrics['f1_score']:.4f}")
    logs.append(f"  CV F1:     {rf_metrics['cv_f1_mean']:.4f} ± {rf_metrics['cv_f1_std']:.4f}")

    # ── Feature importances (RF) ───────────────────────────────────────────────
    rf_clf = rf_model.named_steps["clf"]
    feature_importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(FEATURE_COLS, rf_clf.feature_importances_)
    }

    # ── Choose best by CV F1 ───────────────────────────────────────────────────
    if rf_metrics["cv_f1_mean"] >= lr_metrics["cv_f1_mean"]:
        best_model, best_name, best_metrics = rf_model, "Random Forest", rf_metrics
    else:
        best_model, best_name, best_metrics = lr_model, "Logistic Regression", lr_metrics

    logs.append(f"\n✅ Best model: {best_name} "
                f"(CV F1 = {best_metrics['cv_f1_mean']:.4f})")

    save_model(best_model, best_name, best_metrics)
    logs.append(f"💾 Model saved to: data/models/match_model.pkl")

    return {
        "best_model_name":   best_name,
        "best_metrics":      best_metrics,
        "lr_metrics":        lr_metrics,
        "rf_metrics":        rf_metrics,
        "feature_importances": feature_importances,
        "class_dist":        {"match": n_pos, "no_match": n_neg},
        "train_size":        len(X_train),
        "test_size":         len(X_test),
        "logs":              logs,
    }
