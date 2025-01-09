import streamlit as st
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from utils.data_loading import load_static_data
from utils.ui_components import choice_avatar, my_chat_message
from utils.geolocation import geocode, search_your_address
from utils.data_processing import (
    category_filters,
    haversine,
    generate_introduction,
    search_menu,
    pick_random_diner,
    grade_to_stars,
    # recommend_items,
    # recommend_items_model,
    # filter_recommendations_by_distance_memory,
)
from config.constants import (
    LOGO_IMG_PATH,
    LOGO_SMALL_IMG_PATH,
    LOGO_TITLE_IMG_PATH,
    GUIDE_IMG_PATH,
    DEFAULT_ADDRESS_INFO_LIST,
    PRIORITY_ORDER,
    ZONE_INDEX,
    CITY_INDEX,
)

# 페이지 설정 및 데이터 로딩
st.set_page_config(page_title="머먹?", page_icon=LOGO_SMALL_IMG_PATH, layout="wide")
df_diner, banner_image, icon_image, kakao_guide_image = load_static_data(
    LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH, GUIDE_IMG_PATH
)
st.logo(image=LOGO_TITLE_IMG_PATH, icon_image=LOGO_SMALL_IMG_PATH)
df_diner.rename(columns={"index": "diner_idx"}, inplace=True)
# algo_knn, trainset_knn, user_item_matrix, user_similarity_df = load_model()


# 세션 상태 초기화
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "user_lat" not in st.session_state or "user_lon" not in st.session_state:
    st.session_state.user_lat, st.session_state.user_lon = (
        DEFAULT_ADDRESS_INFO_LIST[2],
        DEFAULT_ADDRESS_INFO_LIST[1],
    )
if "address" not in st.session_state:
    st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]


# 위치 선택 함수
def select_location():
    option = st.radio(
        "위치를 선택하세요", ("주변에서 찾기", "키워드로 검색으로 찾기(강남역 or 강남대로 328)")
    )
    if option == "주변에서 찾기":
        location = streamlit_geolocation()
        if location["latitude"] is not None or location["longitude"] is not None:
            st.session_state.user_lat, st.session_state.user_lon = (
                location["latitude"],
                location["longitude"],
            )
            st.session_state.address = geocode(st.session_state.user_lon, st.session_state.user_lat)
        else:
            st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]
    elif option == "키워드로 검색으로 찾기(강남역 or 강남대로 328)":
        search_your_address()
    return st.session_state.user_lat, st.session_state.user_lon, st.session_state.address


# 거리 선택 함수
def select_radius(avatar_style, seed):
    my_chat_message("어디까지 갈겨?", avatar_style, seed)
    radius_distance = st.selectbox(
        "어디", ["300m", "500m", "1km", "3km", "10km"], label_visibility="hidden"
    )
    return {"300m": 0.3, "500m": 0.5, "1km": 1, "3km": 3, "10km": 10}[
        radius_distance
    ], radius_distance


# 결과 표시 함수
def display_results(df_filtered, radius_int, radius_str, avatar_style, seed):
    df_filtered = df_filtered.sort_values(by="bayesian_score", ascending=False)
    print("radius_int", radius_int)
    if not len(df_filtered):
        my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed)
    else:
        # 나쁜 리뷰와 좋은 리뷰를 분리
        bad_reviews = []
        good_reviews = []

        for _, row in df_filtered.iterrows():
            if row["real_bad_review_percent"] is not None and row["real_bad_review_percent"] > 20:
                bad_reviews.append(row)  # 나쁜 리뷰로 분리
            else:
                good_reviews.append(row)  # 좋은 리뷰로 분리

        # 소개 메시지 초기화
        introduction = f"{radius_str} 근처 \n {len(df_filtered)}개의 인증된 곳 발견!\n\n"

        # 좋은 리뷰 먼저 처리
        for row in good_reviews:
            introduction += generate_introduction(
                row["diner_idx"],
                row["diner_name"],
                radius_int,
                int(row["distance"] * 1000),
                row["diner_category_small"],
                row["diner_grade"],
                row["diner_tag"],
                row["diner_menu_name"],
                row.get("score"),
            )

        # 나쁜 리뷰 마지막에 처리
        for row in bad_reviews:
            introduction += f"\n🚨 주의: [{row['diner_name']}](https://place.map.kakao.com/{row['diner_idx']})의 비추 리뷰가 {round(row['real_bad_review_percent'], 2)}%입니다.\n"

        # 최종 메시지 전송
        my_chat_message(introduction, avatar_style, seed)


# 캐시된 데이터 필터링 함수
@st.cache_data
def get_filtered_data(df, user_lat, user_lon, max_radius=30):
    df["distance"] = df.apply(
        lambda row: haversine(user_lat, user_lon, row["diner_lat"], row["diner_lon"]), axis=1
    )

    # 거리 계산 및 필터링
    filtered_df = df[df["distance"] <= max_radius]

    return filtered_df


#  '중국요리', '떡볶이', '국밥', '곱창,막창','회', '피자',
def ranking_page():
    st.title("지역별 카테고리 랭킹")

    # 지역 선택
    zone = st.selectbox("지역을 선택하세요", list(ZONE_INDEX.keys()))
    zone_value = ZONE_INDEX[zone]
    selected_zone_all = f"{zone} 전체"

    # 선택한 지역의 데이터 필터링
    filtered_zone_df = df_diner[df_diner["zone_idx"] == zone_value]

    # 상세 지역 선택
    city_options = filtered_zone_df["constituency_idx"].dropna().unique()
    city_labels = [CITY_INDEX.get(str(idx), "Unknown") for idx in city_options]
    city_label = st.selectbox("상세 지역을 선택하세요", [selected_zone_all] + city_labels)
    print("city_label", city_label)

    if city_label:
        if city_label == selected_zone_all:
            filtered_city_df = filtered_zone_df
        else:
            city_value = next((k for k, v in CITY_INDEX.items() if v == city_label), None)

            if city_value is not None:
                filtered_city_df = filtered_zone_df[
                    filtered_zone_df["constituency_idx"] == int(city_value)
                ]

        # 중간 카테고리 선택 및 필터링
        available_categories = filtered_city_df["diner_category_middle"].dropna().unique()
        selected_category = st.selectbox(
            "중간 카테고리를 선택하세요", ["전체"] + list(available_categories)
        )

        if selected_category != "전체":
            filtered_city_df = filtered_city_df[
                filtered_city_df["diner_category_middle"] == selected_category
            ]

        # 세부 카테고리 선택 및 필터링
        available_small_categories = filtered_city_df["diner_category_small"].dropna().unique()
        selected_small_category = st.selectbox(
            "세부 카테고리를 선택하세요", ["전체"] + list(available_small_categories)
        )

        if selected_small_category != "전체":
            filtered_city_df = filtered_city_df[
                filtered_city_df["diner_category_small"] == selected_small_category
            ]

        # 세부 카테고리별 랭킹 표시
        st.subheader(
            f"{selected_category if selected_category != '전체' else '전체 중간 카테고리'} 카테고리 ({selected_small_category if selected_small_category != '전체' else '전체'}) 랭킹"
        )
        ranked_df = filtered_city_df.sort_values(by="bayesian_score", ascending=False)[
            ["diner_name", "diner_url", "diner_category_small", "diner_grade"]
        ]

        st.dataframe(
            ranked_df.rename(
                columns={
                    "diner_name": "음식점명",
                    "diner_category_small": "세부 카테고리",
                    "diner_url": "카카오맵링크",
                    "diner_grade": "쩝슐랭",
                }
            ),
            use_container_width=True,
        )


def chat_page():
    # 아바타 선택 및 초기 메시지
    avatar_style, seed = choice_avatar()
    my_chat_message("안녕! 오늘 머먹?", avatar_style, seed)
    # my_chat_message(
    #     "잠깐! AI 머먹을 시험 시행 중이야 한번 써볼래? \n [AI 머먹 이용하기](https://laas.wanted.co.kr/sandbox/share?project=PROMPTHON_PRJ_463&hash=f11097aa25dde2ef411ac331f47c1a3d1199331e8c4d10adebd7750576f442ff)",
    #     avatar_style,
    #     seed,
    # )

    # 메인 로직
    user_lat, user_lon, user_address = select_location()
    my_chat_message(user_address, avatar_style, seed)

    # 최대 반경 10km로 데이터 필터링 (캐시 사용)
    df_geo_filtered = get_filtered_data(df_diner, user_lat, user_lon)

    if len(df_geo_filtered):
        radius_kilometers, radius_distance = select_radius(avatar_style, seed)

        # 선택된 반경으로 다시 필터링
        df_geo_filtered_radius = df_geo_filtered[df_geo_filtered["distance"] <= radius_kilometers]
        df_geo_filtered_real_review = df_geo_filtered_radius[
            df_geo_filtered_radius["bayesian_score"].notna()
        ]
        # df_geo_filtered_real_review = df_geo_filtered_radius.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

        search_option = st.radio(
            "검색 방법을 선택하세요", ("카테고리로 찾기", "메뉴로 찾기", "랜덤 추천 받기")
        )  # , '추천 받기'
        # diner_nearby_cnt = len(df_geo_filtered)
        if search_option == "메뉴로 찾기":
            menu_search = st.text_input("찾고 싶은 메뉴를 입력하세요")
            if menu_search:

                df_menu_filtered = df_geo_filtered_real_review[
                    df_geo_filtered_real_review.apply(
                        lambda row: search_menu(row, menu_search), axis=1
                    )
                ]
                display_results(
                    df_menu_filtered, radius_kilometers, radius_distance, avatar_style, seed
                )
        elif search_option == "랜덤 추천 받기":
            if st.button("랜덤 뽑기"):
                result = pick_random_diner(df_geo_filtered_real_review)
                if result is None:
                    my_chat_message(
                        "야, 추천할 레스토랑이 더 이상 없어. 다른 옵션 골라보거나 한 번 더 눌러봐!",
                        avatar_style,
                        seed,
                    )

                    st.error("추천할 레스토랑이 없어!")
                else:
                    diner_name = result["diner_name"]
                    diner_category_small = result["diner_category_small"]
                    diner_url = result["diner_url"]
                    diner_grade = result["diner_grade"]
                    diner_tag = result["diner_tag"]
                    diner_menu = result["diner_menu_name"]
                    diner_distance = round(result["distance"] * 1000, 2)

                    introduction = (
                        f"✨ **입벌려! 추천 들어간다** ✨\n\n"
                        f"📍 [{diner_name}]({diner_url}) ({diner_category_small})\n"
                        f"🗺️ 여기서 대략 **{diner_distance}m** 떨어져 있어.\n\n"
                    )

                    introduction += f"{grade_to_stars(diner_grade)}\n\n"

                    if diner_tag:
                        introduction += f"🔑 **주요 키워드**: {'/'.join(diner_tag)}\n"
                    if diner_menu:
                        introduction += f"🍴 **주요 메뉴**: {'/'.join(diner_menu[:10])}\n"

                    introduction += "\n가서 맛있게 먹고 와! 😋"

                    my_chat_message(introduction, avatar_style, seed)

        # elif search_option == '추천 받기':
        #     kakao_id = st.text_input("카카오맵의 닉네임을 알려주시면 리뷰를 남긴 기반으로 추천을 해드려요.")
        #     st.image(kakao_guide_image, width=300)
        #     # # 사용자-아이템 매트릭스에 사용자가 있는지 확인
        #     # if kakao_id in user_item_matrix.index:
        #     #     # 추천 아이템 목록 생성 (기존 사용자)
        #     #     recommended_items_df = recommend_items(
        #     #         kakao_id, user_item_matrix, user_similarity_df, num_recommendations=50
        #     #     )
        #     # else:
        #         # print(f"사용자 {kakao_id}가 데이터에 존재하지 않습니다.")
        #     # 신규 사용자에 대한 추천 생성 (KNN 기반)
        #     recommended_items_df = recommend_items_model(
        #         kakao_id, algo_knn, trainset_knn, num_recommendations=200
        #     )
        #     df_geo_filtered = df_geo_filtered[(df_geo_filtered['real_good_review_cnt'] > 4) & (df_geo_filtered['distance'] <= radius_kilometers)]
        #     # 추천 결과에 위치 정보 병합
        #     recommended_items_df = pd.merge(recommended_items_df, df_geo_filtered, on='diner_idx', how='right')
        #     recommended_items_df = recommended_items_df[recommended_items_df['score'].notna()]

        #     # 상위 N개의 추천 출력
        #     num_final_recommendations = 20
        #     final_recommendations = recommended_items_df.head(num_final_recommendations)
        #     display_results(final_recommendations, diner_nearby_cnt, radius_distance)

        else:
            my_chat_message("뭐 먹을겨?", avatar_style, seed)
            diner_category_lst = [
                str(category)
                for category in set(
                    df_geo_filtered_real_review["diner_category_middle"].dropna().to_list()
                )
                if str(category) != "음식점"
            ]
            sorted_diner_category_lst = sorted(
                diner_category_lst, key=lambda x: PRIORITY_ORDER.get(x, 3)
            )

            if sorted_diner_category_lst:
                diner_category = st.multiselect(
                    label="첫번째 업태",
                    options=sorted_diner_category_lst,
                    label_visibility="hidden",
                )
                if bool(diner_category):
                    df_geo_mid_category_filtered = category_filters(
                        diner_category, df_geo_filtered_real_review, df_geo_filtered_radius
                    )
                    if len(df_geo_mid_category_filtered):
                        my_chat_message("세부 업종에서 안 당기는 건 빼!", avatar_style, seed)
                        unique_categories = (
                            df_geo_mid_category_filtered["diner_category_small"].unique().tolist()
                        )
                        selected_category = st.multiselect(
                            label="세부 카테고리",
                            options=unique_categories,
                            default=unique_categories,
                        )
                        if selected_category:
                            df_geo_small_category_filtered = df_geo_mid_category_filtered[
                                df_geo_mid_category_filtered["diner_category_small"].isin(
                                    selected_category
                                )
                            ].sort_values(by="bayesian_score", ascending=False)
                            display_results(
                                df_geo_small_category_filtered,
                                radius_kilometers,
                                radius_distance,
                                avatar_style,
                                seed,
                            )
            else:
                my_chat_message(
                    "헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed
                )
    else:
        my_chat_message("헉.. 주변에 맛집이 없대.. \n 다른 위치를 찾아봐", avatar_style, seed)


def main():
    st.sidebar.title("페이지 선택")
    page = st.sidebar.radio("이동할 페이지를 선택하세요", ["🧑‍🍳오늘 머먹?", "📈TOP 100"])

    if page == "🧑‍🍳오늘 머먹?":
        chat_page()
    elif page == "📈TOP 100":
        ranking_page()


if __name__ == "__main__":
    main()
