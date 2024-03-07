import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from streamlit_chat import message
from geopy.geocoders import Nominatim

import folium
from folium.plugins import MarkerCluster

import pandas as pd
from sentence_transformers import SentenceTransformer
from math import radians, sin, cos, sqrt, atan2
import random
import string
import json
import ast
from PIL import Image


@st.cache_data
def load_excel_data():
    # Load the Excel data and create the DataFrame
    # df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv', index_col=0)
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv', index_col=0)
    df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv')
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv')
    df_diner['diner_category_detail'].fillna('', inplace=True)
    df_diner["diner_menu"] = df_diner["diner_menu"].apply(ast.literal_eval)
    return df_diner


@st.cache_data
def category_filters(diner_category, df_diner_real_review, df_diner):
    category_filted_df = df_diner_real_review.query(f"diner_category_middle in @diner_category")
    diner_nearby_cnt = len(df_diner.query(f"diner_category_middle in @diner_category"))
    
    return category_filted_df, diner_nearby_cnt

@st.cache_data
def choice_avatar():
    avatar_style_list =['avataaars','pixel-art-neutral','adventurer-neutral', 'big-ears-neutral']
    seed_list =[100, "Felix"] + list(range(1,140))

    avatar_style = random.choice(avatar_style_list)
    seed = random.choice(seed_list)
    return avatar_style, seed

def my_chat_message(message_txt, choiced_avatar_style, choiced_seed):
    return message(message_txt, avatar_style=choiced_avatar_style, seed=choiced_seed)

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c

    return distance


def generate_user_agent():
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    user_agent = f"What2Eat_{random_string}"
    return user_agent

def geocode(longitude, latitude):
    user_agent = generate_user_agent()
    
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.reverse((latitude, longitude))
    
    address_components = location.raw['address']
    
    if 'man_made' in address_components:
        return '너 어딨어!!! \n 위에 버튼을 눌러봐 \n 그리고 위치 허용 해야함 ㅠ'
    elif address_components['city'] not in ['서울특별시', '과천시', '성남시']:
        return '미안해.. 아직 서울만 돼....'
    
    else:
        if 'city' in address_components:
            city_name = address_components['city']
        else:
            city_name = ''
            
        if 'borough' in address_components:
            neighbourhood = address_components['borough']
        else:
            neighbourhood = ''

        if 'suburb' in address_components:
            suburb = address_components['suburb']
        else:
            suburb = ''

        return f"{city_name} {neighbourhood} {suburb}에 있구나!"
        
def generate_introduction(diner_name, diner_url, diner_bad_percent, radius_kilometers, distance, diner_category_small, real_review_cnt, diner_good_percent):
    introduction = f"[{diner_name}]({diner_url})"
    if diner_bad_percent is not None and diner_bad_percent > 10:
        introduction += f"\n불호(비추)리뷰 비율이 {diner_bad_percent}%나 돼!"
        if radius_kilometers >= 0.5:
            introduction += f"\n{distance}M \n\n"
        else:
            introduction += "\n\n"
    else:
        if diner_name:
            introduction += f" ({diner_category_small})\n"
        else:
            introduction += "\n"
                            
        introduction += f"쩝쩝박사 {real_review_cnt}명 인증 \n 쩝쩝 퍼센트: {diner_good_percent}%"
                            
        if radius_kilometers >= 0.5:
            introduction += f"\n{distance}M \n\n"
        else:
            introduction += "\n\n"
    
    return introduction

# -----------------------------maps----------------------------------

def generate_user_agent():
    # Generate a random string of letters and digits
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    # Concatenate with a prefix to ensure it's a valid user_agent format
    user_agent = f"What2Eat_{random_string}"
    return user_agent



# 지도에 Pop시 정보창 생성
def popup_html(diner_row, linke_tags, unlike):
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




def make_map(desired_df, x, y):

    # 지도시각화
    m = folium.Map(location=[y, x], zoom_start=15)
    # Get the center coordinates
    # now_center = m.get_center()

    folium.CircleMarker(location=[y, x],
        radius=7, color='blue', fill_color='#147DF5').add_to(m)
    
    marker_cluster = MarkerCluster().add_to(m)

    for diner_row_idx, diner_row in desired_df.iterrows():
        diner_name = diner_row['diner_name']
        diner_bad_percent = diner_row['real_bad_review_percent']
        diner_review_tags = diner_row["diner_review_tags"]
        diner_menu = diner_row["diner_menu"]


    
        ## 정리
        if type(diner_review_tags) is not float:
            diner_tags = diner_review_tags.replace('@', ' ')
            
        color = 'darkblue'
        unlike = ''
        
        if diner_bad_percent > 10:
            color = 'gray'
            unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 퍼센트 : {}".format(diner_bad_percent)

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
            icon=folium.Icon(color=color, icon="cutlery", prefix='fa')
            ).add_to(marker_cluster)

    return m


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
