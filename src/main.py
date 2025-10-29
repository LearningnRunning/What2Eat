# src/main.py

import streamlit as st

from config.constants import LOGO_SMALL_IMG_PATH, LOGO_TITLE_IMG_PATH
from pages import chat_page, my_page, ranking_page, search_filter_page, worldcup_page
from pages.onboarding import OnboardingPage
from utils.analytics import load_analytics
from utils.app import What2EatApp
from utils.auth import (
    auth_form,
    check_authentication,
    get_current_user,
    has_completed_onboarding,
    logout,
)


def login_page():
    """로그인 페이지"""
    # 로고와 앱 소개
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_TITLE_IMG_PATH, width=300)

    # 로그인 폼
    auth_form()


def configure_page(is_authenticated: bool = False):
    """페이지 설정"""
    st.set_page_config(
        page_title="머먹?",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded" if is_authenticated else "collapsed",
    )
    st.logo(
        link="https://what2eat-chat.streamlit.app/",
        image=LOGO_SMALL_IMG_PATH,
        icon_image=LOGO_TITLE_IMG_PATH,
    )


def setup_sidebar():
    """사이드바 설정"""
    with st.sidebar:
        # 사용자 정보 표시
        user_info = get_current_user()
        if user_info:
            st.success(f"👋 환영합니다, {user_info.get('displayName', '사용자')}님!")
            st.write(f"📧 {user_info.get('email', '')}")

            if st.button("🚪 로그아웃", use_container_width=True):
                logout()


def main():
    """메인 함수"""
    # 인증 상태 먼저 확인 (페이지 설정 전에 체크)
    is_authenticated = check_authentication()
    
    # 페이지 설정 및 분석 로드
    configure_page(is_authenticated)
    load_analytics()

    # 로그인하지 않은 사용자는 로그인 페이지만 표시
    if not is_authenticated:
        login_page()
        return

    # 첫 로그인 사용자이고 온보딩을 완료하지 않은 경우 또는 강제 온보딩 플래그가 있는 경우 온보딩 페이지 표시
    force_onboarding = st.session_state.get("force_onboarding", False)
    if not has_completed_onboarding() or force_onboarding:
        st.info("🎉 머먹에 오신 것을 환영합니다! 맞춤 추천을 위한 간단한 설정을 진행해주세요.")
        # 강제 온보딩인 경우 메시지 변경
        if force_onboarding:
            st.info("🔄 프로필을 다시 설정합니다. 더 정확한 추천을 위해 정보를 업데이트해주세요!")
            # 강제 온보딩 플래그 리셋
            st.session_state["force_onboarding"] = False

        # 온보딩에서도 app 인스턴스가 필요하므로 먼저 생성
        app = What2EatApp()
        onboarding_page = OnboardingPage(app)
        onboarding_page.render()
        return

    # 로그인된 사용자를 위한 메인 앱
    # 앱 초기화
    if "app" not in st.session_state:
        st.session_state.app = What2EatApp()

    # 사이드바 설정
    setup_sidebar()

    # 페이지 정의
    pages = [
        st.Page(search_filter_page.render, url_path="search", title="맛집 검색", icon="🔍"),
        st.Page(ranking_page.render, url_path="ranking", title="니가 가본 그집", icon="🕺🏽"),
        st.Page(my_page.render, url_path="mypage", title="마이페이지", icon="👤"),
        st.Page(worldcup_page.render, url_path="worldcup", title="맛집 이상형 월드컵", icon="⚽"),
        st.Page(chat_page.render, url_path="chat", title="오늘 머먹?", icon="🤤"),
        
    ]

    # 온보딩 완료 직후라면 chat_page를 기본값으로 설정
    if "onboarding_just_completed" in st.session_state and st.session_state.onboarding_just_completed:
        st.success("🎉 온보딩이 완료되었습니다! 이제 맞춤 추천을 받아보세요.")
        st.session_state.onboarding_just_completed = False

    # 네비게이션 실행
    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()
