import streamlit as st
import pandas as pd
from streamlit_geolocation import streamlit_geolocation
from utils.data_loading import load_static_data
from utils.ui_components import choice_avatar, my_chat_message
from utils.geolocation import geocode, search_your_address
from utils.data_processing import category_filters, haversine, generate_introduction, search_menu, recommend_items, recommend_items_model, filter_recommendations_by_distance_memory
from config.constants import LOGO_IMG_PATH, LOGO_SMALL_IMG_PATH, LOGO_TITLE_IMG_PATH, GUIDE_IMG_PATH, DEFAULT_ADDRESS_INFO_LIST, PRIORITY_ORDER

# 페이지 설정 및 데이터 로딩
st.set_page_config(page_title="머먹?", page_icon=LOGO_SMALL_IMG_PATH, layout="wide")
df_diner, banner_image, icon_image, kakao_guide_image = load_static_data(LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH, GUIDE_IMG_PATH)
df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)
# algo_knn, trainset_knn, user_item_matrix, user_similarity_df = load_model()

# 아바타 선택 및 초기 메시지
avatar_style, seed = choice_avatar()
my_chat_message("안녕! 오늘 머먹?", avatar_style, seed)
my_chat_message("잠깐! AI 머먹을 시험 시행 중이야 한번 써볼래? \n [AI 머먹 이용하기](https://laas.wanted.co.kr/sandbox/share?project=PROMPTHON_PRJ_463&hash=f11097aa25dde2ef411ac331f47c1a3d1199331e8c4d10adebd7750576f442ff)", avatar_style, seed)

# 세션 상태 초기화
if 'generated' not in st.session_state: st.session_state['generated'] = []
if 'past' not in st.session_state: st.session_state['past'] = []
if "user_lat" not in st.session_state or "user_lon" not in st.session_state:
    st.session_state.user_lat, st.session_state.user_lon = DEFAULT_ADDRESS_INFO_LIST[2], DEFAULT_ADDRESS_INFO_LIST[1]
if "address" not in st.session_state:
    st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]

# 위치 선택 함수
def select_location():
    option = st.radio("위치를 선택하세요", ('주변에서 찾기', '키워드로 검색으로 찾기(강남역 or 강남대로 328)'))
    if option == '주변에서 찾기':
        location = streamlit_geolocation()
        if location['latitude'] is not None or location['longitude'] is not None:
            st.session_state.user_lat, st.session_state.user_lon = location['latitude'], location['longitude']
            st.session_state.address = geocode(st.session_state.user_lon, st.session_state.user_lat)
        else:
            st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]
    elif option == '키워드로 검색으로 찾기(강남역 or 강남대로 328)':
        search_your_address()
    return st.session_state.user_lat, st.session_state.user_lon, st.session_state.address

# 거리 선택 함수
def select_radius():
    my_chat_message("어디까지 갈겨?", avatar_style, seed)
    radius_distance = st.selectbox("어디", ["300m", "500m", "1km", "3km", "10km"], label_visibility='hidden')
    return {"300m": 0.3, "500m": 0.5, "1km": 1, "3km": 3, "10km": 10}[radius_distance], radius_distance

# 결과 표시 함수
def display_results(df_filtered, radius_distance):
    if not len(df_filtered):
        my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed)
    else:
        introduction = f"{radius_distance} 근처 \n {len(df_filtered)}개의 인증된 곳 발견!\n\n"
        for _, row in df_filtered.iterrows():
            introduction += generate_introduction(
                row['diner_idx'], row['diner_name'], row['real_bad_review_percent'],
                radius_kilometers, int(row['distance']*1000), row['diner_category_small'],
                int(row['real_good_review_cnt']), row['real_good_review_percent'],
                row.get('score')  # score와 recommend_score 추가
            )
        my_chat_message(introduction, avatar_style, seed)

# 캐시된 데이터 필터링 함수
@st.cache_data
def get_filtered_data(df, user_lat, user_lon, max_radius=10):
    df['distance'] = df.apply(lambda row: haversine(user_lat, user_lon, row['diner_lat'], row['diner_lon']), axis=1)
    return df[df['distance'] <= max_radius]

# 메인 로직
user_lat, user_lon, user_address = select_location()
my_chat_message(user_address, avatar_style, seed)

# 최대 반경 10km로 데이터 필터링 (캐시 사용)
df_geo_filtered = get_filtered_data(df_diner, user_lat, user_lon)

if len(df_geo_filtered):
    radius_kilometers, radius_distance = select_radius()
    
    # 선택된 반경으로 다시 필터링
    df_geo_filtered_radius = df_geo_filtered[df_geo_filtered['distance'] <= radius_kilometers]
    df_geo_filtered_real_review = df_geo_filtered_radius[df_geo_filtered_radius['real_good_review_cnt'].notna()]
    # df_geo_filtered_real_review = df_geo_filtered_radius.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

    search_option = st.radio("검색 방법을 선택하세요", ('카테고리로 찾기', '메뉴로 찾기')) #, '추천 받기'
    diner_nearby_cnt = len(df_geo_filtered)
    if search_option == '메뉴로 찾기':
        menu_search = st.text_input("찾고 싶은 메뉴를 입력하세요")
        if menu_search:
            df_menu_filtered = df_geo_filtered_real_review[df_geo_filtered_real_review.apply(lambda row: search_menu(row, menu_search), axis=1)]
            display_results(df_menu_filtered, radius_distance)
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
        diner_category_lst = [str(category) for category in set(df_geo_filtered_real_review['diner_category_middle'].dropna().to_list()) if str(category) != '음식점']
        sorted_diner_category_lst = sorted(diner_category_lst, key=lambda x: PRIORITY_ORDER.get(x, 3))
        
        if sorted_diner_category_lst:
            diner_category = st.multiselect(label="첫번째 업태", options=sorted_diner_category_lst, label_visibility='hidden')
            if bool(diner_category):
                df_geo_mid_category_filtered = category_filters(diner_category, df_geo_filtered_real_review, df_geo_filtered_radius)
                if len(df_geo_mid_category_filtered):
                    my_chat_message("세부 업종에서 안 당기는 건 빼!", avatar_style, seed)
                    unique_categories = df_geo_mid_category_filtered['diner_category_small'].unique().tolist()
                    selected_category = st.multiselect(label="세부 카테고리", options=unique_categories, default=unique_categories)
                    if selected_category:
                        df_geo_small_category_filtered = df_geo_mid_category_filtered[df_geo_mid_category_filtered['diner_category_small'].isin(selected_category)].sort_values(by='real_good_review_percent', ascending=False)
                        display_results(df_geo_small_category_filtered, radius_distance)
        else:
            my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed)
else:
    my_chat_message("헉.. 주변에 맛집이 없대.. \n 다른 위치를 찾아봐", avatar_style, seed)