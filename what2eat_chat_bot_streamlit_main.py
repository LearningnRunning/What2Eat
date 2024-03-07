import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from awesome_package.module import (my_chat_message, choice_avatar, haversine,
                                    geocode, load_excel_data, category_filters,
                                    generate_introduction)

from PIL import Image


logo_img_path = './img_data/what2eat-logo-middle.png'
logo_small_img_path = './img_data/what2eat-logo-small.png'
diner_review_avg = 3.2

# 페이지 설정
st.set_page_config(
    page_title="머먹?",
    page_icon=logo_small_img_path,
    layout="wide",
)


df_diner = load_excel_data()
df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)  # Renaming the index column to diner_idx


BannerImage = Image.open(logo_img_path)
st.image(BannerImage)

avatar_style, seed = choice_avatar()

# st.sidebar.header("오늘 뭐 먹?")
# name = st.sidebar.radio("Menu", ["What2Eat Chats", "What2Eat Maps"])

my_chat_message("안녕! 오늘 머먹?", avatar_style, seed)
# # st.markdown("[❤️빵형의 개발도상국](https://www.youtube.com/c/빵형의개발도상국)")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

# # 인원수 입력
# # TODO:인원 값 피처엔지니어링 하기
# num_people = st.number_input("몇 명이서 식사하시나요?", min_value=1, value=1)


location = streamlit_geolocation()
user_lat, user_lon = location['latitude'], location['longitude']
# user_lat, user_lon =  37.4202, 126.9911
user_address = geocode(user_lon, user_lat)
my_chat_message(user_address, avatar_style, seed)

if user_lat is not None or user_lon is not None:
    my_chat_message("어디까지 갈겨?", avatar_style, seed)

    # Select radius distance
    radius_distance = st.selectbox("", ["300m", "500m", "1km", "3km", "10km"])

    # Convert radius distance to meters
    if radius_distance == "300m":
        radius_kilometers = 0.3
    elif radius_distance == "500m":
        radius_kilometers = 0.5
    elif radius_distance == "1km":
        radius_kilometers = 1
    elif radius_distance == "3km":
        radius_kilometers = 3
    elif radius_distance == "10km":
        radius_kilometers = 10

    # Calculate distance for each diner and filter rows within 1km radius
    df_diner['distance'] = df_diner.apply(lambda row: haversine(user_lat, user_lon, row['diner_lat'], row['diner_lon']), axis=1)
    df_geo_filtered = df_diner[df_diner['distance'] <= radius_kilometers]
    people_counts = 5

    if len(df_geo_filtered):
        my_chat_message("뭐 먹을겨?", avatar_style, seed)
        
        # Filter out categories and convert float values to strings
        df_geo_filtered = df_geo_filtered[df_geo_filtered['real_good_review_cnt'].notna()]

        df_geo_filtered_real_review = df_geo_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

        diner_category_lst = sorted([str(category) for category in set(df_geo_filtered_real_review['diner_category_middle'].dropna().to_list()) if str(category) != '음식점'])

        diner_category = st.multiselect("", diner_category_lst)


        if bool(diner_category):
            df_geo_mid_catecory_filtered, diner_nearby_cnt = category_filters(diner_category, df_geo_filtered_real_review, df_geo_filtered)
            
            if len(df_geo_mid_catecory_filtered):
            
                my_chat_message("세부 업종에서 안 당기는 건 빼!", avatar_style, seed)

                unique_categories = df_geo_mid_catecory_filtered['diner_category_small'].unique().tolist()   
                
                # Create a multi-select radio button
                seleted_category = st.multiselect("세부 카테고리", unique_categories, default=unique_categories)
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
                
