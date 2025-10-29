# src/pages/ranking_page.py
"""랭킹 페이지"""

import streamlit as st

from config.constants import GRADE_MAP
from utils.app import What2EatApp
from utils.data_processing import grade_to_stars
from utils.dialogs import change_location, show_restaurant_map
from utils.firebase_logger import get_firebase_logger


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
    """랭킹 페이지 렌더링"""
    # 페이지 방문 로그
    _log_user_activity("page_visit", {"page_name": "ranking"})

    # 앱 인스턴스 가져오기
    if "app" not in st.session_state:
        st.session_state.app = What2EatApp()
    app = st.session_state.app

    st.title("지역별 카테고리 랭킹")

    # 현재 위치 표시 및 수정 옵션
    st.subheader("📍 현재 위치")
    if "address" not in st.session_state:
        change_location()
    else:
        st.write(st.session_state.address)
        if st.button("위치 변경"):
            change_location()
            _log_user_activity("location_change", {"from_page": "ranking"})

    # 쩝슐랭 등급 선택
    st.subheader("🏅 쩝슐랭 등급 선택")
    selected_grades = st.multiselect(
        "보고 싶은 쩝슐랭 등급을 선택하세요 (다중 선택 가능)",
        options=["🌟", "🌟🌟", "🌟🌟🌟"],
        default=["🌟🌟🌟"],
    )
    selected_grade_values = [GRADE_MAP[grade] for grade in selected_grades]

    # 지역 선택
    app.df_diner[["city", "region"]] = (
        app.df_diner["diner_num_address"].str.split(" ", n=2, expand=True).iloc[:, :2]
    )

    ZONE_LIST = list(app.df_diner["city"].unique())
    zone = st.selectbox("지역을 선택하세요", ZONE_LIST, index=0)
    selected_zone_all = f"{zone} 전체"

    # 선택한 지역의 데이터 필터링
    filtered_zone_df = app.df_diner[app.df_diner["city"] == zone]

    # 상세 지역 선택
    city_options = list(filtered_zone_df["region"].dropna().unique())
    city_label = st.selectbox("상세 지역을 선택하세요", [selected_zone_all] + city_options)

    if city_label:
        filtered_zone_df["diner_category_large"] = filtered_zone_df[
            "diner_category_large"
        ].fillna("기타")
        if city_label == selected_zone_all:
            filtered_city_df = filtered_zone_df
        else:
            filtered_city_df = filtered_zone_df[filtered_zone_df["region"] == city_label]

        # 중간 카테고리 선택 및 필터링
        available_categories = filtered_city_df["diner_category_large"].unique()
        selected_category = st.selectbox(
            "중간 카테고리를 선택하세요", ["전체"] + list(available_categories)
        )

        if selected_category != "전체":
            filtered_city_df = filtered_city_df[
                filtered_city_df["diner_category_large"] == selected_category
            ]
            _log_user_activity(
                "category_filter",
                {
                    "category": selected_category,
                    "location": city_label,
                    "from_page": "ranking",
                },
            )

        # 세부 카테고리 선택 및 필터링
        available_small_categories = (
            filtered_city_df["diner_category_middle"].fillna("기타").unique()
        )
        selected_small_category = st.selectbox(
            "세부 카테고리를 선택하세요", ["전체"] + list(available_small_categories)
        )

        if selected_small_category != "전체":
            filtered_city_df = filtered_city_df[
                filtered_city_df["diner_category_middle"] == selected_small_category
            ]

        # 쩝슐랭 등급 필터링
        filtered_city_df = filtered_city_df[
            filtered_city_df["diner_grade"].isin(selected_grade_values)
        ]

        # 랭킹 조회 로그
        _log_user_activity(
            "ranking_view",
            {
                "location": city_label,
                "category": selected_category,
                "small_category": selected_small_category,
                "grades": selected_grades,
                "results_count": len(filtered_city_df),
            },
        )

        # 세부 카테고리별 랭킹 표시
        st.subheader(
            f"{selected_category if selected_category != '전체' else '전체 중간 카테고리'} 카테고리 ({selected_small_category if selected_small_category != '전체' else '전체'}) 랭킹"
        )

        # 복사본을 만들고 fillna 적용
        filtered_city_df_copy = filtered_city_df.copy()
        filtered_city_df_copy["diner_category_middle"] = filtered_city_df_copy[
            "diner_category_middle"
        ].fillna(filtered_city_df_copy["diner_category_large"])

        ranked_df = filtered_city_df_copy.sort_values(by="bayesian_score", ascending=False)[
            [
                "diner_name",
                "diner_url",
                "diner_category_middle",
                "diner_grade",
                "diner_lat",
                "diner_lon",
                "diner_menu_name",
                "diner_tag",
                "diner_num_address",
                "region",
            ]
        ]

        if not ranked_df.empty:
            # 지도 다이얼로그를 위한 상태 추가
            if "show_map" not in st.session_state:
                st.session_state.show_map = False
            if "selected_restaurant" not in st.session_state:
                st.session_state.selected_restaurant = None

            # 음식점 목록을 카드 형태로 표시
            ranked_df = ranked_df[:100]
            for _, row in ranked_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.write(grade_to_stars(row["diner_grade"]))
                    with col2:
                        # 음식점 링크 클릭 로그
                        if st.button(
                            f"**{row['diner_name']}** | {row['diner_category_middle']} | {row['region']}",
                            key=f"link_{row['diner_name']}",
                        ):
                            # 강화된 음식점 클릭 로깅
                            logger = get_firebase_logger()
                            if "user_info" in st.session_state and st.session_state.user_info:
                                uid = st.session_state.user_info.get("localId")
                                if uid:
                                    logger.log_restaurant_click(
                                        uid=uid,
                                        restaurant_name=row["diner_name"],
                                        restaurant_url=row["diner_url"],
                                        restaurant_idx=str(row.get("diner_idx", "")),
                                        category=row["diner_category_middle"],
                                        location=row["region"],
                                        grade=row.get("diner_grade"),
                                        review_count=row.get("diner_review_cnt"),
                                        distance=row.get("distance"),
                                        from_page="ranking",
                                    )
                            st.link_button("음식점 보기", row["diner_url"])
                    with col3:
                        if st.button("상세정보", key=f"map_{row['diner_name']}"):
                            st.session_state.show_map = True
                            st.session_state.selected_restaurant = row
                            # 상세정보 조회 로그
                            logger = get_firebase_logger()
                            if "user_info" in st.session_state and st.session_state.user_info:
                                uid = st.session_state.user_info.get("localId")
                                if uid:
                                    logger.log_restaurant_detail_view(
                                        uid=uid,
                                        restaurant_name=row["diner_name"],
                                        restaurant_idx=str(row.get("diner_idx", "")),
                                        from_page="ranking",
                                    )
                            show_restaurant_map(st.session_state.selected_restaurant)
                    st.divider()
        else:
            st.warning("해당 조건의 랭킹 데이터가 없습니다.")

