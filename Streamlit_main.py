# from collections import Counter

import folium
import pandas as pd
import requests
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium
import branca
import math
from geopy.geocoders import Nominatim
from collections import Counter
from PIL import Image
from time import time

BannerImage = Image.open('./img_data/what2eat-logo.png')

st.sidebar.header("오늘 뭐 먹?")
name = st.sidebar.selectbox("menu", ["What2Eat", "About us"])

# 주소를 넣으면 위도, 경도 생성
# def geocode(center):
#     # longitude, latitude = 126.962101108891, 37.5512831039192
#     # address_gu = "마포구"
#     geolocator = Nominatim(user_agent="What2Eat")
#     location = geolocator.geocode(address)
#     if location:
#         address_gu = location.address.split(", ")[1]
#         print(address_gu)
#         if address_gu[-1] != "구":
#             address_gu = "마포구"
#         latitude = location.latitude
#         longitude = location.longitude
#     # Reverse geocode the coordinates
#     location = geolocator.reverse(center, exactly_one=True, language="ko")
    
#     # Extract the address from the location object
#     address = location.raw['address']

#     # Extract the Korean address components
#     korean_address = {
#         'country': address.get('country', ''),
#         'city': address.get('city', ''),
#         'town': address.get('town', ''),
#         'village': address.get('village', ''),
#         'road': address.get('road', ''),
#         'postcode': address.get('postcode', '')
#     }

#     # Extract the address from the location object
#     # address = location.address
#     print(korean_address)
        
#         # return longitude, latitude, address_gu
#     # else:
#         # return longitude, latitude, address_gu

# 지도에 Pop시 정보창 생성
def popup_html(df,count, likepoint,menu, unlike):
    name=df['diner_name']
    category1=df['diner_category_large']
    address = df['diner_address'] 
    review_num=df['diner_review_cnt']
    if isinstance(review_num, (int,str)):
        review_num = int(review_num)
                    
    blog_review_num = df['diner_review_cnt']
    score_min = df['diner_review_avg']

    
    if type(df["diner_url"]) == float:
        link = 'https://map.kakao.com/'
    else:
        link = df['diner_url']

    if type(df["diner_open_time"]) == float:
        open_time = '준비중'
    else:
        open_time = df["diner_open_time"]        
        
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
        <h4 width="200px" >{0}</h4>""".format(name) + """
    </p>
</div>


<h5 style="margin-bottom:10"; width="200px">{0}명의 리뷰어가 4점 이상으로 평가하였습니다.{1}</h4>""".format(count, unlike) + """

</head>
    <table style="height: 126px; width: 500px;">
<tbody>


<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">업종</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(category1) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">평균 평점</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(score_min) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">평점수/ 블로그 리뷰수</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{0} 개/ {1}개</td>""".format(review_num, blog_review_num) + """
</tr>

<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">메뉴</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(menu) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">요약</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(likepoint) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">영업시간</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(open_time) + """
</tr>
<tr>
<td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">주소</span></td>
<td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(address) + """
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

def create_link(url:str) -> str:
    return f"<a href='{url}'>🔗</a>"


def main(result_df_inner_join, x, y, people_counts):
            result_df_inner_join.dropna(subset=['diner_idx'], inplace=True)
            # result_df_inner_join = result_df_inner_join.reset_index(drop=False)
            
            result_lst = result_df_inner_join['diner_idx'].to_list()
            result_lst = Counter(result_lst)
            desired_df = result_df_inner_join.loc[result_df_inner_join['diner_idx'].isin(list(result_lst.keys())), ['diner_idx', 'diner_address_constituency', 'diner_name', 'diner_url', 'diner_category_small', 'diner_open_time']] #,'diner_lon', 'diner_lat'
            result_dict = dict(result_lst)
            desired_df = desired_df.drop_duplicates()
            desired_df['real_review_cnt'] = desired_df['diner_idx'].apply(lambda idx: result_dict[idx])

            desired_df['diner_url_img'] = [create_link(url) for url in desired_df["diner_url"]]
            desired_df = desired_df.iloc[:,1:]
            # st.dataframe(desired_df,unsafe_allow_html=True)
            # st.components.html(desired_df.to_html(escape=False), scrolling=True)
            st.markdown(desired_df.sort_values('real_review_cnt', ascending=False).to_html(render_links=True),unsafe_allow_html=True)
            

            # # 지도시각화
            # m = folium.Map(location=[y, x], zoom_start=15)
            # # Get the center coordinates
            # # now_center = m.get_center()
            
            
            # marker_cluster = MarkerCluster().add_to(m)
            # for diner_idx, cnt in result_lst.items():
            #     # print(diner_idx, cnt)
            #     try:
            #         personalAverageScoreRow = 1.2
            #         thisRestaurantScore = 2.0

            #             ## 쿼리문 대체
            #         bad_reviews = result_df_inner_join.query(
            #                                 f"(diner_idx == '{diner_idx}')" + 
            #                                 f" and (reviewer_avg >= {personalAverageScoreRow})" + 
            #                                 f" and (reviewer_review_score <= {thisRestaurantScore})"
            #                                 )
            #         if len(bad_reviews) > 3:
            #             print(len(bad_reviews))
            #         ## 쿼리문 대체
            #         detail = result_df_inner_join[result_df_inner_join['diner_idx'] == diner_idx].iloc[-1, :]
            

            #             ## 정리
            #         if type(detail["diner_review_tags"]) is not float:
            #             # detail_set = detail.drop_duplicates(subset = 'diner_name', keep='last')
            #             diner_tags = detail["diner_review_tags"].replace('@', ' ')
            #         color = 'darkblue'
            #         unlike = ''
            #         if len(bad_reviews) >= 5:
            #             color = 'gray'
            #             unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 개수 : {}".format(len(bad_reviews))

            #         if cnt >= people_counts:

            #             if detail["diner_menu"] is not None:
            #                 menu_tmp = detail["diner_menu"]
            #                 if menu_tmp.find('['):
            #                     menu_list = [" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('[','').replace('[','').split(', ') if len(i)]
            #                     menu = "\n".join(menu_list)
            #                 elif menu_tmp.find('->'):
            #                     menu_list =[" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('가격:', '').split('->')]
            #                     menu = "\n".join(menu_list)
            #                 elif len(menu_tmp):
            #                     menu = "".join(menu_tmp.replace('[','').replace('[','').split(', '))
            #                 else:
            #                     menu = "메뉴정보가 없는 음식점입니다."
            #             if len(menu) >= 120:
            #                 menu = menu[:120] 
            #             html = popup_html(detail,cnt, diner_tags, menu, unlike)
            #             # iframe = branca.element.IFrame(html=html,width=510,height=280)
            #             popup = folium.Popup(folium.Html(html, script=True), max_width=500)
                        
            #             # 마커 생성
            #             folium.Marker(
            #                 [detail["diner_lon"], detail["diner_lat"]],
            #                 popup=popup,
            #                 tooltip=name,
            #                 icon=folium.Icon(color=color, icon="cloud", prefix='fa')
            #                 ).add_to(marker_cluster)


                # except Exception as err:
                #     # st.write(err)
                #     continue

            # st_data = folium_static(m, width=wdt, height=hght)

@st.cache
def makingquery(diner_category, address_gu, df_diner):
    personalAverageScoreRow = 3.8

    # result_df = df_diner.query(f"(diner_category_middle == '{diner_category}')  and (diner_address_constituency == '{address_gu}') and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg <= {personalAverageScoreRow})")
    result_df = df_diner.query(f"(diner_category_middle == '{diner_category}')  and (diner_address_constituency in @address_gu) and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg <= {personalAverageScoreRow})")
    result_df_inner_join = pd.merge(df_review, result_df, on='diner_idx', how='inner')
    
    thisRestaurantScore = 4.0
    
    result_df_inner_join = result_df_inner_join.query(f"reviewer_review_score >= {thisRestaurantScore}")

    return result_df_inner_join

def findGu(address_str):
    default_ans = "마포구"
    if type(address_str) == str:
        gu_str = address_str.split(' ')[1]
        if gu_str[-1] == '구':
            return gu_str
        else:
            return default_ans
    else:
        return default_ans

df_diner = pd.read_excel('./whatToEat_DB_all.xlsx', sheet_name='diner', index_col=0)
df_review = pd.read_excel('./whatToEat_DB_all.xlsx', sheet_name='review', index_col=0)

# 소개창
if name == "About us":
    st.image(BannerImage)
    st.write("# Hello, What2Eat World")
    st.write("보유 음식점 수: {0}개 깐깐한 평가 수: {1}개".format(
            len(set(df_diner["diner_name"].to_list())), len(df_diner["diner_name"].to_list())
        ))
    

    st.write("## 0. 서비스 설명")
    st.write(
        "1. 음식점 평균 평점이 3.0 이상\n2. 리뷰어 개인 평균 평점이 3.8 이하지만 해당 음식점에는 4.0 이상으로 평가한 리뷰어\n"
    )
    st.write(
        "#### 1번 조건의 음식점 중에서 2번 조건의 리뷰어가 많은 음식점만이 지도에 표시됩니다. \n##### 단, 개인평균평점이 3.2 이상이지만 해당 음식점에 2.0 이하로 평가한 리뷰어가 3명을 초과한 음식점은 불호가 많은 음식점이라고 별도 표기해놓았습니다."
    )

    st.write("## 1. 사용방법")
    st.write(
        "0. 왼쪽 사이드에서 What2Eat으로 갑니다. \n1. 음식 카테고리는 숫자로 입력하시면 됩니다. \n2. 지역 검색은 행정구역 단위로 검색하시면 됩니다. 예를 들어, 망원동/ 영등포구 등등..")

    st.write(
        "## 2. 서비스 중인 지역 입니다. \n 2호선 위주로 차츰 늘려가겠습니다. 혹시 급하게 원하는 지역이 있다면 카톡 주세요.(ID: rockik)"
    )
    # st.write(region_lst)
    st.write("## 3. 카테고리 세부 목록입니다. 카테고리 선택시 참조하십시오.")
    st.write(cat)
    # st.write(
    #     '### 2. 크롤러_ 예를 들어 "부산 서면" 이라고 친다면 부산 서면 맛집 450개를 스크래핑하여 matki_DB 데이터에 추가됩니다! '
    # )

# 기능창
elif name == "What2Eat":
    st.image(BannerImage, width=350, use_column_width=True)
    
    # st.write("# 깐깐한 리뷰어들이 극찬한 음식점을 찾아줍니다. ")
    st.write("## 카테고리를 골라보세요.")
    # X_Point
    diner_category = st.radio(
    "",
    [category for category in list(set(df_diner['diner_category_middle'].to_list())) if category not in ['음식점']]
    )
    # Create a list of options
    constituency_options = list(set(df_diner['diner_address_constituency'].to_list()))

    # Create a multi-select radio button
    seleted_constituency = st.multiselect("찾을 지역을 고르세요.(복수선택)", constituency_options)
    print(seleted_constituency)
    # input_cat = st.text_input("카테고리를 설정해주세요(번호) : ", value="11")
    # size = st.radio(
    # "사이즈를 위해 사용 중인 디바이스 선택",
    # ('Phone', 'Web'))
    people_counts = 5
    # hate_counts = st.slider('불호 리뷰어 해당 명이상의 식당은 별도 표기합니다', 1, 20, 3)
    wdt = st.slider('화면 가로 크기', 320, 1536, 400)
    hght = st.slider('화면 세로 크기', 500, 2048, 700)



    if bool(diner_category):
        # 사용자 위도경도 생성
        # x, y, address_gu = geocode(region)
        longitude, latitude = 126.991290, 37.573341

        # address_gu = '중구'
        result_df_inner_join = makingquery(diner_category, seleted_constituency, df_diner)
        st.write()
        st.write("# {}(음식점, 깐깐한 리뷰어 수)".format(diner_category))

        if len(result_df_inner_join) > 3:
            main(result_df_inner_join, longitude, latitude, people_counts)
            people_counts = st.slider('깐깐한 리뷰어 몇 명이상의 식당만 표시할까요?', 1, 50, 4)
        else:
            st.write('### 아쉽지만 기준에 맞는 맛집이 없네요...')