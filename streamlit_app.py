from pathlib import Path
import importlib.util
import sys

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PAMalytics validation demo",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT / "demo_project"
DETECTIONS_PATH = PROJECT_ROOT / "data_normalised" / "detections_normalised.csv"
VALIDATED_PATH = PROJECT_ROOT / "data_normalised" / "detections_validated.csv"
VALIDATION_IMPL = APP_ROOT / "validation_impl.py"

st.session_state.setdefault("auth_user", "reviewer")
st.session_state.setdefault("user_name", "reviewer")
st.session_state.setdefault("current_project", str(PROJECT_ROOT))
st.session_state.setdefault("pa_review_demo", True)
st.session_state.setdefault("validate_strategy_goal", "representative_sample")
st.session_state.setdefault("validate_strategy_balance", "species_confidence")
st.session_state.setdefault("validate_strategy_target_mode", "total_clips")
st.session_state.setdefault("validate_strategy_target_value", 100)
st.session_state.setdefault("validate_strategy_bins", 5)
st.session_state.setdefault("validate_strategy_seed", 42)
st.session_state.setdefault("validate_num_per_page", 10)
st.session_state.setdefault("validate_cols_per_row", 2)

with st.sidebar:
    st.markdown("### PAMalytics demo")
    st.caption("Preconfigured example project")
    if st.button("Reset demo", key="reset_demo"):
        try:
            if VALIDATED_PATH.exists():
                VALIDATED_PATH.unlink()
            for k in list(st.session_state.keys()):
                if str(k).startswith(("validate_", "val_", "active_dataset", "pa_df_det")):
                    st.session_state.pop(k, None)
            st.session_state["validate_strategy_goal"] = "representative_sample"
            st.session_state["validate_strategy_balance"] = "species_confidence"
            st.session_state["validate_strategy_target_mode"] = "total_clips"
            st.session_state["validate_strategy_target_value"] = 100
            st.session_state["validate_strategy_bins"] = 5
            st.session_state["validate_strategy_seed"] = 42
            st.session_state["validate_num_per_page"] = 10
            st.session_state["validate_cols_per_row"] = 2
            st.rerun()
        except Exception as e:
            st.error(f"Could not reset demo: {e}")

if not PROJECT_ROOT.exists():
    st.error(f"Demo project not found: {PROJECT_ROOT}")
    st.stop()

if not DETECTIONS_PATH.exists():
    st.error(f"Demo detections file not found: {DETECTIONS_PATH}")
    st.stop()

if not VALIDATION_IMPL.exists():
    st.error(f"Validation implementation not found: {VALIDATION_IMPL}")
    st.stop()

try:
    df_det = pd.read_csv(DETECTIONS_PATH, low_memory=False)
except Exception as e:
    st.error(f"Could not load demo detections: {e}")
    st.stop()

sources = {
    "project": str(PROJECT_ROOT),
    "project_root": str(PROJECT_ROOT),
}

spec = importlib.util.spec_from_file_location("pamalytics_validation_impl", VALIDATION_IMPL)
if spec is None or spec.loader is None:
    st.error("Could not load the validation module.")
    st.stop()

mod = importlib.util.module_from_spec(spec)
sys.modules["pamalytics_validation_impl"] = mod

try:
    spec.loader.exec_module(mod)
except Exception as e:
    st.error(f"Import error in validation module: {e}")
    st.stop()

render_validation = getattr(mod, "render_validation", None)
if render_validation is None or not callable(render_validation):
    st.error("Validation module does not expose render_validation().")
    st.stop()

render_validation(df_det, sources)
