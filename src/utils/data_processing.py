# src/utils/data_processing.py

from math import atan2, cos, radians, sin, sqrt

import matplotlib.colors as mcolors  # 색상 변환에 사용
import pandas as pd
import streamlit as st


# 리스트나 기타 iterable 객체를 안전하게 처리하는 함수 추가
def safe_item_access(item, index=None):
    """
    리스트나 기타 iterable 객체를 안전하게 처리하는 함수

    Args:
        item: 처리할 아이템 (리스트, 문자열 등)
        index: 리스트인 경우 접근할 인덱스 (None이면 모든 요소 접근)

    Returns:
        안전하게 처리된 아이템
    """
    if item is None:
        return ""

    # 리스트인 경우
    if isinstance(item, list):
        if index is not None:
            # 특정 인덱스까지 접근 (ex: [:3])
            items = item[:index]
        else:
            # 전체 리스트 사용
            items = item
        # 리스트 요소들을 문자열로 변환하여 조인
        return "/".join(str(i) for i in items)

    # 문자열 또는 기타 타입의 경우 그대로 반환
    return str(item)


@st.cache_data
def get_filtered_data(df, user_lat, user_lon, max_radius=30):
    df["distance"] = df.apply(
        lambda row: haversine(user_lat, user_lon, row["diner_lat"], row["diner_lon"]),
        axis=1,
    )

    # 거리 계산 및 필터링
    filtered_df = df[df["distance"] <= max_radius]
    return filtered_df


@st.cache_data
def category_filters(diner_category, df_diner_real_review, df_diner):
    category_filted_df = df_diner_real_review.query(
        "diner_category_large in @diner_category"
    )

    return category_filted_df


def select_radius(avatar_style, seed):
    radius_distance = st.selectbox(
        "어디", ["300m", "500m", "1km", "3km", "10km"], label_visibility="hidden"
    )
    st.session_state.radius_kilometers = {
        "300m": 0.3,
        "500m": 0.5,
        "1km": 1,
        "3km": 3,
        "10km": 10,
    }[radius_distance]
    st.session_state.radius_distance = radius_distance
    return st.session_state.radius_kilometers, st.session_state.radius_distance


# 색상 코드 (#FF5733)를 [R, G, B, A] 형식으로 변환하는 함수
def hex_to_rgba(hex_color, alpha=160):
    rgb = mcolors.hex2color(hex_color)  # (R, G, B) 값 반환 (0~1)
    rgb_scaled = [int(c * 255) for c in rgb]  # 0~255로 변환
    return rgb_scaled + [alpha]  # [R, G, B, A] 반환


def grade_to_stars(diner_grade):
    if diner_grade == 0:
        return ""
    return f"🏅 쩝슐랭 {'🌟' * diner_grade} \n"  # 이모티콘 개수 반복


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c

    return distance


def filter_recommendations_by_distance_memory(
    recommended_items_df, user_lat, user_lon, radius
):
    # 거리 계산
    distances = recommended_items_df.apply(
        lambda row: haversine(user_lat, user_lon, row["diner_lat"], row["diner_lon"]),
        axis=1,
    )
    recommended_items_df["distance"] = distances
    # 반경 내의 아이템 필터링
    filtered_df = recommended_items_df[recommended_items_df["distance"] <= radius]
    return filtered_df


def predict_rating(user_id, item_id, algo):
    prediction = algo.predict(user_id, item_id)
    return prediction.est


def recommend_items(
    user_id, user_item_matrix, user_similarity_df, num_recommendations=10
):
    # 해당 사용자의 유사도 가져오기
    similar_users = (
        user_similarity_df[user_id].drop(user_id).sort_values(ascending=False)
    )

    # 유사한 사용자가 선호하는 아이템 추출
    similar_users_indices = similar_users.index
    similar_users_ratings = user_item_matrix.loc[similar_users_indices]

    # 평균 평점 계산
    recommendation_scores = similar_users_ratings.mean(axis=0)

    # 이미 평가한 아이템 제거
    user_rated_items = user_item_matrix.loc[user_id].dropna().index
    recommendation_scores = recommendation_scores.drop(
        user_rated_items, errors="ignore"
    )

    # 상위 추천 아이템 반환
    top_items = recommendation_scores.sort_values(ascending=False).head(
        num_recommendations
    )
    top_items_df = pd.DataFrame({
        "diner_idx": top_items.index,
        "score": top_items.values,
    })

    return top_items_df


def recommend_items_model(user_id, algo, trainset, num_recommendations=5):
    # 사용자가 trainset에 존재하는지 확인
    try:
        inner_uid = trainset.to_inner_uid(user_id)
        user_rated_items = set([j for (j, _) in trainset.ur[inner_uid]])
    except ValueError:
        # 사용자가 trainset에 없을 경우 빈 집합으로 초기화
        user_rated_items = set()

    all_items = set(trainset.all_items())
    unrated_items = all_items - user_rated_items

    # 아이템에 대한 예측 평점 계산
    predictions = []
    for inner_iid in unrated_items:
        raw_iid = trainset.to_raw_iid(inner_iid)
        est = algo.predict(user_id, raw_iid).est
        predictions.append((raw_iid, est))

    # 예측 평점 기준으로 정렬하여 상위 추천
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_items = predictions[:num_recommendations]
    top_items_df = pd.DataFrame(top_items, columns=["diner_idx", "score"])

    return top_items_df


@st.cache_data
def category_filters(diner_category, df_diner_real_review):
    category_filted_df = df_diner_real_review.query(
        "diner_category_large in @diner_category"
    )

    return category_filted_df


# 랜덤 뽑기 함수
@st.cache_data
def pick_random_diners(df, num_to_select=25):
    high_grade_diners = df[df["diner_grade"] >= 2]
    # 조건: 이미 선택된 카테고리는 제외
    available_diners = high_grade_diners[
        ~high_grade_diners["diner_category_small"].isin(
            st.session_state.previous_category_small
        )
    ]

    # 모든 카테고리가 선택된 경우 초기화
    if available_diners.empty:
        st.session_state.previous_category_small.clear()

        # 5번 연속 실패 시 None 반환
        st.session_state.consecutive_failures += 1
        if st.session_state.consecutive_failures >= 5:
            return None

        available_diners = high_grade_diners

    # 랜덤으로 num_to_select개 뽑기
    selected_diners = available_diners.sample(
        n=min(num_to_select, len(available_diners))
    )
    st.session_state.previous_category_small.extend(
        selected_diners["diner_category_small"].tolist()
    )
    st.session_state.consecutive_failures = 0  # 성공 시 실패 횟수 초기화

    return selected_diners


# 메뉴 검색 함수 정의
def search_menu(row, search_term):
    search_fields = [
        "diner_menu_name",
        "diner_tag",
        "diner_category_middle",
        "diner_category_small",
        "diner_category_detail",
    ]
    for field in search_fields:
        if isinstance(row[field], list):  # 리스트인 경우
            # 리스트 내 요소 중 검색어가 포함된 경우
            if any(search_term in item for item in row[field]):
                return True
        elif isinstance(row[field], str):  # 문자열인 경우
            # 문자열에 검색어가 포함된 경우
            if search_term in row[field]:
                return True
    return False
