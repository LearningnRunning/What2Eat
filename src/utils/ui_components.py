# src/uils/ui_components.py
import random

import pandas as pd
import pydeck as pdk
import streamlit as st
from streamlit_chat import message

from utils.data_processing import grade_to_stars, safe_item_access
from utils.firebase_logger import get_firebase_logger


@st.cache_data
def choice_avatar():
    avatar_style_list = [
        "avataaars",
        "pixel-art-neutral",
        "adventurer-neutral",
        "big-ears-neutral",
    ]
    seed_list = [100, "Felix"] + list(range(1, 140))

    avatar_style = random.choice(avatar_style_list)
    seed = random.choice(seed_list)
    return avatar_style, seed


# 메시지 카운터 변수 추가
message_counter = 0


def my_chat_message(message_txt, choiced_avatar_style, choiced_seed):
    global message_counter
    message_counter += 1
    return message(
        message_txt,
        avatar_style=choiced_avatar_style,
        seed=choiced_seed,
        key=f"message_{message_counter}",
    )


@st.dialog("주변 맛집 지도")
def display_maps(df_filtered):
    # 현재 위치 데이터
    current_location = pd.DataFrame(
        {
            "lat": [st.session_state.user_lat],
            "lon": [st.session_state.user_lon],
            "name": ["현재 위치"],
            "color": [[0, 0, 255]],  # 파란색(현재 위치)
            "url": [""],  # 현재 위치는 URL 없음
        }
    )

    # 음식점 데이터 준비 (순위별로 다른 색상)
    restaurants = []
    for idx, row in df_filtered.iterrows():
        grade_num = row["diner_grade"]
        if grade_num >= 3:
            color = [255, 0, 0]  # 빨간색
        elif grade_num == 2:
            color = [255, 69, 0]  # 주황빨간색
        else:
            color = [255, 140, 0]  # 주황색

        restaurants.append(
            {
                "lat": row["diner_lat"],
                "lon": row["diner_lon"],
                "name": f"{row['diner_name']}",
                "color": color,
                "url": row["diner_url"],
            }
        )

    # 데이터프레임 생성
    restaurant_df = pd.DataFrame(restaurants)
    map_data = pd.concat([current_location, restaurant_df])

    # 지도 중심점 계산
    center_lat = (map_data["lat"].max() + map_data["lat"].min()) / 2
    center_lon = (map_data["lon"].max() + map_data["lon"].min()) / 2

    # 레이어 설정
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius=2,
        pickable=True,
        radiusScale=2,
        onClick=True,
        auto_highlight=True,
        highlight_color=[255, 255, 0, 100],  # 하이라이트 색상
        hover_distance=100,  # 마우스오버 감지 거리
    )

    # 지도 설정
    view_state = pdk.ViewState(
        latitude=center_lat, longitude=center_lon, zoom=16, pitch=50
    )

    # 툴팁 HTML 템플릿
    tooltip_html = """
    <div style="
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        position: sticky;
        top: 0;
        z-index: 1000;
    ">
        <strong>{name}</strong><br/>
        <a href="{url}" target="_blank" 
           style="
               display: inline-block;
               margin-top: 5px;
               padding: 5px 10px;
               background-color: #FEE500;
               color: #000;
               text-decoration: none;
               border-radius: 5px;
               font-weight: bold;
           "
        >
            카카오맵에서 보기
        </a>
    </div>
    """

    # 지도 렌더링
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": tooltip_html,
            "style": {
                "position": "fixed",
                "right": "10px",
                "top": "10px",
                "z-index": "10000",
                "pointer-events": "auto",  # 툴팁 내 클릭 가능하도록 설정
                "display": "block",  # 항상 표시
            },
        },
        map_style="mapbox://styles/mapbox/light-v10",
    )

    st.pydeck_chart(deck, use_container_width=True)

    # 범례 표시
    st.write("🎯 **색깔별 쩝슐랭 표시**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🔴  🌟🌟🌟")
    with col2:
        st.markdown("🟠  🌟🌟")
    with col3:
        st.markdown("🟡  🌟")

    st.markdown("💡 **마커를 더블 클릭하면 카카오맵으로 이동합니다**")


def display_results(df_filtered, radius_int, radius_str, avatar_style, seed):
    df_filtered = df_filtered.sort_values(by="bayesian_score", ascending=False)
    if not len(df_filtered):
        my_chat_message(
            "헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed
        )
    else:
        # 지도로 보기 버튼 추가
        if st.button("📍 모든 음식점 지도로 보기"):
            # 지도 보기 로그 (강화된 버전)
            logger = get_firebase_logger()
            if "user_info" in st.session_state and st.session_state.user_info:
                uid = st.session_state.user_info.get("localId")
                if uid:
                    logger.log_map_view(
                        uid=uid,
                        restaurants_count=len(df_filtered),
                        radius_km=radius_int,
                        from_page="chat",
                    )
            display_maps(df_filtered)

        # 정렬 옵션 선택
        sort_option = st.radio(
            "정렬 기준",
            ["추천순", "리뷰 많은 순", "거리순"],
            horizontal=True,
            key="sort_option",
        )

        # 정렬 옵션 변경 로깅
        if "previous_sort_option" not in st.session_state:
            st.session_state.previous_sort_option = sort_option
        elif st.session_state.previous_sort_option != sort_option:
            logger = get_firebase_logger()
            if "user_info" in st.session_state and st.session_state.user_info:
                uid = st.session_state.user_info.get("localId")
                if uid:
                    logger.log_sort_option_change(
                        uid=uid, sort_option=sort_option, from_page="chat"
                    )
            st.session_state.previous_sort_option = sort_option

        # 선택한 옵션에 따라 정렬
        if sort_option == "리뷰 많은 순":
            # 리뷰 많은 순으로 정렬
            df_sorted = df_filtered.sort_values(
                by=["diner_grade", "diner_review_cnt"], ascending=[False, False]
            )
        elif sort_option == "거리순":
            # 거리순으로 정렬
            df_sorted = df_filtered.sort_values(
                by=["distance", "diner_grade"], ascending=[True, False]
            )
        else:  # 추천순(기본값)
            # 등급 높은 순 + 베이지안 점수 높은 순
            df_sorted = df_filtered.sort_values(
                by=["diner_grade", "bayesian_score"], ascending=[False, False]
            )

        # 나쁜 리뷰와 좋은 리뷰를 분리
        bad_reviews = []
        good_reviews = []

        # 문제가 되는 부분 수정 - copy 생성 후 fillna 적용
        df_filtered_copy = df_filtered.copy()
        df_filtered_copy["diner_category_middle"] = df_filtered_copy[
            "diner_category_middle"
        ].fillna(df_filtered_copy["diner_category_large"])

        for _, row in df_sorted.iterrows():
            if (
                row["real_bad_review_percent"] is not None
                and row["real_bad_review_percent"] > 20
            ):
                bad_reviews.append(row)  # 나쁜 리뷰로 분리
            else:
                good_reviews.append(row)  # 좋은 리뷰로 분리

        # 소개 메시지 초기화
        introduction = f"{radius_str} 근처 \n {len(df_filtered)}개의 인증된 곳 발견! ({sort_option})\n\n"

        # 좋은 리뷰 처리 (이미 정렬되어 있음)
        for row in good_reviews:
            # 리스트 처리를 위한 안전 처리 추가
            introduction += generate_introduction(
                row["diner_idx"],
                row["diner_name"],
                row["diner_review_cnt"],
                radius_int,
                int(row["distance"] * 1000),
                row["diner_category_middle"],
                row["diner_grade"],
                row["diner_tag"],
                row["diner_menu_name"],
                row.get("score"),
            )

        # 나쁜 리뷰 처리 (이미 정렬되어 있음)
        for row in bad_reviews:
            introduction += f"\n🚨 주의: [{row['diner_name']}](https://place.map.kakao.com/{row['diner_idx']})의 비추 리뷰가 {round(row['real_bad_review_percent'], 2)}%입니다.\n"

        # 최종 메시지 전송
        my_chat_message(introduction, avatar_style, seed)

        # 음식점별 클릭 버튼 추가 (로깅을 위해)
        st.subheader("🔗 음식점 바로가기")

        # 좋은 리뷰 음식점들
        for idx, row in enumerate(good_reviews[:5]):  # 상위 5개만 표시
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['diner_name']}** - {row['diner_category_middle']}")
            with col2:
                if st.button("보러가기", key=f"visit_{idx}_{row['diner_name']}"):
                    # 음식점 클릭 로깅 (강화된 버전)
                    logger = get_firebase_logger()
                    if "user_info" in st.session_state and st.session_state.user_info:
                        uid = st.session_state.user_info.get("localId")
                        if uid:
                            logger.log_restaurant_click(
                                uid=uid,
                                restaurant_name=row["diner_name"],
                                restaurant_url=f"https://place.map.kakao.com/{row['diner_idx']}",
                                restaurant_idx=str(row.get("diner_idx", "")),
                                category=row["diner_category_middle"],
                                location=None,  # 지역 정보가 없는 경우
                                grade=row.get("diner_grade"),
                                review_count=row.get("diner_review_cnt"),
                                distance=row.get("distance"),
                                from_page="chat_results",
                            )
                    # 새 탭에서 음식점 페이지 열기
                    st.link_button(
                        "음식점 보기", f"https://place.map.kakao.com/{row['diner_idx']}"
                    )


def generate_introduction(
    diner_idx,
    diner_name,
    diner_review_cnt,
    radius_kilometers,
    distance,
    diner_category_small,
    diner_grade,
    diner_tags,
    diner_menus,
    recommend_score=None,
):
    # 기본 정보
    introduction = f"[{diner_name}](https://place.map.kakao.com/{diner_idx})"

    if diner_name:
        introduction += f" ({diner_category_small})\n"
    else:
        introduction += "\n"

    # 추천 점수 및 주요 정보
    if recommend_score is not None:
        introduction += f"🍽️ 쩝쩝상위 {diner_grade}%야!\n"
        introduction += f"👍 추천지수: {recommend_score}%\n"
        introduction += f"👍 리뷰 수: {diner_review_cnt}\n"
        if diner_tags:
            introduction += f"🔑 키워드: {safe_item_access(diner_tags)}\n"
        if diner_menus:
            introduction += f"🍴 메뉴: {safe_item_access(diner_menus, 3)}\n"
    else:
        introduction += f"{grade_to_stars(diner_grade)}"
        if diner_review_cnt:
            introduction += f"👍 리뷰 수: {diner_review_cnt}\n"

        if diner_tags:
            introduction += f"🔑 키워드: {safe_item_access(diner_tags, 5)}\n"
        if diner_menus:
            introduction += f"🍴 메뉴: {safe_item_access(diner_menus, 3)}\n"

    # 거리 정보 추가
    if radius_kilometers >= 0.5:
        introduction += f"📍 여기서 {distance}M 정도 떨어져 있어!\n\n"
    else:
        introduction += "\n\n"

    return introduction
