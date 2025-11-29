# src/utils/app.py

import streamlit as st
from config.constants import GUIDE_IMG_PATH, LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH

from utils.api_data_loader import load_diners_from_api
from utils.data_loading import load_static_data
from utils.map_renderer import MapRenderer
from utils.search_manager import SearchManager
from utils.session_state import get_session_state


@st.cache_data
def load_app_data(use_api: bool = False, api_url: str = None):
    """
    앱 데이터 로딩을 위한 독립 함수
    
    Args:
        use_api: API를 사용할지 여부 (False면 CSV 사용)
        api_url: API 베이스 URL (None이면 secrets에서 자동 로드)
    """
    if use_api:
        # API에서 데이터 로드
        # api_url이 None이면 load_diners_from_api가 secrets에서 가져옴
        df_diner = load_diners_from_api(api_url=api_url)
        if df_diner.empty:
            st.warning("API 데이터 로딩 실패. CSV 데이터를 사용합니다.")
            use_api = False
    
    if not use_api:
        # 기존 CSV 로딩 방식
        df_diner, _, _, _ = load_static_data(
            LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH, GUIDE_IMG_PATH
        )
        df_diner.rename(columns={"index": "diner_idx"}, inplace=True)
    
    return df_diner


class What2EatApp:
    """What2Eat 앱의 메인 클래스"""

    def __init__(self, use_api: bool = True, api_url: str = None):
        """
        What2EatApp 초기화
        
        Args:
            use_api: API를 사용할지 여부 (False면 CSV 사용)
            api_url: API 베이스 URL (None이면 secrets에서 자동 로드)
        """
        self.session_state = get_session_state()
        self.session_state.initialize()
        self.map_renderer = MapRenderer()
        self.df_diner = load_app_data(use_api=use_api, api_url=api_url)
        self.search_manager = SearchManager(self.df_diner)