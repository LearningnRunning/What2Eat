import streamlit as st

LOGO_IMG_PATH = './static/img/what2eat-logo-middle.png'
LOGO_SMALL_IMG_PATH = './static/img/what2eat-logo-small.png'
LOGO_TITLE_IMG_PATH = './static/img/what2eat-word-logo-small.png'
GUIDE_IMG_PATH = './static/img/kakomap_nickname_guide.jpg'

DEFAULT_ADDRESS_INFO_LIST = ["강남구 삼성동", 127.0567474, 37.5074423]

DINER_REVIEW_AVG = 3.2

DATA_PATH = './data/seoul_data/*.csv'
MODEL_PATH = './data/model_data'

# Kakao API settings
KAKAO_API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_API_HEADERS = {
    "Authorization": f"KakaoAK {st.secrets['REST_API_KEY']}"
}

# 우선순위를 정의
PRIORITY_ORDER = {
    '한식': 1,
    '중식': 2,
    '일식': 2,
    '양식': 2
}