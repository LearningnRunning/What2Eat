# src/pages/worldcup_page.py
"""맛집 이상형 월드컵 페이지"""

import streamlit as st

from utils.api_data_loader import load_diners_from_api
from utils.firebase_logger import get_firebase_logger
from utils.worldcup import get_worldcup_manager


def _log_user_activity(activity_type: str, detail: dict) -> bool:
    """사용자 활동 로깅 헬퍼 메서드"""
    logger = get_firebase_logger()
    if "user_info" not in st.session_state or not st.session_state.user_info:
        return False

    uid = st.session_state.user_info.get("localId")
    if not uid:
        return False

    return logger.log_user_activity(uid, activity_type, detail)


def render():
    """월드컵 페이지 렌더링"""
    # 페이지 방문 로그
    _log_user_activity("page_visit", {"page_name": "worldcup"})
    
    # 데이터 로딩 상태 표시
    with st.spinner("음식점 데이터를 불러오는 중..."):
        df_diner = load_diners_from_api()
    
    # 데이터가 비어있으면 에러 메시지 표시
    if df_diner.empty:
        st.error("음식점 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return

    # WorldCupManager 사용 (Redis 통합 버전)
    worldcup_manager = get_worldcup_manager(df_diner)
    worldcup_manager.render_worldcup_page()