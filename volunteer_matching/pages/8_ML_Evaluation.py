"""
pages/8_ML_Evaluation.py — Phase 9
Admin-only ML evaluation dashboard: dataset analysis, model training, metrics.
"""

import streamlit as st
from ui.styles import apply_global_styles
import pandas as pd
import numpy as np
from utils.session import init_session, current_user, logout_user, require_auth
from ml.dataset_loader import load_dataset, validate_dataset, generate_dataset_report
from ml.preprocessing import clean_dataset, engineer_features, FEATURE_COLS
try:
    from ml.train_model import train_best_model
    ML_IMPORT_ERROR = None
except ModuleNotFoundError as exc:
    train_best_model = None
    ML_IMPORT_ERROR = str(exc)
except ImportError as exc:
    train_best_model = None
    ML_IMPORT_ERROR = str(exc)

try:
    from ml.ml_matcher import reload_ml_model
except Exception:
    reload_ml_model = None

from ml.model_utils import get_model_status

st.set_page_config(
    page_title="ML Evaluation · VolunteerAI",
    page_icon="🤖",
    layout="wide",
)
apply_global_styles()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
    html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
    #MainMenu,footer,header  { visibility:hidden; }
    .stApp { background:#0d1117; color:#e6edf3; }
    [data-testid="stSidebar"] { background:#161b22!important; border-right:1px solid #30363d; }
    [data-testid="stSidebar"] * { color:#e6edf3!important; }
    h1,h2,h3 { font-family:'Syne',sans-serif!important; font-weight:800!important; color:#e6edf3!important; }
    .main .block-container { padding:2rem 3rem; max-width:1200px; }
    .vm-divider { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    .stButton > button { background:#238636!important; color:#fff!important;
        border:1px solid #2ea043!important; border-radius:6px!important; font-weight:500!important; }
    .stButton > button:hover { background:#2ea043!important; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:#58a6ff!important; font-size:1.6rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.75rem!important; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["admin"])
user = current_user()

if train_best_model is None:
    st.error("ML dependencies are not installed. Run the command below, then restart the app.")
    if ML_IMPORT_ERROR:
        st.caption(f"Import detail: {ML_IMPORT_ERROR}")
    st.code("pip install -r requirements.txt", language="bash")
    st.code("pip install joblib scikit-learn", language="bash")
    st.stop()

with st.sidebar:
    st.markdown("**🤝 VolunteerAI**")
    st.caption(f"Admin: {user['email']}")
    st.markdown("")
    if st.button("🚪 Logout", key="ml_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py",                   label="🏠 Home")
    st.page_link("pages/4_Admin_Dashboard.py", label="🔐 Admin Dashboard")
    st.page_link("pages/7_Evaluation.py",      label="📊 Evaluation")

st.markdown(
    "<h1 style='font-size:2.2rem;margin-bottom:0.2rem'>🤖 ML Evaluation Dashboard</h1>"
    "<p style='color:#8b949e;margin-top:0'>"
    "Dataset analysis, model training, and ML integration overview.</p>",
    unsafe_allow_html=True,
)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── Model status banner ───────────────────────────────────────────────────────
status = get_model_status()
if status["exists"]:
    m = status["metrics"] or {}
    st.success(
        f"✅ **Model available:** {status['model_name']}  ·  "
        f"Accuracy: {m.get('accuracy','—')}  ·  "
        f"F1: {m.get('f1_score','—')}  ·  "
        f"CV F1: {m.get('cv_f1_mean','—')}"
    )
else:
    st.warning("⚠️ No trained model found. Use **Train Model** tab below to train one.")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── Load dataset ──────────────────────────────────────────────────────────────
from ml.dataset_loader import load_dataset, _DATASET_PATH

df_raw = load_dataset()

if df_raw is None:
    st.error(f"Dataset not found.")
    st.code(f"Expected location:\n{_DATASET_PATH}")
    st.stop()

tabs = st.tabs([
    "📋 Dataset Overview",
    "📊 Analysis Report",
    "🔧 Feature Engineering",
    "🎯 Train Model",
    "📈 Model Metrics",
    "ℹ️ System Info",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DATASET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("### 📋 Raw Dataset Preview")

    val = validate_dataset(df_raw)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Rows",    df_raw.shape[0])
    with m2: st.metric("Columns", df_raw.shape[1])
    with m3: st.metric("Valid",   "✅ Yes" if val["valid"] else "❌ No")
    with m4: st.metric("Duplicates", df_raw.duplicated().sum())

    if val["issues"]:
        for issue in val["issues"]:
            st.error(f"🚫 {issue}")
    if val["warnings"]:
        for w in val["warnings"]:
            st.warning(f"⚠️ {w}")

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

    # Column types
    st.markdown("**Column Types & Null Counts**")
    col_info = pd.DataFrame({
        "Column":   df_raw.columns,
        "Type":     [str(df_raw[c].dtype) for c in df_raw.columns],
        "Nulls":    [int(df_raw[c].isnull().sum()) for c in df_raw.columns],
        "Null %":   [f"{df_raw[c].isnull().sum()/len(df_raw)*100:.1f}%" for c in df_raw.columns],
        "Unique":   [df_raw[c].nunique() for c in df_raw.columns],
    })
    st.dataframe(col_info, use_container_width=True, hide_index=True)

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    st.markdown("**Sample Data (first 20 rows)**")
    st.dataframe(df_raw.head(20), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYSIS REPORT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("### 📊 Dataset Analysis Report")
    report = generate_dataset_report(df_raw)

    # Distribution charts
    st.markdown("**Availability Distribution**")
    avail_df = pd.DataFrame(
        list(report["availability_dist"].items()),
        columns=["Availability", "Count"]
    )
    st.bar_chart(avail_df.set_index("Availability"), color="#58a6ff", height=220)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Gender Distribution**")
        g_df = pd.DataFrame(list(report["gender_dist"].items()), columns=["Gender","Count"])
        st.bar_chart(g_df.set_index("Gender"), color="#a371f7", height=200)

    with col_b:
        st.markdown("**Organisation Type Distribution**")
        o_df = pd.DataFrame(list(report["org_type_dist"].items()), columns=["Org Type","Count"])
        st.bar_chart(o_df.set_index("Org Type"), color="#3fb950", height=200)

    st.markdown("**Age Band Distribution**")
    ab_df = pd.DataFrame(list(report["age_band_dist"].items()), columns=["Age Band","Count"])
    st.bar_chart(ab_df.set_index("Age Band"), color="#f0883e", height=180)

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    st.markdown("**Top 20 Individual Skills**")
    skills_df = pd.DataFrame(
        list(report["top_skills"].items()), columns=["Skill","Count"]
    ).sort_values("Count", ascending=False)
    st.bar_chart(skills_df.set_index("Skill"), color="#79c0ff", height=300)

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    with st.expander("📋 Full Report Details"):
        st.markdown(f"- **Total skill tokens:** {report['total_skill_tokens']}")
        st.markdown(f"- **Unique skills:** {report['unique_skills']}")
        st.markdown(f"- **Age range:** {report['age_range']['min']} – {report['age_range']['max']} (mean {report['age_range']['mean']})")
        st.markdown("**Availability → App Slot Mapping:**")
        for ds_val, app_val in report["avail_app_mapping"].items():
            st.markdown(f"  - `{ds_val}` → `{app_val}`")
        st.markdown("**Location Distribution:**")
        for loc, cnt in sorted(report["location_dist"].items(), key=lambda x: -x[1]):
            st.markdown(f"  - {loc}: {cnt}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### 🔧 Feature Engineering Preview")
    st.info(
        "Features are engineered to mirror the deterministic engine's 6 components.  \n"
        "A **binary match label** is synthesised based on skill–organisation alignment."
    )

    with st.spinner("Cleaning and engineering features…"):
        df_clean    = clean_dataset(df_raw)
        df_features = engineer_features(df_clean)

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Cleaned Rows",  len(df_clean))
    with m2: st.metric("Features",      len(FEATURE_COLS))
    with m3:
        match_count = int(df_features["match_label"].sum())
        st.metric("Match=1",  match_count)
    with m4:
        no_match = len(df_features) - match_count
        st.metric("Match=0",  no_match)

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

    # Feature correlations with label
    st.markdown("**Feature → Label Correlation**")
    corr_data = {
        feat: round(float(df_features[feat].corr(df_features["match_label"])), 4)
        for feat in FEATURE_COLS
    }
    corr_df = pd.DataFrame(
        list(corr_data.items()), columns=["Feature", "Correlation with Match Label"]
    ).sort_values("Correlation with Match Label", ascending=False)
    st.dataframe(corr_df, use_container_width=True, hide_index=True)

    st.markdown("**Feature Statistics**")
    st.dataframe(
        df_features[FEATURE_COLS + ["match_label"]].describe().round(4),
        use_container_width=True,
    )

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    st.markdown("**Sample Engineered Rows (first 15)**")
    display_cols = ["Volunteer ID", "Skills", "Availability", "Type of Organization"] + FEATURE_COLS + ["match_label"]
    show_cols = [c for c in display_cols if c in df_features.columns]
    st.dataframe(df_features[show_cols].head(15), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — TRAIN MODEL
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("### 🎯 Model Training")

    st.markdown("""
    **Training pipeline:**
    1. Load and clean dataset
    2. Engineer 6 matching features
    3. Train **Logistic Regression** + **Random Forest**
    4. Evaluate both with 5-fold cross-validation
    5. Save the best model automatically to `data/models/match_model.pkl`

    **Why both models?**
    - **Logistic Regression** — linear, highly interpretable, fast, good baseline
    - **Random Forest** — handles non-linearity, feature interactions, usually more accurate
    """)

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

    col_train, col_info = st.columns([1, 2])
    with col_train:
        train_btn = st.button(
            "🚀 Train & Save Best Model",
            key="train_model_btn",
            use_container_width=True,
        )
    with col_info:
        st.caption("Training takes ~5–15 seconds depending on dataset size.")
        st.caption("The best model (by CV F1-score) is saved automatically.")

    if train_btn:
        with st.spinner("Training models… please wait…"):
            try:
                df_c = clean_dataset(df_raw)
                df_e = engineer_features(df_c)
                result = train_best_model(df_e)
                reload_ml_model() if reload_ml_model is not None else None   # clear cache so new model is used immediately
                st.session_state["last_train_result"] = result
                st.success(
                    f"✅ Training complete!  \n"
                    f"**Best model:** {result['best_model_name']}  ·  "
                    f"F1: {result['best_metrics']['f1_score']:.4f}  ·  "
                    f"CV F1: {result['best_metrics']['cv_f1_mean']:.4f}"
                )
                st.rerun()
            except Exception as exc:
                st.error(f"❌ Training failed: {exc}")

    # Show last training logs if available
    if "last_train_result" in st.session_state:
        result = st.session_state["last_train_result"]
        with st.expander("📋 Training Logs"):
            for line in result.get("logs", []):
                st.text(line)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — MODEL METRICS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("### 📈 Model Performance Metrics")

    result = st.session_state.get("last_train_result")

    if not result and not status["exists"]:
        st.info("Train the model first (see **Train Model** tab).")
        st.stop()

    # Use session result if available, else show saved meta
    if result:
        lr_m  = result["lr_metrics"]
        rf_m  = result["rf_metrics"]
        best  = result["best_model_name"]
        fi    = result.get("feature_importances", {})
        cd    = result["class_dist"]

        st.markdown(f"**Best model selected: {best}**")

        # ── Model comparison table ─────────────────────────────────────────────
        st.markdown("#### 📊 Model Comparison")
        comp_df = pd.DataFrame({
            "Metric":             ["Accuracy","Precision","Recall","F1-Score","CV F1 Mean","CV F1 Std"],
            "Logistic Regression":[lr_m["accuracy"], lr_m["precision"], lr_m["recall"],
                                   lr_m["f1_score"],  lr_m["cv_f1_mean"], lr_m["cv_f1_std"]],
            "Random Forest":      [rf_m["accuracy"], rf_m["precision"], rf_m["recall"],
                                   rf_m["f1_score"],  rf_m["cv_f1_mean"], rf_m["cv_f1_std"]],
        })
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        # Metric bar charts
        st.markdown("#### Accuracy Comparison")
        acc_df = pd.DataFrame({
            "Model":    ["Logistic Regression", "Random Forest"],
            "Accuracy": [lr_m["accuracy"],      rf_m["accuracy"]],
            "F1-Score": [lr_m["f1_score"],       rf_m["f1_score"]],
        }).set_index("Model")
        st.bar_chart(acc_df, height=220)

        st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

        # ── Confusion matrices ─────────────────────────────────────────────────
        st.markdown("#### Confusion Matrices")
        cmc1, cmc2 = st.columns(2)

        def _cm_df(cm_list, name):
            cm = np.array(cm_list)
            return pd.DataFrame(
                cm,
                index  =[f"{name} Actual 0", f"{name} Actual 1"],
                columns=[f"Predicted 0", f"Predicted 1"],
            )

        with cmc1:
            st.markdown("**Logistic Regression**")
            st.dataframe(_cm_df(lr_m["confusion_matrix"], "LR"), use_container_width=True)
            tn,fp,fn,tp = np.array(lr_m["confusion_matrix"]).ravel()
            st.caption(f"TN={tn}  FP={fp}  FN={fn}  TP={tp}")

        with cmc2:
            st.markdown("**Random Forest**")
            st.dataframe(_cm_df(rf_m["confusion_matrix"], "RF"), use_container_width=True)
            tn,fp,fn,tp = np.array(rf_m["confusion_matrix"]).ravel()
            st.caption(f"TN={tn}  FP={fp}  FN={fn}  TP={tp}")

        st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

        # ── Feature importances (RF) ───────────────────────────────────────────
        if fi:
            st.markdown("#### 🔍 Feature Importances (Random Forest)")
            fi_df = pd.DataFrame(
                list(fi.items()), columns=["Feature","Importance"]
            ).sort_values("Importance", ascending=False)
            st.bar_chart(fi_df.set_index("Feature"), color="#a371f7", height=250)
            st.caption(
                "Skills overlap has the highest importance (aligned with 40% weight in deterministic engine). "
                "Location is fixed at 1.0 in this dataset (same city assumed)."
            )

        st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

        # ── Classification reports ─────────────────────────────────────────────
        st.markdown("#### Full Classification Reports")
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("**Logistic Regression**")
            st.code(lr_m.get("report","—"), language=None)
        with rc2:
            st.markdown("**Random Forest**")
            st.code(rf_m.get("report","—"), language=None)

        st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

        # ── Class balance ──────────────────────────────────────────────────────
        st.markdown("#### Class Balance")
        cb_df = pd.DataFrame(
            {"Class":["Match=1 (Good)","Match=0 (Poor)"],
             "Count":[cd["match"], cd["no_match"]]}
        ).set_index("Class")
        st.bar_chart(cb_df, color="#ffa657", height=180)
        total = cd["match"] + cd["no_match"]
        st.caption(
            f"Match=1: {cd['match']} ({cd['match']/total*100:.1f}%)  ·  "
            f"Match=0: {cd['no_match']} ({cd['no_match']/total*100:.1f}%)"
        )
    else:
        # Show stored meta if no session result
        m = status["metrics"] or {}
        st.markdown(f"**Saved model:** {status['model_name']}")
        meta_df = pd.DataFrame(
            [(k, v) for k, v in m.items() if k != "confusion_matrix"],
            columns=["Metric","Value"],
        )
        st.dataframe(meta_df, use_container_width=True, hide_index=True)
        if "confusion_matrix" in m:
            st.markdown("**Confusion Matrix**")
            cm = np.array(m["confusion_matrix"])
            cm_df = pd.DataFrame(
                cm,
                index=["Actual 0","Actual 1"],
                columns=["Predicted 0","Predicted 1"],
            )
            st.dataframe(cm_df, use_container_width=True)
        st.info("Re-train the model to see detailed comparison charts.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — SYSTEM INFO
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("### ℹ️ ML System Overview")

    with st.container(border=True):
        st.markdown("**Architecture: Deterministic + ML Hybrid**")
        st.markdown("""
        | Component | Role | Weight |
        |-----------|------|--------|
        | **Deterministic Score** | Primary ranking signal | 100% of sort order |
        | **ML Score** | Secondary reference signal | Display only |
        | Logistic Regression | Baseline linear model | Trained & compared |
        | Random Forest | Ensemble model | Trained & compared |
        """)

    with st.container(border=True):
        st.markdown("**Feature Engineering (6 features — mirror deterministic engine)**")
        feat_df = pd.DataFrame({
            "Feature":            FEATURE_COLS,
            "Deterministic Weight": ["40%","20%","15%","15%","5%","5%"],
            "Description":        [
                "Fraction of required skills covered by volunteer",
                "How well volunteer availability fits organisation type",
                "Exact city match (1.0) or different city (0.3)",
                "Fraction of org cause areas matching volunteer interests",
                "Age-band / experience fitness for org type",
                "Preferred volunteering mode compatibility",
            ],
        })
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.markdown("**Model Files**")
        st.caption(f"Model: `data/models/match_model.pkl`  →  Exists: {status['exists']}")
        st.caption(f"Meta:  `data/models/model_meta.json`")
        st.caption("Dataset: `data/dataset/volunteer_dataset_cleaned_audit.xlsx`")

    with st.container(border=True):
        st.markdown("**FYP Academic Note**")
        st.info(
            "This system uses a **hybrid deterministic + ML approach**.  \n"
            "The deterministic engine (rule-based, 6 weighted features) provides the primary "
            "ranking to ensure transparency and auditability.  \n"
            "The ML layer (Logistic Regression / Random Forest trained on synthesised labels) "
            "provides a secondary confidence score for academic evaluation and comparison.  \n"
            "This approach is fully explainable, reproducible, and suitable for FYP defence."
        )
