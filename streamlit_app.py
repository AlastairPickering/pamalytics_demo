from pathlib import Path
import importlib.util
import sys

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="PAMalytics demo",
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
st.session_state.setdefault("pa_demo_started", False)


def reset_demo():
    if VALIDATED_PATH.exists():
        VALIDATED_PATH.unlink()

    for key in list(st.session_state.keys()):
        if str(key).startswith(("validate_", "val_", "active_dataset", "pa_df_det")):
            st.session_state.pop(key, None)


def apply_demo_display_defaults():
    # Demo-specific display defaults only.
    # These are deliberately the only validation-page settings overridden here.
    st.session_state["validate_lock_freq"] = True
    st.session_state["validate_fmin_khz"] = 0.0
    st.session_state["validate_fmax_khz"] = 100.0
    st.session_state["validate_use_fft_override"] = True
    st.session_state["validate_fft_size"] = 2048


def start_validation_workflow(open_strategy=True):
    st.session_state["pa_demo_started"] = True
    apply_demo_display_defaults()

    if open_strategy:
        st.session_state["validate_strategy_modal_open"] = True

    st.rerun()


def render_welcome():
    st.markdown(
        """
        <style>
        .pa-welcome-wrap {
            max-width: 920px;
            margin: 4rem auto 2rem auto;
            text-align: center;
        }

        .pa-welcome-title {
            font-size: 3.1rem;
            line-height: 3.4rem;
            font-weight: 750;
            margin-bottom: 0.8rem;
        }

        .pa-welcome-subtitle {
            font-size: 1.25rem;
            line-height: 1.8rem;
            color: rgba(49, 51, 63, 0.76);
            max-width: 760px;
            margin: 0 auto 2.2rem auto;
        }

        .pa-workflow-line {
            display: flex;
            justify-content: center;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-bottom: 2.4rem;
            color: rgba(49, 51, 63, 0.78);
            font-size: 1rem;
        }

        .pa-workflow-pill {
            border: 1px solid rgba(49, 51, 63, 0.18);
            border-radius: 999px;
            padding: 0.45rem 0.85rem;
            background: white;
        }

        .pa-welcome-note {
            max-width: 700px;
            margin: 1.8rem auto 0 auto;
            font-size: 0.95rem;
            line-height: 1.45rem;
            color: rgba(49, 51, 63, 0.62);
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pa-welcome-wrap">
            <div class="pa-welcome-title">PAMalytics demo</div>
            <div class="pa-welcome-subtitle">
                Explore a preconfigured acoustic validation project in your browser.
                Choose a review strategy, inspect spectrograms, play time-expanded audio,
                record validation decisions and export the reviewed table.
            </div>
            <div class="pa-workflow-line">
                <div class="pa-workflow-pill">Choose strategy</div>
                <div class="pa-workflow-pill">Review detections</div>
                <div class="pa-workflow-pill">Track progress</div>
                <div class="pa-workflow-pill">Export results</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([0.38, 0.24, 0.38])

    with c2:
        if st.button("Start demo", type="primary", use_container_width=True):
            start_validation_workflow(open_strategy=True)

    st.markdown(
        """
        <div class="pa-welcome-note">
            This hosted demo starts after project setup. The full local PAMalytics application
            also includes classifier-output import, schema mapping and audio-linkage tools.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_validation_app():
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


with st.sidebar:
    st.markdown("### PAMalytics demo")
    st.caption("Preconfigured example project")

    st.divider()

    if st.button("Welcome", use_container_width=True):
        st.session_state["pa_demo_started"] = False
        st.rerun()

    if st.button("Validation workflow", type="primary", use_container_width=True):
        start_validation_workflow(open_strategy=True)

    if st.button("Reset demo", use_container_width=True):
        reset_demo()
        start_validation_workflow(open_strategy=True)


if st.session_state["pa_demo_started"]:
    render_validation_app()
else:
    render_welcome()
