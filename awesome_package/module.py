import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from streamlit_chat import message
from geopy.geocoders import Nominatim

import pandas as pd
from sentence_transformers import SentenceTransformer
from math import radians, sin, cos, sqrt, atan2
import random
import string
import json
from PIL import Image


@st.cache_data
def load_excel_data():
    # Load the Excel data and create the DataFrame
    # df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv', index_col=0)
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv', index_col=0)
    df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv')
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv')
    df_diner['diner_category_detail'].fillna('', inplace=True)
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
