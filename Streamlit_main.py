# from collections import Counter

import folium
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


# 주소를 넣으면 위도, 경도 생성
def geocode(center):
    # longitude, latitude = 126.962101108891, 37.5512831039192
    # address_gu = "마포구"
    geolocator = Nominatim(user_agent="What2Eat")
    location = geolocator.geocode(address)
    if location:
        address_gu = location.address.split(", ")[1]
        print(address_gu)
        if address_gu[-1] != "구":
            address_gu = "마포구"
        latitude = location.latitude
        longitude = location.longitude
    # Reverse geocode the coordinates
    location = geolocator.reverse(center, exactly_one=True, language="ko")
    
    # Extract the address from the location object
    address = location.raw['address']

    # Extract the Korean address components
    korean_address = {
        'country': address.get('country', ''),
        'city': address.get('city', ''),
        'town': address.get('town', ''),
        'village': address.get('village', ''),
        'road': address.get('road', ''),
        'postcode': address.get('postcode', '')
    }

    # Extract the address from the location object
    # address = location.address
    print(korean_address)
        
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


<h5 style="margin-bottom:10"; width="80px"> {0}명의 솔직한 리뷰 {1}</h4>""".format(int(count), unlike) + """

</head>
    <table style="height: 126px; width: 150px;">
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



def main(df_diner, result_df_inner_join_bad, x, y, people_counts):

    
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
    
    
    marker_cluster = MarkerCluster().add_to(m)
    for diner_row_idx, diner_row in desired_df.iterrows():
        diner_idx = diner_row['diner_idx']
        # print(diner_idx, cnt)
        try:
            # personalAverageScoreRow = 1.2
            # thisRestaurantScore = 2.0

            #     ## 쿼리문 대체
            # bad_reviews = df_diner.query(
            #                         f"(diner_idx == '{diner_idx}')" + 
            #                         f" and (reviewer_avg >= {personalAverageScoreRow})" + 
            #                         f" and (reviewer_review_score <= {thisRestaurantScore})"
            #                         )
            # if len(bad_reviews) > 3:
            #     print(len(bad_reviews))
            
            ## 쿼리문 대체
            detail = result_df_inner_join[result_df_inner_join['diner_idx'] == diner_idx].iloc[-1, :]
    
            ## 정리
            if type(diner_row["diner_review_tags"]) is not float:
                # detail_set = detail.drop_duplicates(subset = 'diner_name', keep='last')
                diner_tags = diner_row["diner_review_tags"].replace('@', ' ')
                
            color = 'darkblue'
            unlike = ''
            
            # if len(bad_reviews) >= 5:
            #     color = 'gray'
            #     unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 개수 : {}".format(len(bad_reviews))



            if diner_row["diner_menu"] is not None:
                menu_tmp = diner_row["diner_menu"]
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
            html = popup_html(diner_row, diner_row['diner_review_cnt'], diner_tags, menu, unlike)
            # iframe = branca.element.IFrame(html=html,width=510,height=280)
            popup = folium.Popup(folium.Html(html, script=True), max_width=500)
            
            # 마커 생성
            folium.Marker(
                [diner_row["diner_lat"], diner_row["diner_lon"]],
                popup=popup,
                tooltip=name,
                icon=folium.Icon(color=color, icon="cloud", prefix='fa')
                ).add_to(marker_cluster)


        except Exception as err:
            # st.write(err)
            continue

    st_data = folium_static(m, width=700, height=500)

@st.cache_data
def makingquery(diner_category, df_diner):
    diner_review_avg = 3.5
    # Convert diner_review_avg to string for formatting
    diner_review_avg_str = str(diner_review_avg)
    # result_df = df_diner.query(f"(diner_category_middle == '{diner_category}')  and (diner_address_constituency == '{address_gu}') and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg <= {diner_review_avg})")
    # (diner_address_constituency in @address_gu)
    result_df = df_diner.query(f"(diner_category_middle in @diner_category) and (diner_lon != 0)  and (diner_lat != 0) and (diner_review_avg >= diner_review_avg)")
    result_df_inner_join = pd.merge(df_review, result_df, on='diner_idx', how='inner')
    
    personalAverageScoreRow = 3.8
    thisRestaurantScore = 4.0
    
    result_df_inner_join = result_df_inner_join.query(f"(reviewer_avg <= {personalAverageScoreRow}) and (reviewer_review_score >= {thisRestaurantScore})")

    
    personalAverageScoreRow = 4.0
    thisRestaurantScore = 1.5
    
    result_df_inner_join_bad = result_df_inner_join.query(f"(reviewer_avg >= {personalAverageScoreRow}) and (reviewer_review_score <= {thisRestaurantScore})")

    return result_df_inner_join, result_df_inner_join_bad

# def findGu(address_str):
#     default_ans = "마포구"
#     if type(address_str) == str:
#         gu_str = address_str.split(' ')[1]
#         if gu_str[-1] == '구':
#             return gu_str
#         else:
#             return default_ans
#     else:
#         return default_ans

@st.cache_data
def load_excel_data():
    # Load the Excel data and create the DataFrame
    # df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv', index_col=0)
    # df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv', index_col=0)
    df_diner = pd.read_csv('./seoul_data/whatToEat_DB_seoul_diner.csv')
    df_review = pd.read_csv('./seoul_data/whatToEat_DB_seoul_review.csv')
    df_diner['diner_category_detail'].fillna('', inplace=True)
    return df_diner, df_review

df_diner, df_review = load_excel_data()

columns_name = ['diner_name', 'diner_category_large', 'diner_category_middle', 'diner_category_small', 'diner_category_detail', 'diner_menu', 'diner_review_cnt', 'diner_review_avg', 'diner_review_tags', 'diner_address', 'diner_phone', 'diner_lat', 'diner_lon', 'diner_url', 'diner_open_time', 'diner_address_constituency', '']
df_diner.columns = columns_name
# Assuming df_diner is your DataFrame
df_diner.reset_index(inplace=True)  # Resetting index and making changes in-place
df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)  # Renaming the index column to diner_idx

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
    
    
    st.write("### 아래 버튼을 클릭해주세요, 주변 맛집을 찾아드릴게요")
    location = streamlit_geolocation()
    user_lat, user_lon = location['latitude'], location['longitude']
    longitude, latitude = 126.991290, 37.573341
    
    # Select radius distance
    radius_distance = st.selectbox("Select radius distance", ["300m", "500m", "1km", "3km"])

    # Convert radius distance to meters
    if radius_distance == "300m":
        radius_kilometers = 0.3
    elif radius_distance == "500m":
        radius_kilometers = 0.5
    elif radius_distance == "1km":
        radius_kilometers = 1
    elif radius_distance == "3km":
        radius_kilometers = 3
        
    if user_lat is not None or user_lon is not None:

        # Calculate distance for each diner and filter rows within 1km radius
        df_diner['distance'] = df_diner.apply(lambda row: haversine(user_lat, user_lon, row['diner_lat'], row['diner_lon']), axis=1)
        df_filtered = df_diner[df_diner['distance'] <= radius_kilometers]

        # st.dataframe(df_filtered)
        
    # st.write("##  다른 곳에서 당길 거면!")
    # # Create a list of options
    # # Filter out NaN values and convert float values to strings
    # constituency_options = sorted([str(constituency) for constituency in set(df_diner['diner_address_constituency'].dropna().to_list())])

    # # Create a multi-select radio button
    # seleted_constituency = st.multiselect("", constituency_options)
    
        st.write("##  오늘 뭐가 당겨?(복수가능)")
        
        # Filter out categories and convert float values to strings
        diner_category_lst = sorted([str(category) for category in set(df_filtered['diner_category_middle'].dropna().to_list()) if str(category) != '음식점'])

        diner_category = st.multiselect("", diner_category_lst)

        people_counts = 5


        # bool(seleted_constituency)
        
        if bool(diner_category):
            # 사용자 위도경도 생성
            # x, y, address_gu = geocode(region)
            

            # address_gu = '중구'
            result_df_inner_join, result_df_inner_join_bad = makingquery(diner_category, df_filtered)

            if len(result_df_inner_join) > people_counts:
                
                result_df_inner_join.dropna(subset=['diner_idx'], inplace=True)
                # result_df_inner_join = result_df_inner_join.reset_index(drop=False)
                # Calculate the row_counts
                row_counts = result_df_inner_join.groupby('diner_idx').size()

                # Filter the DataFrame based on the condition
                desired_df = df_diner[df_diner['diner_idx'].map(row_counts) > 3]
    
                # Assign the row_counts values to the 'real_review_cnt' column
                desired_df['real_review_cnt'] = desired_df['diner_idx'].map(row_counts)

                # Assuming your data is stored in a DataFrame called 'df'
                unique_categories = desired_df['diner_category_small'].unique().tolist()           
                # Create a multi-select radio button
                seleted_category = st.multiselect("안 당기는 건 빼!", unique_categories, default=unique_categories)
                desired_df = desired_df[desired_df['diner_category_small'].isin(seleted_category)]
                # Assuming your data is stored in a DataFrame called 'df'
                desired_df['combined_categories'] = desired_df['diner_category_small'] + ' / ' + desired_df['diner_category_detail']
                
                # desired_df = desired_df.loc[:,['real_review_cnt','diner_name','combined_categories','diner_url','diner_open_time', 'diner_address']]
                # st.dataframe(desired_df.sort_values('real_review_cnt', ascending=False))
                # st.components.html(desired_df.to_html(escape=False), scrolling=True)
                # st.markdown(desired_df.sort_values('real_review_cnt', ascending=False).to_html(render_links=True),unsafe_allow_html=True)
                
                main(desired_df, result_df_inner_join_bad, user_lon, user_lat, people_counts)
                # people_counts = st.slider('깐깐한 리뷰어 몇 명이상의 식당만 표시할까요?', 1, 50, 4)
            else:
                st.write('### 아쉽지만 기준에 맞는 맛집이 없네요...')