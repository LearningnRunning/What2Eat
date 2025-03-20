# src/utils/geolocation.py

import random
import string

import requests
import streamlit as st
from config.constants import (DEFAULT_ADDRESS_INFO_LIST, KAKAO_API_HEADERS,
                              KAKAO_API_URL)
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim


def generate_user_agent():
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    user_agent = f"What2Eat_{random_string}"
    return user_agent


def geocode(longitude, latitude):
    user_agent = generate_user_agent()

    geolocator = Nominatim(user_agent=user_agent)
    # deplot_latitude, deplot_longitude = 37.5074423, 127.0567474
    try:

        location = geolocator.reverse((latitude, longitude))

    except GeocoderUnavailable:
        st.warning(
            "Geocoding 서비스가 현재 사용 불가능합니다.\n 키워드 검색으로 현위치를 찾아주세요."
        )
        return DEFAULT_ADDRESS_INFO_LIST[0]
    except Exception as e:
        st.error(
            f"Geocoding 서비스가 현재 사용 불가능합니다.\n 키워드 검색으로 현위치를 찾아주세요."
        )
        return DEFAULT_ADDRESS_INFO_LIST[0]
    # print(location)
    address_components = location.raw["address"]

    # print(address_components.get('city'))

    if "city" in address_components:
        city_name = address_components.get("city")
    else:
        city_name = ""

    if "borough" in address_components:
        neighbourhood = address_components.get("borough")
    else:
        neighbourhood = ""

    if "suburb" in address_components:
        suburb = address_components.get("suburb")
    else:
        suburb = ""

    return f"{city_name} {neighbourhood} {suburb}에 있구나!"


def search_your_address():
    # session_state 초기화
    if "last_search" not in st.session_state:
        st.session_state.last_search = ""

    search_region_text = st.text_input("주소나 키워드로 입력해줘")
    search_clicked = st.button("검색")
    
    # 검색 버튼을 클릭했거나 새로운 검색어로 엔터를 눌렀을 때
    if search_clicked or (
        search_region_text and search_region_text != st.session_state.last_search
    ):
        st.session_state.last_search = search_region_text

        params = {"query": search_region_text, "size": 1}

        response = requests.get(KAKAO_API_URL, headers=KAKAO_API_HEADERS, params=params)

        if response.status_code == 200:
            response_json = response.json()
            response_doc_list = response_json["documents"]
            if response_doc_list:
                response_doc = response_doc_list[0]
                address_info_list = [
                    response_doc["address_name"],
                    (float(response_doc["x"]), float(response_doc["y"])),
                ]
                st.session_state.address = address_info_list[0]
                st.session_state.user_lat, st.session_state.user_lon = (
                    address_info_list[1][1],
                    address_info_list[1][0],
                )
                st.rerun()
            else:
                st.write("다른 검색어를 입력해봐... 먄")

        else:
            st.write("다른 검색어를 입력해봐... 먄")
