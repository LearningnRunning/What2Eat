# from collections import Counter

import folium
from folium import plugins
import random
import string
import pandas as pd
import requests
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium
import branca
import math
from geopy.geocoders import Nominatim
from collections import Counter
from PIL import Image
from time import time
from math import radians, sin, cos, sqrt, atan2

BannerImage = Image.open('./img_data/what2eat-logo.png')

st.sidebar.header("오늘 뭐 먹?")
name = st.sidebar.radio("Menu", ["What2Eat", "About us"])
# Add custom CSS to adjust element size


# Function to print map center coordinates
def print_map_center(event):
    print("Map center coordinates:", m.location)
    

def generate_user_agent():
    # Generate a random string of letters and digits
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    # Concatenate with a prefix to ensure it's a valid user_agent format
    user_agent = f"What2Eat_{random_string}"
    return user_agent

@st.cache_data
def category_filters(diner_category, df_diner_real_review, df_diner):
    category_filted_df = df_diner_real_review.query(f"diner_category_middle in @diner_category")
    diner_nearby_cnt = len(df_diner.query(f"diner_category_middle in @diner_category"))
    
    return category_filted_df, diner_nearby_cnt

# 주소를 넣으면 위도, 경도 생성
def geocode(longitude, latitude):
    # longitude, latitude = 126.962101108891, 37.5512831039192
    # address_gu = "마포구"
    user_agent = generate_user_agent()
    
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.reverse((latitude, longitude))
    
    address_components = location.raw['address']
    # print(address_components)
    if 'man_made' in address_components:
        return '아직 당신의 위치를 파악할 수 없어요!'
    
    elif address_components['city'] not in ['서울특별시', '과천시', '성남시']:
        return '...아직 서울만 돼요....'
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
        return f"{city_name} {neighbourhood} {suburb}에 있으시군요!"
    
    
    # if location:
    #     address_gu = location.address.split(", ")[1]
    #     print(address_gu)
    #     if address_gu[-1] != "구":
    #         address_gu = "마포구"
    #     latitude = location.latitude
    #     longitude = location.longitude
    # # Reverse geocode the coordinates
    # location = geolocator.reverse(center, exactly_one=True, language="ko")
    
    # # Extract the address from the location object
    # address = location.raw['address']

    # # Extract the Korean address components
    # korean_address = {
    #     'country': address.get('country', ''),
    #     'city': address.get('city', ''),
    #     'town': address.get('town', ''),
    #     'village': address.get('village', ''),
    #     'road': address.get('road', ''),
    #     'postcode': address.get('postcode', '')
    # }

    # # Extract the address from the location object
    # # address = location.address
    # print(korean_address)
        
        # return longitude, latitude, address_gu
    # else:
        # return longitude, latitude, address_gu

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

# 지도에 Pop시 정보창 생성
def popup_html(diner_row, linke_tags, menu, unlike):
    diner_name = diner_row['diner_name']
    diner_category_small = diner_row['diner_category_small']
    diner_url = diner_row['diner_url']
    diner_open_time = diner_row["diner_open_time"]
    real_review_cnt = int(diner_row['real_good_review_cnt'])
    distance = int(diner_row['distance']*1000)
    diner_good_percent = diner_row['real_good_review_percent']

    
    if type(diner_url) == float:
        link = 'https://map.kakao.com/'
    else:
        link = diner_url

    if type(diner_open_time) == float:
        open_time = '준비중'
    else:
        open_time = diner_open_time        
        
    left_col_color = "#19a7bd"
    right_col_color = "#f2f0d3"
    
    html = """<!DOCTYPE html>
<html>
<head>
<div>
    <a href="{0}" target="_blank" >""".format(link) + """
        <img src="https://upload.wikimedia.org/wikipedia/commons/0/08/KakaoMap_logo.png" alt="Clickable image" width="20" style="float: left; margin-right: 10px;">
    </a>
    <p>
        <h4 width="200px" >{0}</h4>""".format(diner_name) + """
    </p>
</div>


<h5 style="margin-bottom:10"; width="80px"> 찐만족도: {0}% \n 찐만족 리뷰 수: {1}개  {2}</h4>""".format(diner_good_percent, real_review_cnt, unlike) + """

</head>
    <table style="height: 126px; width: 150px;">
<tbody>


<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">업종</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(diner_category_small) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">요약</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(linke_tags) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">영업시간</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(open_time) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">거리</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{} M</td>""".format(distance) + """
</tr>

</tbody>
</table>
</html>
"""
    return html

# 카테고리 단일화를 위한 Dictionary
cat = {
    "베이커리,카페": [
        "폴바셋",
        "파리크라상",
        "파리바게뜨",
        "투썸플레이스",
        "커피전문점",
        "커피빈",
        "카페마마스",
        "카페",
        "제과,베이커리",
        "던킨",
        "도넛",
        "디저트카페",
        "북카페",
        "스타벅스",
    ],
    "패스트푸드": ["KFC", "햄버거", "피자", "치킨", "노브랜드버거", "맥도날드", "버거킹"],
    "육류": [
        "하남돼지집",
        "곱창,막창",
        "닭요리",
        "장어",
        "샤브샤브",
        "스테이크,립",
        "삼겹살",
        "양꼬치",
        "오발탄",
        "연타발",
        "육류,고기",
    ],
    "해산물": ["해물,생선", "해산물뷔페", "회", "조개", "게,대게", "굴,전복", "매운탕,해물탕", "아구", "복어"],
    "술집": ["호프,요리주점", "칵테일바", "술집", "실내포장마차"],
    "찌개,국밥": ["해장국", "추어", "찌개,전골", "감자탕", "곰탕", "국밥", "설렁탕", "이화수전통육개장"],
    "한식": ["한식", "한정식", "도시락", "돈까스,우동", "떡볶이", "불고기,두루치기", "분식", "순대", "소호정"],
    "일식": ["퓨전일식", "초밥,롤", "참치회", "장어", "일식집", "일본식주점", "일식"],
    "기타": ["퓨전요리", "족발,보쌈", "경복궁", "경성양꼬치", "뷔페", "온더보더", "인도음식", "족발,보쌈"],
    "양식": [
        "패밀리레스토랑",
        "터키음식",
        "태국음식",
        "동남아음식",
        "베트남음식",
        "아시아음식",
        "아웃백스테이크하우스",
        "양식",
        "이탈리안",
    ],
    "중식": ["중식", "중국요리"],
    "면류": ["국수", "냉면", "일본식라면"],
    "샌드위치,샐러드": ["샐러디", "써브웨이", "샌드위치"],
}



def make_map(desired_df, x, y):

    
    # desired_df = df_diner.iloc[:,1:]
    # st.dataframe(desired_df,unsafe_allow_html=True)
    # st.components.html(desired_df.to_html(escape=False), scrolling=True)
    # st.markdown(desired_df.sort_values('real_review_cnt', ascending=False).to_html(render_links=True),unsafe_allow_html=True)
    # desired_df_html = desired_df.sort_values('real_review_cnt', ascending=False).to_html(render_links=True)
    # html_code = f'<div style="overflow-x:auto; max-width:100%;">{desired_df_html}</div>'
    # st.markdown(html_code, unsafe_allow_html=True)
    

    # 지도시각화
    m = folium.Map(location=[y, x], zoom_start=15)
    # Get the center coordinates
    # now_center = m.get_center()

    folium.CircleMarker(location=[y, x],
        radius=7, color='blue', fill_color='#147DF5').add_to(m)
    
    marker_cluster = MarkerCluster().add_to(m)
    # plugins.LocateControl().add_to(m)
    
    # folium.Marker(
    #             [y, x],
    #             icon=folium.Icon(color='blue', icon="user-circle", prefix='fa')
    #             ).add_to(marker_cluster)
    
    for diner_row_idx, diner_row in desired_df.iterrows():

        diner_bad_percent = diner_row['real_bad_review_percent']
        diner_review_tags = diner_row["diner_review_tags"]
        diner_menu = diner_row["diner_menu"]


    
        ## 정리
        if type(diner_review_tags) is not float:
            # detail_set = detail.drop_duplicates(subset = 'diner_name', keep='last')
            diner_tags = diner_review_tags.replace('@', ' ')
            
        color = 'darkblue'
        unlike = ''
        
        if diner_bad_percent > 10:
            color = 'gray'
            unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 퍼센트 : {}".format(diner_bad_percent)



        if diner_menu is not None:
            menu_tmp = diner_menu
            if menu_tmp.find('['):
                menu_list = [" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('[','').replace('[','').split(', ') if len(i)]
                menu = "\n".join(menu_list)
            elif menu_tmp.find('->'):
                menu_list =[" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('가격:', '').split('->')]
                menu = "\n".join(menu_list)
            elif len(menu_tmp):
                menu = "".join(menu_tmp.replace('[','').replace('[','').split(', '))
            else:
                menu = "메뉴정보가 없는 음식점입니다."
                
        if len(menu) >= 120:
            menu = menu[:120] 
        html = popup_html(diner_row, diner_tags, menu, unlike)
        # iframe = branca.element.IFrame(html=html,width=510,height=280)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)
        
        # 마커 생성
        folium.Marker(
            [diner_row["diner_lat"], diner_row["diner_lon"]],
            popup=popup,
            tooltip=name,
            icon=folium.Icon(color=color, icon="cutlery", prefix='fa')
            ).add_to(marker_cluster)

    return m



    

# @st.cache_data
# def makingquery(diner_category, df_diner):
#     diner_review_avg = 3.5
#     # Convert diner_review_avg to string for formatting
#     diner_review_avg_str = str(diner_review_avg)
#     # result_df = df_diner.query(f"(diner_category_middle == '{diner_category}')  and (diner_address_constituency == '{address_gu}') and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg <= {diner_review_avg})")
#     # (diner_address_constituency in @address_gu)
#     result_df = df_diner.query(f"(diner_category_middle in @diner_category) and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg >= diner_review_avg)")
#     result_df_inner_join = pd.merge(df_review, result_df, on='diner_idx', how='inner')
    
#     personalAverageScoreRow = 3.8
#     thisRestaurantScore = 4.0
    
#     result_df_inner_join = result_df_inner_join.query(f"(reviewer_avg <= {personalAverageScoreRow}) and (reviewer_review_score >= {thisRestaurantScore})")

    
#     personalAverageScoreRow = 4.0
#     thisRestaurantScore = 1.5
    
#     result_df_inner_join_bad = result_df_inner_join.query(f"(reviewer_avg >= {personalAverageScoreRow}) and (reviewer_review_score <= {thisRestaurantScore})")

#     return result_df_inner_join, result_df_inner_join_bad


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
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv')
    df_diner['diner_category_detail'].fillna('', inplace=True)
    return df_diner

df_diner = load_excel_data()


df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)  # Renaming the index column to diner_idx

# 소개창
if name == "About us":
    st.image(BannerImage)
    st.write("# Hello, What2Eat World")

    
    all_review_total_sum = int(df_diner['all_review_cnt'].dropna().sum())
    real_review_total_sum = int(df_diner['real_good_review_cnt'].dropna().sum())
    
    df_diner_real_review = df_diner[df_diner['real_good_review_cnt'].notna()]
    st.write("보유 음식점 수: {0}개, \n 분석한 리뷰 수: {1}개".format(
            len(df_diner), all_review_total_sum
        ))
    st.write("인증된 음식점 수: {0}개, \n 깐깐한 리뷰 수: {1}개".format(
            len(df_diner_real_review), real_review_total_sum
        ))
    
    link_url = "## [What2Eat 로직설명](https://learningnrunning.github.io/example/tech/review/2024-03-03-from-kakaoRok-to-What2Eat/)"
    st.write(
        link_url
    )
    

# 기능창
elif name == "What2Eat":
    st.image(BannerImage, width=350, use_column_width=True)
    
    st.write("### 아래 버튼을 클릭해주세요, 주변 맛집을 찾아드릴게요")
    location = streamlit_geolocation()
    user_lat, user_lon = location['latitude'], location['longitude']
    user_address = geocode(user_lon, user_lat)
    st.write(user_address)
    # longitude, latitude = 126.991290, 37.573341
    
    people_counts = 20
        
    if user_lat is not None or user_lon is not None:
        # Select radius distance
        radius_distance = "10km" # st.selectbox("", ["300m", "500m", "1km", "3km", "10km"])

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

        # st.dataframe(df_filtered)
        
    # st.write("##  다른 곳에서 당길 거면!")
    # # Create a list of options
    # # Filter out NaN values and convert float values to strings
    # constituency_options = sorted([str(constituency) for constituency in set(df_diner['diner_address_constituency'].dropna().to_list())])

    # # Create a multi-select radio button
    # seleted_constituency = st.multiselect("", constituency_options)
        if len(df_geo_filtered):
                
            st.write("##  오늘 뭐가 당겨요?(복수가능)")
            
            df_geo_filtered = df_geo_filtered[df_geo_filtered['real_good_review_cnt'].notna()]

            df_geo_filtered_real_review = df_geo_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

            diner_category_lst = sorted([str(category) for category in set(df_geo_filtered_real_review['diner_category_middle'].dropna().to_list()) if str(category) != '음식점'])

            diner_category = st.multiselect("", diner_category_lst)

            if bool(diner_category):
                df_geo_mid_catecory_filtered, diner_nearby_cnt = category_filters(diner_category, df_geo_filtered_real_review, df_geo_filtered)
                
                if len(df_geo_mid_catecory_filtered):
                
                    st.write("세부 업종에서 안 당기는 건 빼주세요!")
                    # Assuming your data is stored in a DataFrame called 'df'
                    unique_categories = df_geo_mid_catecory_filtered['diner_category_small'].unique().tolist()   
                    
                    # Create a multi-select radio button
                    seleted_category = st.multiselect("세부 카테고리", unique_categories, default=unique_categories)
                    df_geo_small_catecory_filtered = df_geo_mid_catecory_filtered[df_geo_mid_catecory_filtered['diner_category_small'].isin(seleted_category)].sort_values(by='real_good_review_percent', ascending=False)


                    
                    # Filter rows where real_review_cnt is not NaN
                    # df_geo_small_catecory_filtered = df_geo_small_catecory_filtered[df_geo_small_catecory_filtered['real_review_cnt'].notna()]

                    # desired_df = df_geo_small_catecory_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_review_cnt >= 5)")
                    # Assuming your data is stored in a DataFrame called 'df'
                    # desired_df['combined_categories'] = desired_df['diner_category_small'] + ' / ' + str(desired_df['diner_category_detail'])
                    
                    if not len(df_geo_small_catecory_filtered):
                        st.write("헉.. 주변에 찐맛집이 없대요.. \n 다른 메뉴를 골라봐요")
                    elif seleted_category:
                        # st.dataframe(df_geo_small_catecory_filtered)
                        result_map = make_map(df_geo_small_catecory_filtered, user_lon, user_lat)
                        st_data = folium_static(result_map, width=700, height=500)
                        
                        # result_map.on_move(print_map_center)
                        # new_location = result_map.location
                        # new_lat, new_lon = new_location[0], new_location[1]
                        
                        # if [user_lat, user_lon] == new_location:
                        #     st_data = folium_static(result_map, width=700, height=500)
                        # else:
                        #     print(new_location)
                        #     st_folium(result_map, width=700, height=500)
