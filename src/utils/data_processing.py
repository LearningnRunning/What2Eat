import math
import folium
from folium.plugins import MarkerCluster
from math import radians, sin, cos, sqrt, atan2
import streamlit as st
import pandas as pd
import random


def grade_to_stars(diner_grade):
    if diner_grade == 0:
        return ""
    return f"🏅 쩝슐랭 {'🌟' * diner_grade} \n"  # 이모티콘 개수 반복


def generate_introduction(
    diner_idx,
    diner_name,
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
        if diner_tags:
            introduction += f"🔑 키워드: {'/'.join(diner_tags)}\n"
        if diner_menus:
            introduction += f"🍴 메뉴: {'/'.join(diner_menus[:3])}\n"
    else:
        introduction += f"{grade_to_stars(diner_grade)}"
        if diner_tags:
            introduction += f"🔑 키워드: {'/'.join(diner_tags[:5])}\n"
        if diner_menus:
            introduction += f"🍴 메뉴: {'/'.join(diner_menus[:3])}\n"

    # 거리 정보 추가
    if radius_kilometers >= 0.5:
        introduction += f"📍 여기서 {distance}M 정도 떨어져 있어!\n\n"
    else:
        introduction += "\n\n"

    return introduction


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c

    return distance


def filter_recommendations_by_distance_memory(recommended_items_df, user_lat, user_lon, radius):
    # 거리 계산
    distances = recommended_items_df.apply(
        lambda row: haversine(user_lat, user_lon, row["diner_lat"], row["diner_lon"]), axis=1
    )
    recommended_items_df["distance"] = distances
    # 반경 내의 아이템 필터링
    filtered_df = recommended_items_df[recommended_items_df["distance"] <= radius]
    return filtered_df


def predict_rating(user_id, item_id, algo):
    prediction = algo.predict(user_id, item_id)
    return prediction.est


def recommend_items(user_id, user_item_matrix, user_similarity_df, num_recommendations=10):
    # 해당 사용자의 유사도 가져오기
    similar_users = user_similarity_df[user_id].drop(user_id).sort_values(ascending=False)

    # 유사한 사용자가 선호하는 아이템 추출
    similar_users_indices = similar_users.index
    similar_users_ratings = user_item_matrix.loc[similar_users_indices]

    # 평균 평점 계산
    recommendation_scores = similar_users_ratings.mean(axis=0)

    # 이미 평가한 아이템 제거
    user_rated_items = user_item_matrix.loc[user_id].dropna().index
    recommendation_scores = recommendation_scores.drop(user_rated_items, errors="ignore")

    # 상위 추천 아이템 반환
    top_items = recommendation_scores.sort_values(ascending=False).head(num_recommendations)
    top_items_df = pd.DataFrame({"diner_idx": top_items.index, "score": top_items.values})

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
def category_filters(diner_category, df_diner_real_review, df_diner):
    category_filted_df = df_diner_real_review.query(f"diner_category_middle in @diner_category")
    # diner_nearby_cnt = len(df_diner.query(f"diner_category_middle in @diner_category"))

    return category_filted_df  # , diner_nearby_cnt


def make_map(desired_df, x, y):
    # 지도시각화
    m = folium.Map(location=[y, x], zoom_start=15)
    # Get the center coordinates
    # now_center = m.get_center()

    folium.CircleMarker(location=[y, x], radius=7, color="blue", fill_color="#147DF5").add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    for diner_row_idx, diner_row in desired_df.iterrows():
        diner_name = diner_row["diner_name"]
        diner_bad_percent = diner_row["real_bad_review_percent"]
        diner_review_tags = diner_row["diner_review_tags"]
        diner_menu = diner_row["diner_menu"]

        ## 정리
        if type(diner_review_tags) is not float:
            diner_tags = diner_review_tags.replace("@", " ")

        color = "darkblue"
        unlike = ""

        if diner_bad_percent > 10:
            color = "gray"
            unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 퍼센트 : {}".format(
                round(diner_bad_percent, 2)
            )

        # if diner_menu is not None:
        #     menu_tmp = diner_menu
        #     if menu_tmp.find('['):
        #         menu_list = [" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('[','').replace('[','').split(', ') if len(i)]
        #         menu = "\n".join(menu_list)
        #     elif menu_tmp.find('->'):
        #         menu_list =[" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('가격:', '').split('->')]
        #         menu = "\n".join(menu_list)
        #     elif len(menu_tmp):
        #         menu = "".join(menu_tmp.replace('[','').replace('[','').split(', '))
        #     else:
        #         menu = "메뉴정보가 없는 음식점입니다."

        # if len(menu) >= 120:
        #     menu = menu[:120]
        html = popup_html(diner_row, diner_tags, unlike)
        # iframe = branca.element.IFrame(html=html,width=510,height=280)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)

        # 마커 생성
        folium.Marker(
            [diner_row["diner_lat"], diner_row["diner_lon"]],
            popup=popup,
            tooltip=diner_name,
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
        ).add_to(marker_cluster)

    return m


# 랜덤 뽑기 함수
@st.cache_data
def pick_random_diners(df, num_to_select=5):
    high_grade_diners = df[df["diner_grade"] >= 2]

    # 조건: 이미 선택된 카테고리는 제외
    available_diners = high_grade_diners[
        ~high_grade_diners["diner_category_small"].isin(st.session_state.previous_category_small)
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
    selected_diners = available_diners.sample(n=min(num_to_select, len(available_diners)))
    st.session_state.previous_category_small.extend(
        selected_diners["diner_category_small"].tolist()
    )
    st.session_state.consecutive_failures = 0  # 성공 시 실패 횟수 초기화

    return selected_diners


# def popup_html(diner_row, linke_tags, unlike):
#     diner_name = diner_row["diner_name"]
#     diner_category_small = diner_row["diner_category_small"]
#     diner_url = f"https://place.map.kakao.com/{diner_row['diner_idx']}"
#     diner_open_time = diner_row["diner_open_time"]
#     real_review_cnt = int(diner_row["real_good_review_cnt"])
#     distance = int(diner_row["distance"] * 1000)
#     diner_good_percent = diner_row["real_good_review_percent"]

#     if type(diner_url) == float:
#         link = "https://map.kakao.com/"
#     else:
#         link = diner_url

#     if type(diner_open_time) == float:
#         open_time = "준비중"
#     else:
#         open_time = diner_open_time

#     left_col_color = "#19a7bd"
#     right_col_color = "#f2f0d3"

#     html = (
#         """<!DOCTYPE html>
#                 <html>
#                 <head>
#                 <div>
#                     <a href="{0}" target="_blank" >""".format(
#             link
#         )
#         + """
#                         <img src="https://upload.wikimedia.org/wikipedia/commons/0/08/KakaoMap_logo.png" alt="Clickable image" width="20" style="float: left; margin-right: 10px;">
#                     </a>
#                     <p>
#                         <h4 width="200px" >{0}</h4>""".format(
#             diner_name
#         )
#         + """
#                     </p>
#                 </div>


#                 <h5 style="margin-bottom:10"; width="80px"> 찐만족도: {0}% \n 찐만족 리뷰 수: {1}개  {2}</h4>""".format(
#             diner_good_percent, real_review_cnt, unlike
#         )
#         + """

#                 </head>
#                     <table style="height: 126px; width: 150px;">
#                 <tbody>


#                 <tr>
#                 <td style="width: 30px;background-color: """
#         + left_col_color
#         + """;"><span style="color: #ffffff;">업종</span></td>
#                 <td style="width: 100px;background-color: """
#         + right_col_color
#         + """;">{}</td>""".format(diner_category_small)
#         + """
#                 </tr>
#                 <tr>
#                 <td style="width: 30px;background-color: """
#         + left_col_color
#         + """;"><span style="color: #ffffff;">요약</span></td>
#                 <td style="width: 100px;background-color: """
#         + right_col_color
#         + """;">{}</td>""".format(linke_tags)
#         + """
#                 </tr>
#                 <tr>
#                 <td style="width: 30px;background-color: """
#         + left_col_color
#         + """;"><span style="color: #ffffff;">영업시간</span></td>
#                 <td style="width: 100px;background-color: """
#         + right_col_color
#         + """;">{}</td>""".format(open_time)
#         + """
#                 </tr>
#                 <tr>
#                 <td style="width: 30px;background-color: """
#         + left_col_color
#         + """;"><span style="color: #ffffff;">거리</span></td>
#                 <td style="width: 100px;background-color: """
#         + right_col_color
#         + """;">{} M</td>""".format(distance)
#         + """
#                 </tr>

#                 </tbody>
#                 </table>
#                 </html>
#                 """
#     )
#     return html


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
