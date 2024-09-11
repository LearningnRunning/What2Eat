import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from utils.data_loading import load_excel_data
from utils.ui_components import choice_avatar, my_chat_message
from utils.geolocation import geocode, search_your_address
from utils.data_processing import category_filters, haversine, generate_introduction
from config.constants import LOGO_IMG_PATH, LOGO_SMALL_IMG_PATH, LOGO_TITLE_IMG_PATH, DEFAULT_ADDRESS_INFO_LIST, PRIORITY_ORDER

# 페이지 설정
st.set_page_config(
    page_title="머먹?",
    page_icon=LOGO_SMALL_IMG_PATH,
    layout="wide",
)

# 데이터 로딩
df_diner, banner_image, icon_image = load_excel_data(LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH)
df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)

# 로고 표시
st.logo(banner_image, icon_image=icon_image)

# 아바타 선택
avatar_style, seed = choice_avatar()

# 초기 메시지
my_chat_message("안녕! 오늘 머먹?", avatar_style, seed)
my_chat_message(
    "잠깐! AI 머먹을 시험 시행 중이야 한번 써볼래? \n [AI 머먹 이용하기](https://laas.wanted.co.kr/sandbox/share?project=PROMPTHON_PRJ_463&hash=f11097aa25dde2ef411ac331f47c1a3d1199331e8c4d10adebd7750576f442ff)", 
    avatar_style, 
    seed
    )

# 세션 상태 초기화
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []

# 위치 초기화
if "user_lat" not in st.session_state or "user_lon" not in st.session_state:
    st.session_state.user_lat, st.session_state.user_lon = DEFAULT_ADDRESS_INFO_LIST[2], DEFAULT_ADDRESS_INFO_LIST[1]
if "address" not in st.session_state:
    st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]

# 위치 선택 옵션
option = st.radio("위치를 선택하세요", ('주변에서 찾기', '주소 검색으로 찾기'))

if option == '주변에서 찾기':
    location = streamlit_geolocation()
    if location['latitude'] is not None or location['longitude'] is not None:
        st.session_state.user_lat, st.session_state.user_lon = location['latitude'], location['longitude']
        st.session_state.address = geocode(st.session_state.user_lon, st.session_state.user_lat)
    else:
        st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]
elif option == '주소 검색으로 찾기':
    search_your_address()

user_lat, user_lon = st.session_state.user_lat, st.session_state.user_lon

# 사용자 위치 메시지
if (user_lat == DEFAULT_ADDRESS_INFO_LIST[2] and user_lon == DEFAULT_ADDRESS_INFO_LIST[1]) and option == '주변에서 찾기':
    user_address = "너의 위치를 정확히 파악하기 위해 위 버튼을 눌러 위치 공유를 해줘!"
elif (user_lat == DEFAULT_ADDRESS_INFO_LIST[2] and user_lon == DEFAULT_ADDRESS_INFO_LIST[1]) and option == '주소 검색으로 찾기':
    user_address = "너의 위치를 정확히 파악하기 위해 위 검색을 통해 너의 위치 공유를 해줘!"
else:
    user_address = f"{st.session_state.address} 주변이구나!"

my_chat_message(user_address, avatar_style, seed)

# 거리 선택
my_chat_message("어디까지 갈겨?", avatar_style, seed)
radius_distance = st.selectbox("어디", ["300m", "500m", "1km", "3km", "10km"], label_visibility='hidden')

# 거리를 미터로 변환
radius_kilometers = {"300m": 0.3, "500m": 0.5, "1km": 1, "3km": 3, "10km": 10}[radius_distance]

# 거리 계산 및 필터링
df_diner['distance'] = df_diner.apply(lambda row: haversine(user_lat, user_lon, row['diner_lat'], row['diner_lon']), axis=1)
df_geo_filtered = df_diner[df_diner['distance'] <= radius_kilometers]

if len(df_geo_filtered):
    my_chat_message("뭐 먹을겨?", avatar_style, seed)
    
    # Filter out categories and convert float values to strings
    df_geo_filtered = df_geo_filtered[df_geo_filtered['real_good_review_cnt'].notna()]

    df_geo_filtered_real_review = df_geo_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

    diner_category_lst = [str(category) for category in set(df_geo_filtered_real_review['diner_category_middle'].dropna().to_list()) if str(category) != '음식점']
    # 리스트 정렬: 먼저 priority_order에 따라 정렬하고, 그 외 항목들은 우선순위 3으로 설정
    sorted_diner_category_lst = sorted(diner_category_lst, key=lambda x: PRIORITY_ORDER.get(x, 3))

    # print('sorted_diner_category_lst', sorted_diner_category_lst)
    if sorted_diner_category_lst:
        diner_category = st.multiselect(
            label="첫번째 업태",
            options=sorted_diner_category_lst,
            label_visibility='hidden')


        if bool(diner_category):
            df_geo_mid_catecory_filtered, diner_nearby_cnt = category_filters(diner_category, df_geo_filtered_real_review, df_geo_filtered)
            
            if len(df_geo_mid_catecory_filtered):
            
                my_chat_message("세부 업종에서 안 당기는 건 빼!", avatar_style, seed)

                unique_categories = df_geo_mid_catecory_filtered['diner_category_small'].unique().tolist()   
                # Create a multi-select radio button
                seleted_category = st.multiselect(
                    label="세부 카테고리",
                    options=unique_categories
                    )

                if seleted_category:

                    df_geo_small_catecory_filtered = df_geo_mid_catecory_filtered[df_geo_mid_catecory_filtered['diner_category_small'].isin(seleted_category)].sort_values(by='real_good_review_percent', ascending=False)
                    
                    if not len(df_geo_small_catecory_filtered):
                        my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed)
                    
                    elif seleted_category:
                        introduction = f"{radius_distance} 근처 \n {diner_nearby_cnt}개의 맛집 중에 {len(df_geo_small_catecory_filtered)}개의 인증된 곳 발견!\n\n"
                        
                        for index, row in df_geo_small_catecory_filtered.iterrows():
                            diner_name = row['diner_name']
                            diner_category_small = row['diner_category_small']
                            diner_url = row['diner_url']
                            real_review_cnt = int(row['real_good_review_cnt'])
                            distance = int(row['distance']*1000)
                            diner_good_percent = row['real_good_review_percent']
                            diner_bad_percent = row['real_bad_review_percent']
                            introduction += generate_introduction(diner_name, diner_url, diner_bad_percent, radius_kilometers, distance, diner_category_small, real_review_cnt, diner_good_percent)

                        my_chat_message(introduction, avatar_style, seed)

    else:
        my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed)
else:
    my_chat_message("헉.. 거리를 더 넓혀봐, 주변엔 없대", avatar_style, seed)
            