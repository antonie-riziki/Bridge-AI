"""Run the BridgeAI interface with: streamlit run app.py"""

import streamlit as st

from bridgeai.app import compare_page, inject_css
from bridgeai.ui.guide import guide_page
from bridgeai.ui.limits import limits_page
from bridgeai.ui.places import places_page

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
