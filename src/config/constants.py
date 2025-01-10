import streamlit as st
import json

LOGO_IMG_PATH = "./static/img/what2eat-logo-middle.png"
LOGO_SMALL_IMG_PATH = "./static/img/what2eat-logo-small.png"
LOGO_TITLE_IMG_PATH = "./static/img/what2eat-word-logo-small.png"
GUIDE_IMG_PATH = "./static/img/kakomap_nickname_guide.jpg"

DEFAULT_ADDRESS_INFO_LIST = ["강남구 삼성동", 127.0567474, 37.5074423]

DINER_REVIEW_AVG = 3.2

DATA_PATH = "./data/seoul_data/*.csv"
ZONE_INFO_PATH = "./data/zone_info.json"
MODEL_PATH = "./data/model_data"

# Kakao API settings
KAKAO_API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_API_HEADERS = {"Authorization": f"KakaoAK {st.secrets['REST_API_KEY']}"}

# 우선순위를 정의
PRIORITY_ORDER = {"한식": 1, "중식": 2, "일식": 2, "양식": 2}

# JSON 파일 읽기
with open(ZONE_INFO_PATH, "r", encoding="utf-8") as f:
    loaded_dict = json.load(f)
print(loaded_dict.keys())
ZONE_INDEX = loaded_dict["ZONE_INDEX"]

CITY_INDEX = loaded_dict["CITY_INDEX"]

# 지역 좌표 매핑
ZONE_COORDINATES = {
    "서울 강북권": (37.6173, 127.0236),
    "서울 강남권": (37.4963, 127.0298),
    "서울 서부권": (37.5502, 126.9003),
    "경기 동부권": (37.5309, 127.2435),
    "경기 서부권": (37.3983, 126.7052),
    "경기 중부권": (37.4315, 127.1985),
    "강원 동부권": (37.7581, 128.8761),
    "강원 중부권": (37.8377, 128.2385),
    "경북 동부권": (36.0012, 129.4022),
    "인천권": (37.4563, 126.7052),
    "제주권": (33.4996, 126.5312),
    "광주권": (35.1595, 126.8526),
}

# 등급별 색상 매핑
GRADE_COLORS = {
    3: "#BD2333",  # 빨강
    2: "#84BD00",  # 초록
    1: "#1095F9",  # 파랑
}

GRADE_MAP = {"🌟": 1, "🌟🌟": 2, "🌟🌟🌟": 3}
    