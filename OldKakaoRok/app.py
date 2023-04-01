from collections import Counter

import folium
import pandas as pd
import requests
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium
import branca
from PIL import Image

BannerImage = Image.open('KakaoRok.png')

st.sidebar.header("KakaoRok")
name = st.sidebar.selectbox("menu", ["Welcome", "kakaoRok"])


def geocode(address):
    apiurl = "http://api.vworld.kr/req/address?"
    params = {
        "service": "address",
        "request": "getcoord",
        "crs": "epsg:4326",
        "address": address,
        "format": "json",
        "type": "parcel",
        "key": st.secrets["geocodeKey"],
    }

# from auth import *
# def geocode(address):
#     apiurl = "http://api.vworld.kr/req/address?"
#     params = {
#         "service": "address",
#         "request": "getcoord",
#         "crs": "epsg:4326",
#         "address": address,
#         "format": "json",
#         "type": "parcel",
#         "key": geocodeKey_1
#     }
    
    try:
        response = requests.get(apiurl, params=params)

        json_data = response.json()

        if json_data["response"]["status"] == "OK":
            x = json_data["response"]["result"]["point"]["x"]
            y = json_data["response"]["result"]["point"]["y"]
            print(json_data["response"]["refined"]["text"])
            print("\n경도: ", x, "\n위도: ", y)
            return x, y
    except Exception as e:
        print(e)
        pass

def popup_html(df,count, likepoint,menu, unlike):
    name=df['name']
    category1=df['cat1']
    address = df['addresse'] 
    review_num=df['review_num']
    if isinstance(review_num, (int,str)):
        review_num = int(review_num)
                    
    blog_review_num = df['blog_review_num']
    score_min = df['score_min']

    
    if type(df["url"]) == float:
        link = 'https://map.kakao.com/'
    else:
        link = df['url']

    if type(df["open_time"]) == float:
        open_time = '준비중'
    else:
        open_time = df["open_time"]        
        
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
    <table style="height: 126px; width: 350px;">
<tbody>


<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">업종</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(category1) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">평균 평점</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(score_min) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">평점수/ 블로그 리뷰수</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{0} 개/ {1}개</td>""".format(review_num, blog_review_num) + """
</tr>

<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">메뉴</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(menu) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">요약</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(likepoint) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">영업시간</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(open_time) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">주소</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(address) + """
</tr>

</tbody>
</table>
</html>
"""
    return html

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

# matki_DB 경로설정
tmp_df = pd.read_csv("./matki_DB.csv")

if name == "Welcome":
    st.image(BannerImage)
    st.write("# Hello, KakaoRok World")
    st.write("보유 음식점 수: {0}개 깐깐한 평가 수: {1}개".format(
            len(set(tmp_df["name"].to_list())), len(tmp_df["name"].to_list())
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
        "0. 왼쪽 사이드에서 kakaoRok으로 갑니다. \n1. 음식 카테고리는 숫자로 입력하시면 됩니다. \n2. 지역 검색은 행정구역 단위로 검색하시면 됩니다. 예를 들어, 망원동/ 영등포구 등등.."
    )
    columns = ["region"]
    tmp = pd.read_csv("./matki_DB.csv", usecols=columns)
    region_lst = list(dict.fromkeys(tmp["region"].to_list()))
    st.write(
        "## 2. 서비스 중인 지역 입니다. \n 2호선 위주로 차츰 늘려가겠습니다. 혹시 급하게 원하는 지역이 있다면 카톡 주세요.(ID: rockik)"
    )
    st.write(region_lst)
    st.write("## 3. 카테고리 세부 목록입니다. 카테고리 선택시 참조하십시오.")
    st.write(cat)
    # st.write(
    #     '### 2. 크롤러_ 예를 들어 "부산 서면" 이라고 친다면 부산 서면 맛집 450개를 스크래핑하여 matki_DB 데이터에 추가됩니다! '
    # )

elif name == "kakaoRok":

    st.write("# 깐깐한 리뷰어들이 극찬한 음식점을 찾아줍니다. ")

    st.write("## 카테고리를 골라보세요.")

    cat = st.radio(
    "",
    (
    "베이커리,카페",
    "패스트푸드",
    "샌드위치,샐러드",
    "육류",
    "해산물",
    "한식",
    "일식",
    "양식",
    "중식",
    "기타",
    "면류",
    "술집",
    "찌개,국밥"
    ))

    # input_cat = st.text_input("카테고리를 설정해주세요(번호) : ", value="11")
    region = st.text_input("검색할 지역을 입력해주세요(ex 영등포구 or 속초시)", value="서울특별시 중구")
    # size = st.radio(
    # "사이즈를 위해 사용 중인 디바이스 선택",
    # ('Phone', 'Web'))
    people_counts = st.slider('깐깐한 리뷰어 몇 명이상의 식당만 표시할까요?', 1, 50, 4)
    # hate_counts = st.slider('불호 리뷰어 해당 명이상의 식당은 별도 표기합니다', 1, 20, 3)
    wdt = st.slider('화면 가로 크기', 320, 1536, 400)
    hght = st.slider('화면 세로 크기', 500, 2048, 700)


    
        
    # btn_clicked = st.button("Confirm", key="confirm_btn")

    # if btn_clicked:
    #     con = st.container()
    #     con.caption("Result")
    #     if not str(input_cat):
    #         con.error("다시 입력해주세요.")
    #     else:
    #         con.write(region, input_cat)

    if bool(cat) and bool(region):
        x, y = geocode(region)

        RestaurantType = cat
        result_df = tmp_df[
            (tmp_df["cat1"] == RestaurantType) & (tmp_df["lon"].notnull()) & (tmp_df["lat"].notnull())
        ]
        st.write()
        st.write("# {}(음식점, 깐깐한 리뷰어 수)".format(RestaurantType))

        result_lst = Counter(result_df["name"].to_list()).most_common()

        m = folium.Map(location=[y, x], zoom_start=15)
        marker_cluster = MarkerCluster().add_to(m)
        for result in result_lst:
            try:
                personalAverageScoreRow = 3.2
                thisRestaurantScore = 2.0
                # print(result)
                row_df = result_df[
                    (result_df["name"] == result[0])
                    & (result_df["rate"] >= personalAverageScoreRow)
                    & (result_df["reviewAt"] <= thisRestaurantScore)
                ]

                detail = result_df[result_df["name"] == result[0]].iloc[-1, :]

                # print(detail)
                if type(detail["likePoint"]) != float:
                    likePoint = detail["likePoint"].split("@")
                    likePointCnt = detail["likePointCnt"].split("@")
                    likePointList = []
                    for l, c in zip(likePoint, likePointCnt):
                        tmp = l + ": " + c
                        likePointList.append(tmp)
                        likePoint_tmp = " ".join(likePointList)
                color = 'darkblue'
                unlike = ''
                if len(row_df) >= 5:
                    color = 'gray'
                    unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 개수 : {}".format(len(row_df))

                if result[1] >= people_counts:
    
                    if type(detail["cat2"]) != float:
                        menu_tmp = detail["cat2"]
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
                    html = popup_html(detail,result[1], likePoint_tmp, menu, unlike)
                    iframe = branca.element.IFrame(html=html,width=510,height=280)
                    popup = folium.Popup(folium.Html(html, script=True), max_width=500)
                    

                    folium.Marker(
                        [detail["lat"], detail["lon"]],
                        popup=popup,
                        tooltip=name,
                        icon=folium.Icon(color=color, icon="cloud", prefix='fa')
                        ).add_to(marker_cluster)


            except Exception as err:
                st.write(err)
                continue

        st_data = folium_static(m, width=wdt, height=hght)
