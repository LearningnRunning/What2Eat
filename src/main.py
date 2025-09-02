# src/main.py

import streamlit as st

from config.constants import LOGO_SMALL_IMG_PATH, LOGO_TITLE_IMG_PATH
from pages.onboarding import OnboardingPage
from utils.analytics import load_analytics
from utils.app import What2EatApp
from utils.auth import (
    auth_form,
    check_authentication,
    get_current_user,
    get_organized_user_profile,
    get_user_preferences_summary,
    get_user_profile_from_firestore,
    get_user_ratings_summary,
    has_completed_onboarding,
    logout,
    organize_user_profile_data,
)
from utils.firebase_logger import get_firebase_logger
from utils.pages import PageManager
from utils.session_manager import get_session_manager


def initialize_session_state():
    """Fragment 재실행 여부를 확인하기 위한 session_state 설정"""
    if "app_runs" not in st.session_state:
        st.session_state.app_runs = 0
    if "fragment_runs" not in st.session_state:
        st.session_state.fragment_runs = 0


@st.fragment
def login_page_fragment():
    """로그인 페이지 전용 fragment"""
    st.session_state.fragment_runs += 1

    # 로고와 앱 소개
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_TITLE_IMG_PATH, width=300)

    st.markdown("---")

    # 앱 소개
    st.markdown("""
    ## 🍽️ What2Eat에 오신 것을 환영합니다!

    **What2Eat**은 당신의 맛집 탐험을 도와주는 똑똑한 음식점 추천 서비스입니다.

    ### ✨ 주요 기능
    - 🎯 **개인 맞춤 추천**: 위치와 취향을 고려한 맞춤형 음식점 추천
    - 🗺️ **지도 기반 검색**: 원하는 반경 내에서 맛집 찾기
    - 🏆 **쩝슐랭 랭킹**: 검증된 맛집들의 등급별 랭킹
    
    🚀
    """)

    st.markdown("---")

    # 로그인 폼
    auth_form()


@st.fragment
def chat_page_fragment(page_manager: PageManager):
    """chat_page 부분만 부분 재실행"""
    st.session_state.fragment_runs += 1
    page_manager.chat_page()


@st.fragment
def ranking_page_fragment(page_manager: PageManager):
    """ranking_page 부분만 부분 재실행"""
    st.session_state.fragment_runs += 1
    page_manager.ranking_page()


def get_onboarding_history(uid: str):
    """온보딩 이력 조회 (개선된 버전)"""
    logger = get_firebase_logger()

    onboarding_info = {
        "completed": False,
        "completed_date": None,
        "profile_created": False,
        "profile_created_date": None,
        "profile_data": None,
        "taste_ratings_count": 0,
    }

    # 1. 직접 프로필 문서 확인
    try:
        raw_profile_data = get_user_profile_from_firestore(uid)
        if raw_profile_data:
            onboarding_info["profile_created"] = True
            onboarding_info["profile_created_date"] = raw_profile_data.get("created_at")

            # organize_user_profile_data 사용하여 데이터 정리
            onboarding_info["profile_data"] = organize_user_profile_data(
                raw_profile_data
            )

            # 평점 데이터에서 taste_ratings_count 계산
            ratings = raw_profile_data.get("ratings", {})
            onboarding_info["taste_ratings_count"] = len(
                [r for r in ratings.values() if r > 0]
            )
    except Exception as e:
        st.warning(f"프로필 데이터 조회 중 오류: {str(e)}")

    # 2. 온보딩 완료 로그 확인
    if logger.is_available():
        try:
            onboarding_logs = logger.get_user_logs(
                uid, limit=10, collection_name="onboarding_logs"
            )

            for log in onboarding_logs:
                log_type = log.get("type", "")
                timestamp = log.get("timestamp", "")

                if log_type == "onboarding_completed":
                    onboarding_info["completed"] = True
                    onboarding_info["completed_date"] = timestamp
                    break  # 가장 최근 완료 로그만 사용
        except Exception as e:
            st.warning(f"온보딩 로그 조회 중 오류: {str(e)}")

    return onboarding_info


def get_location_history(uid: str):
    """위치 변경 이력 조회"""
    logger = get_firebase_logger()
    if not logger.is_available():
        return []

    # 네비게이션 로그에서 위치 관련 정보 조회
    nav_logs = logger.get_user_logs(uid, limit=20, collection_name="navigation_logs")

    location_changes = []
    for log in nav_logs:
        log_type = log.get("type", "")
        detail = log.get("detail", {})
        timestamp = log.get("timestamp", "")

        if log_type == "location_saved":
            location_changes.append(
                {
                    "type": "위치 저장",
                    "address": detail.get("address", "알 수 없음"),
                    "coordinates": detail.get("coordinates", {}),
                    "timestamp": timestamp,
                }
            )
        elif log_type == "location_change":
            location_changes.append(
                {
                    "type": "위치 변경",
                    "from_page": detail.get("from_page", "알 수 없음"),
                    "timestamp": timestamp,
                }
            )

    return location_changes


def get_restaurant_history(uid: str):
    """클릭한 음식점 이력 조회"""
    logger = get_firebase_logger()
    if not logger.is_available():
        return []

    # 음식점 로그 조회
    restaurant_logs = logger.get_user_logs(
        uid, limit=50, collection_name="restaurant_logs"
    )

    restaurant_history = []
    for log in restaurant_logs:
        log_type = log.get("type", "")
        detail = log.get("detail", {})
        timestamp = log.get("timestamp", "")

        if log_type == "restaurant_click":
            restaurant_history.append(
                {
                    "type": "음식점 클릭",
                    "restaurant_name": detail.get("restaurant_name", "알 수 없음"),
                    "category": detail.get("category", ""),
                    "location": detail.get("location", ""),
                    "grade": detail.get("grade"),
                    "from_page": detail.get("from_page", ""),
                    "timestamp": timestamp,
                    "url": detail.get("restaurant_url", ""),
                }
            )
        elif log_type == "restaurant_detail_view":
            restaurant_history.append(
                {
                    "type": "상세정보 조회",
                    "restaurant_name": detail.get("restaurant_name", "알 수 없음"),
                    "from_page": detail.get("from_page", ""),
                    "timestamp": timestamp,
                }
            )

    return restaurant_history


@st.fragment
def my_page_fragment():
    """마이페이지 부분만 부분 재실행"""
    st.session_state.fragment_runs += 1

    st.title("👤 마이페이지")

    user_info = get_current_user()
    uid = user_info.get("localId")
    if not user_info:
        st.error("❌ 로그인이 필요합니다.")
        return

        uid = user_info.get("localId")

    # 공통 데이터 미리 로드 (한 번만 조회하여 성능 개선)
    user_profile = get_organized_user_profile(uid)
    preferences = get_user_preferences_summary(uid)
    ratings_summary = get_user_ratings_summary(uid)
    restaurant_history = get_restaurant_history(uid)
    location_history = get_location_history(uid)
    onboarding_info = get_onboarding_history(uid)

    # 사용자 기본 정보 표시
    st.header("👋 환영합니다!")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.info(f"📧 **이메일:** {user_info.get('email', '알 수 없음')}")
        st.info(f"👤 **닉네임:** {user_info.get('displayName', '사용자')}")

    with col2:
        # 가입일 표시 (metadata에서)
        metadata = user_info.get("metadata", {})
        if metadata.get("creationTime"):
            from datetime import datetime

            creation_time = datetime.fromtimestamp(metadata["creationTime"] / 1000)
            st.metric("🗓️ 가입일", creation_time.strftime("%Y.%m.%d"))

    with col3:
        # 마지막 로그인 표시
        if metadata.get("lastSignInTime"):
            last_signin = datetime.fromtimestamp(metadata["lastSignInTime"] / 1000)
            st.metric("🔐 마지막 로그인", last_signin.strftime("%m.%d %H:%M"))

    st.divider()

    # 간단한 활동 요약 대시보드
    st.subheader("📊 활동 요약")

    # 요약 정보 조회
    logger = get_firebase_logger()

    if logger.is_available():
        # 통계 정보 수집
        stats = logger.get_user_statistics(uid)

        # 메트릭 표시
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            total_activities = stats.get("total_activities", 0) if stats else 0
            st.metric("🎯 총 활동", f"{total_activities}회")

        with col2:
            rated_count = (
                ratings_summary.get("total_rated", 0) if ratings_summary else 0
            )
            st.metric("⭐ 평가한 음식점", f"{rated_count}개")

        with col3:
            visited_count = len(restaurant_history) if restaurant_history else 0
            st.metric("🍽️ 방문한 음식점", f"{visited_count}개")

        with col4:
            location_changes = len(location_history) if location_history else 0
            st.metric("📍 위치 변경", f"{location_changes}회")

        with col5:
            avg_rating = (
                ratings_summary.get("average_rating", 0) if ratings_summary else 0
            )
            if avg_rating > 0:
                st.metric("🌟 평균 평점", f"{avg_rating:.1f}점")
            else:
                st.metric("🌟 평균 평점", "없음")

    st.divider()

    # 탭으로 구분
    profile_tab, rating_tab, onboarding_tab, location_tab, restaurant_tab = st.tabs(
        ["🎯 내 취향", "⭐ 내 평점", "📝 온보딩 이력", "📍 위치 이력", "🍽️ 음식점 이력"]
    )

    with profile_tab:
        st.subheader("🎯 내 취향 프로필")

        # 미리 로드된 데이터 사용
        if user_profile and preferences:
            # 기본 정보
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📊 기본 정보")
                basic_info = user_profile.get("basic_info", {})
                if basic_info.get("age"):
                    st.info(f"🎂 **나이:** {basic_info['age']}세")
                if basic_info.get("gender"):
                    st.info(f"👤 **성별:** {basic_info['gender']}")

                # 예산 정보
                budget_info = preferences.get("budget_range", {})
                if budget_info.get("regular"):
                    st.info(f"💰 **평상시 예산:** {budget_info['regular']}원")
                if budget_info.get("special"):
                    st.info(f"💎 **특별한 날 예산:** {budget_info['special']}원")

            with col2:
                st.markdown("### 🌶️ 식사 선호도")
                if preferences.get("spice_level"):
                    spice_emoji = {"안매움": "😊", "적당히": "🌶️", "매움": "🔥"}
                    spice_level = preferences["spice_level"]
                    emoji = spice_emoji.get(spice_level, "🌶️")
                    st.info(f"{emoji} **맵기 선호도:** {spice_level}")

                if preferences.get("dining_companions"):
                    companions = ", ".join(preferences["dining_companions"])
                    st.info(f"👥 **주로 함께 식사:** {companions}")

            # 선호 카테고리
            st.markdown("### 🍜 선호하는 음식")
            if preferences.get("food_preferences_large"):
                categories = preferences["food_preferences_large"]
                cols = st.columns(min(len(categories), 4))
                for i, category in enumerate(categories):
                    with cols[i % 4]:
                        st.success(f"✨ {category}")

            # 제한사항
            restrictions = []
            if preferences.get("dislikes"):
                restrictions.extend(preferences["dislikes"])
            if preferences.get("allergies"):
                restrictions.extend(preferences["allergies"])

            if restrictions:
                st.markdown("### 🚫 식사 제한사항")
                restriction_cols = st.columns(min(len(restrictions), 3))
                for i, restriction in enumerate(restrictions):
                    with restriction_cols[i % 3]:
                        st.error(f"❌ {restriction}")

        else:
            st.warning("⚠️ 프로필 정보가 없습니다. 온보딩을 다시 진행해보세요.")

    with rating_tab:
        st.subheader("⭐ 내가 평가한 음식점")

        # 미리 로드된 데이터 사용
        if ratings_summary and ratings_summary.get("total_rated", 0) > 0:
            # 요약 통계
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🍽️ 평가한 음식점", f"{ratings_summary['total_rated']}개")

            with col2:
                st.metric("⭐ 평균 평점", f"{ratings_summary['average_rating']:.1f}점")

            with col3:
                # 가장 많이 준 평점
                distribution = ratings_summary["rating_distribution"]
                if distribution:
                    most_common = max(distribution.items(), key=lambda x: x[1])
                    st.metric("🎯 선호 평점", f"{most_common[0]}점")

            st.divider()

            # 평점 분포 차트
            st.markdown("### 📊 평점 분포")
            if distribution:
                try:
                    import pandas as pd
                except ImportError:
                    st.error("pandas 라이브러리가 필요합니다.")
                    return

                chart_data = pd.DataFrame(
                    [
                        {"평점": f"{star}⭐", "개수": count}
                        for star, count in distribution.items()
                        if count > 0
                    ]
                )

                if not chart_data.empty:
                    st.bar_chart(chart_data.set_index("평점"))

            st.divider()

            # 평가한 음식점 목록
            st.markdown("### 🏪 평가한 음식점 목록")
            rated_restaurants = ratings_summary.get("rated_restaurants", [])

            if rated_restaurants:
                # 평점별로 필터링 옵션
                all_ratings = sorted(
                    set(r["rating"] for r in rated_restaurants), reverse=True
                )
                selected_rating = st.selectbox(
                    "평점별 필터", ["전체"] + [f"{r}점" for r in all_ratings], index=0
                )

                # 필터링
                if selected_rating != "전체":
                    target_rating = int(selected_rating.replace("점", ""))
                    filtered_restaurants = [
                        r for r in rated_restaurants if r["rating"] == target_rating
                    ]
                else:
                    filtered_restaurants = rated_restaurants

                st.info(
                    f"📊 {len(filtered_restaurants)}개 음식점 (총 {len(rated_restaurants)}개 중)"
                )

                # 음식점 목록 표시
                for i, restaurant in enumerate(
                    filtered_restaurants[:20]
                ):  # 최대 20개까지 표시
                    with st.container():
                        col1, col2, col3 = st.columns([1, 3, 1])

                        with col1:
                            # 평점을 별로 표시
                            rating = restaurant["rating"]
                            stars = "⭐" * rating
                            st.write(f"**{stars}**")
                            st.caption(f"{rating}점")

                        with col2:
                            # diner_idx로 실제 음식점 정보 조회할 수 있지만,
                            # 현재는 diner_idx만 있으므로 간단히 표시
                            diner_idx = restaurant.get("diner_idx", "알 수 없음")
                            st.write(f"**음식점 ID:** {diner_idx}")
                            st.caption(
                                "음식점 상세 정보는 온보딩에서 평가한 음식점입니다."
                            )

                        with col3:
                            if restaurant.get("timestamp"):
                                st.caption(f"평가일: {restaurant['timestamp']}")

                        if i < len(filtered_restaurants) - 1:
                            st.divider()

                if len(filtered_restaurants) > 20:
                    st.info(
                        f"💡 {len(filtered_restaurants) - 20}개 음식점이 더 있습니다."
                    )

            else:
                st.info("📝 아직 평가한 음식점이 없습니다.")

        else:
            st.info("⭐ 아직 평가한 음식점이 없습니다.")
            st.markdown("""
            **💡 음식점을 평가하는 방법:**
            1. 온보딩에서 취향 평가하기
            2. 추천받은 음식점에 평점 남기기
            """)

    with onboarding_tab:
        st.subheader("📝 온보딩 완료 이력")

        # 미리 로드된 데이터 사용
        if onboarding_info:
            # 상태 요약
            col1, col2, col3 = st.columns(3)

            with col1:
                if onboarding_info["completed"]:
                    st.success("✅ 온보딩 완료")
                    if onboarding_info["completed_date"]:
                        st.caption(f"완료일: {onboarding_info['completed_date']}")
                else:
                    st.error("❌ 온보딩 미완료")

            with col2:
                if onboarding_info["profile_created"]:
                    st.success("✅ 프로필 생성 완료")
                    if onboarding_info["profile_created_date"]:
                        st.caption(f"생성일: {onboarding_info['profile_created_date']}")
                else:
                    st.warning("⚠️ 프로필 미생성")

            with col3:
                ratings_count = onboarding_info["taste_ratings_count"]
                st.info(f"⭐ 취향 평가: {ratings_count}회")

            # 프로필 데이터가 있으면 요약 정보 표시
            if onboarding_info.get("profile_data"):
                st.divider()
                st.markdown("### 📋 프로필 요약")

                profile_data = onboarding_info["profile_data"]
                summary_col1, summary_col2 = st.columns(2)

                with summary_col1:
                    # 기본 정보
                    basic_info = profile_data.get("basic_info", {})
                    if basic_info.get("age") or basic_info.get("gender"):
                        info_parts = []
                        if basic_info.get("age"):
                            info_parts.append(f"{basic_info['age']}세")
                        if basic_info.get("gender"):
                            info_parts.append(basic_info["gender"])
                        st.info(f"👤 **기본 정보:** {' / '.join(info_parts)}")

                    # 예산 정보
                    budget_info = profile_data.get("budget_info", {})
                    if budget_info.get("regular_budget") or budget_info.get(
                        "special_budget"
                    ):
                        budget_parts = []
                        if budget_info.get("regular_budget"):
                            budget_parts.append(
                                f"평상시: {budget_info['regular_budget']}"
                            )
                        if budget_info.get("special_budget"):
                            budget_parts.append(
                                f"특별한 날: {budget_info['special_budget']}"
                            )
                        st.info(f"💰 **예산:** {' / '.join(budget_parts)}")

                with summary_col2:
                    # 선호도 정보
                    if profile_data.get("spice_level"):
                        st.info(f"🌶️ **맵기 선호도:** {profile_data['spice_level']}")

                    if profile_data.get("dining_companions"):
                        companions = ", ".join(profile_data["dining_companions"][:3])
                        if len(profile_data["dining_companions"]) > 3:
                            companions += "..."
                        st.info(f"👥 **식사 동반자:** {companions}")

                # 선호 카테고리
                if profile_data.get("food_preferences_large"):
                    st.markdown("#### 🍜 선호 음식 카테고리")
                    categories = profile_data["food_preferences_large"]
                    category_cols = st.columns(min(len(categories), 4))
                    for i, category in enumerate(categories):
                        with category_cols[i % 4]:
                            st.success(f"✨ {category}")

            st.divider()

            if not onboarding_info["completed"]:
                st.warning("📝 온보딩을 완료하면 더 정확한 추천을 받을 수 있습니다!")

                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🚀 온보딩 다시 하기"):
                        # 온보딩 플래그 리셋
                        st.session_state["force_onboarding"] = True
                        st.rerun()
                with col2:
                    st.caption("⚠️ 기존 프로필 정보가 새로운 정보로 업데이트됩니다.")
            else:
                # 온보딩이 완료된 경우에도 재설정 옵션 제공
                with st.expander("🔄 프로필 다시 설정하기"):
                    st.warning(
                        "⚠️ **주의:** 기존의 모든 프로필 정보가 삭제되고 새로 설정됩니다."
                    )
                    if st.button("✅ 프로필 재설정 확인", type="primary"):
                        st.session_state["force_onboarding"] = True
                        st.rerun()
        else:
            st.error("온보딩 정보를 불러올 수 없습니다.")

    with location_tab:
        st.subheader("📍 위치 변경 이력")

        # 미리 로드된 데이터 사용
        if location_history:
            st.info(f"📍 총 {len(location_history)}번의 위치 관련 활동이 있습니다.")

            for i, location in enumerate(location_history[:10]):  # 최근 10개만 표시
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])

                    with col1:
                        if location["type"] == "위치 저장":
                            st.success("💾 저장")
                        else:
                            st.info("🔄 변경")

                    with col2:
                        if location["type"] == "위치 저장":
                            st.write(f"**주소:** {location['address']}")
                            coords = location.get("coordinates", {})
                            if coords:
                                st.caption(
                                    f"좌표: {coords.get('lat', 0):.4f}, {coords.get('lon', 0):.4f}"
                                )
                        else:
                            st.write(f"**페이지:** {location['from_page']}")

                    with col3:
                        if location["timestamp"]:
                            st.caption(location["timestamp"])

                    if i < len(location_history) - 1:
                        st.divider()
        else:
            st.info("📍 아직 위치 변경 이력이 없습니다.")

    with restaurant_tab:
        st.subheader("🍽️ 방문한 음식점 이력")

        # 미리 로드된 데이터 사용
        if restaurant_history:
            st.info(f"🍽️ 총 {len(restaurant_history)}개의 음식점과 상호작용했습니다.")

            # 최근 방문한 음식점들을 카드 형태로 표시
            for i, restaurant in enumerate(restaurant_history[:15]):  # 최근 15개만 표시
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

                    with col1:
                        if restaurant["type"] == "음식점 클릭":
                            st.success("👆 클릭")
                        else:
                            st.info("👀 상세보기")

                    with col2:
                        st.write(f"**{restaurant['restaurant_name']}**")
                        details = []
                        if restaurant.get("category"):
                            details.append(restaurant["category"])
                        if restaurant.get("location"):
                            details.append(restaurant["location"])
                        if details:
                            st.caption(" | ".join(details))

                        # 등급 표시
                        if restaurant.get("grade"):
                            grade = restaurant["grade"]
                            stars = "⭐" * int(grade) if grade else ""
                            st.caption(f"등급: {stars} ({grade}점)")

                    with col3:
                        if restaurant.get("from_page"):
                            page_emoji = {"chat": "💬", "ranking": "🏆", "search": "🔍"}
                            emoji = page_emoji.get(restaurant["from_page"], "📱")
                            st.write(f"{emoji}")
                            st.caption(restaurant["from_page"])

                    with col4:
                        if restaurant["timestamp"]:
                            st.caption(restaurant["timestamp"])

                        # 음식점 URL이 있으면 버튼 표시
                        if restaurant.get("url"):
                            st.link_button(
                                "🔗", restaurant["url"], use_container_width=True
                            )

                    if i < len(restaurant_history) - 1:
                        st.divider()
        else:
            st.info("🍽️ 아직 방문한 음식점이 없습니다. 맛집을 찾아보세요!")


@st.fragment
def worldcup_fragment(page_manager: PageManager):
    """chat_page 부분만 부분 재실행"""
    st.session_state.fragment_runs += 1
    page_manager.worldcup_page()


def render_authenticated_sidebar():
    """인증된 사용자를 위한 사이드바 렌더링"""
    with st.sidebar:
        # 사용자 정보 표시
        user_info = get_current_user()
        if user_info:
            st.success(f"👋 환영합니다, {user_info.get('displayName', '사용자')}님!")
            st.write(f"📧 {user_info.get('email', '')}")

            # 토큰 상태 표시 (개발용)
            session_manager = get_session_manager()
            if session_manager.is_token_valid():
                st.success("🔐 세션 활성")
            else:
                st.warning("⚠️ 세션 만료 임박")

            if st.button("🚪 로그아웃", use_container_width=True):
                logout()

        st.divider()

        # 페이지 선택
        page_options = [
            "🤤 오늘 머먹?",
            "🕺🏽 니가 가본 그집",
            "👤 마이페이지",
            "⚽ 맛집 이상형 월드컵",
        ]

        # 온보딩 완료 직후라면 chat_page를 기본값으로 설정
        default_index = 0  # 기본적으로 첫 번째 옵션 (chat_page)

        # 온보딩 완료 직후 감지: 온보딩이 완료되었지만 아직 페이지 선택 기록이 없는 경우
        if "selected_page_history" not in st.session_state:
            st.session_state.selected_page_history = []
            # 온보딩을 막 완료한 사용자는 chat_page로 안내
            if has_completed_onboarding():
                default_index = 0  # chat_page 인덱스

        # 명시적인 온보딩 완료 플래그가 있는 경우
        if (
            "onboarding_just_completed" in st.session_state
            and st.session_state.onboarding_just_completed
        ):
            default_index = 0  # chat_page 인덱스
            st.session_state.onboarding_just_completed = False  # 플래그 리셋

        selected_page = st.radio("페이지 선택", page_options, index=default_index)

        # 페이지 선택 기록 추가
        if selected_page not in st.session_state.selected_page_history:
            st.session_state.selected_page_history.append(selected_page)

        return selected_page


def configure_page():
    """페이지 설정"""
    st.set_page_config(
        page_title="머먹?",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.logo(
        link="https://what2eat-chat.streamlit.app/",
        image=LOGO_SMALL_IMG_PATH,
        icon_image=LOGO_TITLE_IMG_PATH,
    )


def main():
    """메인 함수"""
    # 초기 설정 (session_state 초기화를 먼저 실행)
    initialize_session_state()

    # 전체 앱 실행 횟수 카운트
    st.session_state.app_runs += 1

    # 페이지 설정 및 분석 로드
    configure_page()
    load_analytics()

    # 인증 상태 확인 및 세션 복원
    is_authenticated = check_authentication()

    # 로그인하지 않은 사용자는 로그인 페이지만 표시
    if not is_authenticated:
        login_page_fragment()
        return

    # 첫 로그인 사용자이고 온보딩을 완료하지 않은 경우 또는 강제 온보딩 플래그가 있는 경우 온보딩 페이지 표시
    force_onboarding = st.session_state.get("force_onboarding", False)
    if not has_completed_onboarding() or force_onboarding:
        st.info(
            "🎉 머먹에 오신 것을 환영합니다! 맞춤 추천을 위한 간단한 설정을 진행해주세요."
        )
        # 강제 온보딩인 경우 메시지 변경
        if force_onboarding:
            st.info(
                "🔄 프로필을 다시 설정합니다. 더 정확한 추천을 위해 정보를 업데이트해주세요!"
            )
            # 강제 온보딩 플래그 리셋
            st.session_state["force_onboarding"] = False

        # 온보딩에서도 app 인스턴스가 필요하므로 먼저 생성
        app = What2EatApp()
        onboarding_page = OnboardingPage(app)
        onboarding_page.render()
        return

    # 로그인된 사용자를 위한 메인 앱
    # 앱 초기화
    app = What2EatApp()
    page_manager = PageManager(app)

    # 사이드바 렌더링 및 페이지 선택
    selected_page = render_authenticated_sidebar()

    # 온보딩 완료 직후 환영 메시지 표시
    if (
        "selected_page_history" in st.session_state
        and len(st.session_state.selected_page_history) == 1
        and selected_page == "🤤 오늘 머먹?"
        and has_completed_onboarding()
    ):
        st.success("🎉 온보딩이 완료되었습니다! 이제 맞춤 추천을 받아보세요.")

    # 선택된 페이지에 따라 해당 함수 호출
    if selected_page == "🤤 오늘 머먹?":
        chat_page_fragment(page_manager)
    elif selected_page == "🕺🏽 니가 가본 그집":
        ranking_page_fragment(page_manager)
    elif selected_page == "👤 마이페이지":
        my_page_fragment()
    elif selected_page == "⚽ 맛집 이상형 월드컵":
        worldcup_fragment(page_manager)


if __name__ == "__main__":
    main()
