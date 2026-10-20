"""Run the BridgeAI interface with: streamlit run app.py"""

import sys
from pathlib import Path

import streamlit as st

# Community Cloud starts from the repository root. Keep that directory
# importable even if the process was launched with a cleaned sys.path.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Named compare, not app: Community Cloud otherwise loads this entrypoint
# when the app asks for bridgeai.app.
try:
    from bridgeai.compare import compare_page, inject_css
    from bridgeai.ui.guide import guide_page
    from bridgeai.ui.limits import limits_page
    from bridgeai.ui.places import places_page
except ImportError as exc:
    missing = getattr(exc, "name", None) or "unknown"
    raise ImportError(
        "BridgeAI could not import "
        + str(missing)
        + ". Set the main file to app.py in the repository root and install requirements.txt."
    ) from None

st.set_page_config(
    page_title="BridgeAI",
    page_icon="B",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

navigation = st.navigation(
    [
        st.Page(compare_page, title="Compare notices", default=True),
        st.Page(places_page, title="Places", url_path="places"),
        st.Page(guide_page, title="How to read a result", url_path="how-to-read"),
        st.Page(limits_page, title="Limits", url_path="limits"),
    ]
)
st.sidebar.caption(
    "BridgeAI compares notices you paste. It is not a news, medical, or emergency service."
)
navigation.run()
