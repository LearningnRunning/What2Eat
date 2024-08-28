from geopy.geocoders import Nominatim
import random
import string
import requests
import streamlit as st
from config.constants import KAKAO_API_URL, KAKAO_API_HEADERS


def generate_user_agent():
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    user_agent = f"What2Eat_{random_string}"
    return user_agent

def geocode(longitude, latitude):
    user_agent = generate_user_agent()
    
    geolocator = Nominatim(user_agent=user_agent)
    # deplot_latitude, deplot_longitude = 37.5074423, 127.0567474
    location = geolocator.reverse((latitude, longitude))
    print(location)
    address_components = location.raw['address']
    

    if address_components.get('city') not in ['서울특별시', '과천시', '성남시']:
        return '미안해.. 아직 서울만 돼....'
    
    else:
        if 'city' in address_components:
            city_name = address_components.get('city')
        else:
            city_name = ''
            
        if 'borough' in address_components:
            neighbourhood = address_components.get('borough')
        else:
            neighbourhood = ''

        if 'suburb' in address_components:
            suburb = address_components.get('suburb')
        else:
            suburb = ''

        return f"{city_name} {neighbourhood} {suburb}에 있구나!"
def search_your_address():
    search_region_text = st.text_input("주소나 키워드로 입력해줘")
    if st.button("검색"):
        params = {
            "query": search_region_text,
            # 'analyze_type': 'similar',
            'size': 1
        }

        response = requests.get(KAKAO_API_URL, headers=KAKAO_API_HEADERS, params=params)

        if response.status_code == 200:
            response_json = response.json()
            response_doc_list = response_json['documents']
            if response_doc_list:
                response_doc = response_doc_list[0]
                address_info_list = [response_doc['address_name'], (float(response_doc['x']), float(response_doc['y']))]
                st.session_state.address = address_info_list[0]
                st.session_state.user_lat, st.session_state.user_lon = address_info_list[1][1], address_info_list[1][0]
                st.experimental_rerun()
            else:
                st.write('다른 검색어를 입력해봐... 먄')
                
        else:
            st.write('다른 검색어를 입력해봐... 먄')