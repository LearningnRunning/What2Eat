import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from streamlit_chat import message
from geopy.geocoders import Nominatim

import pandas as pd
from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
from math import radians, sin, cos, sqrt, atan2
import random
import string
import json
from PIL import Image

# logo_color_lst = [
#     ["FF7F00", "0000FF", "FFC0CB", "FF7F00", "0000FF", "FFC0CB", "FF0000", "000000"],
#     ["FFFF00", "FFFFFF", "808080", "FFFFFF", "800080", "800080", "000000", "FF7F00"],
#     ["8B4513", "F5F5DC", "FFC0CB", "000000", "0000FF", "008080", "808080", "FFFF00"]
# ]

logo_img_path = './img_data/what2eat-logo-middle.png'
logo_small_img_path = './img_data/what2eat-logo-small.png'
# 페이지 설정
st.set_page_config(
    page_title="머먹?",
    page_icon=logo_small_img_path,
    layout="wide",
)

@st.cache_data()
def cached_model():
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    return model

@st.cache_data()
def get_dataset():
    df = pd.read_csv('wellness_dataset.csv')
    df['embedding'] = df['embedding'].apply(json.loads)
    return df

@st.cache_data
def category_filters(diner_category, df_diner):
    category_filted_df = df_diner.query(f"diner_category_middle in @diner_category")
    
    diner_nearby_cnt = len(category_filted_df)
    
    return category_filted_df

@st.cache_data
def real_review_filters(df_diner):
    
    diner_review_avg = 3.2
    # Convert diner_review_avg to string for formatting
    diner_review_avg_str = str(diner_review_avg)
    # result_df = df_diner.query(f"(diner_category_middle == '{diner_category}')  and (diner_address_constituency == '{address_gu}') and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg <= {diner_review_avg})")
    # (diner_address_constituency in @address_gu)
    
    result_df = df_diner.query(f"(diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg >= diner_review_avg)")
    result_df_inner_join = pd.merge(df_review, result_df, on='diner_idx', how='inner')
    
    personalAverageScoreRow = 3.8
    thisRestaurantScore = 4.0
    
    result_df_inner_join = result_df_inner_join.query(f"(reviewer_avg <= {personalAverageScoreRow}) and (reviewer_review_score >= {thisRestaurantScore})")

    
    personalAverageScoreRow = 4.0
    thisRestaurantScore = 1.5
    
    result_df_inner_join_bad = result_df_inner_join.query(f"(reviewer_avg >= {personalAverageScoreRow}) and (reviewer_review_score <= {thisRestaurantScore})")
    
    return result_df_inner_join, result_df_inner_join_bad

@st.cache_data
def load_excel_data():
    # Load the Excel data and create the DataFrame
    # df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv', index_col=0)
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv', index_col=0)
    df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv')
    df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv')
    df_diner['diner_category_detail'].fillna('', inplace=True)
    return df_diner, df_review

def my_chat_message(message_txt):
    return message(message_txt, avatar_style="adventurer-neutral", seed=100)


def your_chat_message(message_txt):
    return message(message_txt, avatar_style="adventurer-neutral", seed=100)


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert latitude and longitude from decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c  # Radius of earth in kilometers

    return distance

def generate_user_agent():
    # Generate a random string of letters and digits
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    # Concatenate with a prefix to ensure it's a valid user_agent format
    user_agent = f"What2Eat_{random_string}"
    return user_agent

# 주소를 넣으면 위도, 경도 생성
def geocode(longitude, latitude):
    # longitude, latitude = 126.962101108891, 37.5512831039192
    # address_gu = "마포구"
    user_agent = generate_user_agent()
    
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.reverse((latitude, longitude))
    
    address_components = location.raw['address']
    print(address_components)
    
    
    if 'man_made' in address_components:
        return '너 어딨어!!! \n 위에 버튼을 눌러봐'
    elif address_components['city'] not in ['서울특별시', '과천시', '성남시']:
        return '미안해.. 아직 서울만 돼....'
    
    else:
        if 'city' in address_components:
            city_name = address_components['city']
        else:
            city_name = ''
            
        # Extract specific parts of the address
        if 'borough' in address_components:
            neighbourhood = address_components['borough']
        else:
            neighbourhood = ''

        if 'suburb' in address_components:
            suburb = address_components['suburb']
        else:
            suburb = ''

        # Print the desired address parts
        return f"{city_name} {neighbourhood} {suburb}에 있구나!"
        
# model = cached_model()
# df = get_dataset()
diner_review_avg = 3.2
df_diner, df_review = load_excel_data()
# print(df_diner.info())


# columns_name = [
#     'diner_name', 'diner_category_large', 'diner_category_middle', 'diner_category_small', 'diner_category_detail', 
#     'diner_menu', 'diner_review_cnt', 'diner_review_avg', 'diner_review_tags', 'diner_address', 'diner_phone', 'diner_lat', 'diner_lon', 
#     'diner_url', 'diner_open_time', 'diner_address_constituency', 'all_review_cnt', 'real_review_cnt', 'real_review_percent']
# df_diner.columns = columns_name
# # Assuming df_diner is your DataFrame
# df_diner.reset_index(inplace=True)  # Resetting index and making changes in-place
df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)  # Renaming the index column to diner_idx



BannerImage = Image.open(logo_img_path)
st.image(BannerImage)



# st.sidebar.header("오늘 뭐 먹?")
# name = st.sidebar.radio("Menu", ["What2Eat Chats", "What2Eat Maps"])

my_chat_message("안녕! 오늘 머먹?")
# # st.markdown("[❤️빵형의 개발도상국](https://www.youtube.com/c/빵형의개발도상국)")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

# with st.form('form', clear_on_submit=True):
#     user_input = st.chat_input(placeholder="Your message")
#     submitted = st.form_submit_button('전송')

# user_input = st.chat_input(placeholder="머먹?")

# # 인원수 입력
# # TODO:인원 값 피처엔지니어링 하기
# num_people = st.number_input("몇 명이서 식사하시나요?", min_value=1, value=1)

# # 지역 입력c
# # TODO:위치기반으로 바꾸기
# area = st.text_input("어느 지역에서 찾으시나요?", placeholder="예: 강남, 홍대")


location = streamlit_geolocation()
user_lat, user_lon = location['latitude'], location['longitude']
# user_lat, user_lon =  37.429246, 126.9874451
user_address = geocode(user_lon, user_lat)
my_chat_message(user_address)

if user_lat is not None or user_lon is not None:
    my_chat_message("어디까지 갈겨?")

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
        my_chat_message("뭐 먹을겨?")
        # my_chat_message("")
        # Filter out categories and convert float values to strings
        df_geo_filtered = df_geo_filtered[df_geo_filtered['real_good_review_cnt'].notna()]

        df_geo_filtered = df_geo_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")
        
        diner_category_lst = sorted([str(category) for category in set(df_geo_filtered['diner_category_middle'].dropna().to_list()) if str(category) != '음식점'])

        diner_category = st.multiselect("", diner_category_lst)

   
        if bool(diner_category):
            df_geo_mid_catecory_filtered = category_filters(diner_category, df_geo_filtered)
            
            if len(df_geo_mid_catecory_filtered) > people_counts:
            
                my_chat_message("세부 업종에서 안 당기는 건 빼!")
                # Assuming your data is stored in a DataFrame called 'df'
                unique_categories = df_geo_mid_catecory_filtered['diner_category_small'].unique().tolist()   
                
                # Create a multi-select radio button
                seleted_category = st.multiselect("세부 카테고리", unique_categories, default=unique_categories)
                df_geo_small_catecory_filtered = df_geo_mid_catecory_filtered[df_geo_mid_catecory_filtered['diner_category_small'].isin(seleted_category)]

                diner_nearby_cnt = len(df_geo_small_catecory_filtered)

                
                # Filter rows where real_review_cnt is not NaN
                # df_geo_small_catecory_filtered = df_geo_small_catecory_filtered[df_geo_small_catecory_filtered['real_review_cnt'].notna()]

                # desired_df = df_geo_small_catecory_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_review_cnt >= 5)")
                # Assuming your data is stored in a DataFrame called 'df'
                # desired_df['combined_categories'] = desired_df['diner_category_small'] + ' / ' + str(desired_df['diner_category_detail'])
                
                if not len(df_geo_small_catecory_filtered):
                    my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐")
                elif seleted_category:
                    # st.dataframe(df_geo_small_catecory_filtered)
                    introduction = f"{radius_distance} 근처 {diner_nearby_cnt}개의 맛집 중에 {len(df_geo_small_catecory_filtered)}개의 인증된 곳이 있음\n\n"
                    for index, row in df_geo_small_catecory_filtered.iterrows():
                        diner_name = row['diner_name']
                        diner_category_small = row['diner_category_small']
                        diner_url = row['diner_url']
                        real_review_cnt = int(row['real_good_review_cnt'])
                        distance = int(row['distance']*1000)
                        diner_good_percent = row['real_good_review_percent']
                        diner_bad_percent = row['real_bad_review_percent']
                        
                        # Create Markdown-formatted introduction
                        introduction += f"[{diner_name}]({diner_url})"
                        if diner_bad_percent is not None and diner_bad_percent > 10:
                            introduction += f"\n불호(비추)리뷰 비율이 {diner_bad_percent}%나 돼!"
                            if radius_kilometers >= 1:
                                introduction += f"\n{distance}M \n\n"
                            else:
                                introduction += "\n\n"
                        else:
                            if diner_name:
                                introduction += f" ({diner_category_small})\n"
                            else:
                                introduction += "\n"
                                
                            introduction += f"쩝쩝박사 {real_review_cnt}명 인증 \n 쩝쩝 퍼센트: {diner_good_percent}%"
                            
                            if radius_kilometers >= 1:
                                introduction += f"\n{distance}M \n\n"
                            else:
                                introduction += "\n\n"
                        # {int(distance*1000)}M 거리에 있습니다.
                        # introduction += f"[카카오맵 바로가기]({diner_url})\n"
                    # result_msg = "[캐럿](https://carat.im/)"
                    my_chat_message(introduction)

                chat_result = f""
            else:
                my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐")
    else:
        my_chat_message("헉.. 거리를 더 넓혀봐, 주변엔 없대")
                
#                 마크다운 형식을오 
# 한 row에서 
# f"{real_review_cnt}개의 쩝쩝박사가 선택한  \n [diner_name](diner_url)
# if user_input:
#     embedding = model.encode(user_input)

#     df['distance'] = df['embedding'].map(lambda x: cosine_similarity([embedding], [x]).squeeze())
#     answer = df.loc[df['distance'].idxmax()]

#     # max_distance = df['distance'].max()
#     # print("Maximum distance:", max_distance)
    
#     # if max_distance >= 0.6:
#     #     answer = df.loc[df['distance'].idxmax()]
#     # else:
#     st.session_state.past.append(user_input)
#     st.session_state.generated.append(answer['챗봇'])

# for i in range(len(st.session_state['past'])):
#     message(st.session_state['past'][i], is_user=True, key=str(i) + '_user', avatar_style="big-ears-neutral")
#     if len(st.session_state['generated']) > i:
#         message(st.session_state['generated'][i], key=str(i) + '_bot', avatar_style="croodles-neutral")