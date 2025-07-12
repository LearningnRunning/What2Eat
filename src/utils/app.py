# src/utils/app.py

import streamlit as st
from config.constants import GUIDE_IMG_PATH, LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH

from utils.data_loading import load_static_data
from utils.map_renderer import MapRenderer
from utils.search_manager import SearchManager
from utils.session_state import get_session_state


@st.cache_data
def load_app_data():
    """앱 데이터 로딩을 위한 독립 함수"""
    df_diner, _, _, _ = load_static_data(
        LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH, GUIDE_IMG_PATH
    )
    df_diner.rename(columns={"index": "diner_idx"}, inplace=True)
    return df_diner


class What2EatApp:
    """What2Eat 앱의 메인 클래스"""

    def __init__(self):
        self.session_state = get_session_state()
        self.session_state.initialize()
        self.map_renderer = MapRenderer()
        self.df_diner = load_app_data()
        self.search_manager = SearchManager(self.df_diner)
