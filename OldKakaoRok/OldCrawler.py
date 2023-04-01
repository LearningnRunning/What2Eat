import os
import re
from time import sleep
import requests
from geopy.geocoders import Nominatim
from auth import *

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from tqdm import tqdm
tqdm.pandas()
##############################################################  ############
##################### variable related geo ##########################
##########################################################################
def get_coordinates(address):
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None



def geocode(address, address_type="road"):
    address = " ".join(address.split(' ')[:4])
    apiurl = "http://api.vworld.kr/req/address?"
    params = {
        "service": "address",
        "request": "getcoord",
        "crs": "epsg:4326",
        "address": address,
        "format": "json",
        "type": address_type,
        "key": geocodeKey,#st.secrets["geocodeKey"],
    }
    
    try:
        response = requests.get(apiurl, params=params)

        json_data = response.json()

        if json_data["response"]["status"] == "OK":
            x = json_data["response"]["result"]["point"]["x"]
            y = json_data["response"]["result"]["point"]["y"]
            # print(json_data["response"]["refined"]["text"])
            # print("\n경도: ", x, "\n위도: ", y)
            return (x, y)
        else:
            params['type'] = 'parcel'
            response = requests.get(apiurl, params=params)

            json_data = response.json()
            x = json_data["response"]["result"]["point"]["x"]
            y = json_data["response"]["result"]["point"]["y"]
            # print(json_data["response"]["refined"]["text"])
            # print("\n경도: ", x, "\n위도: ", y)
            return (x, y)
        #     x,y = get_coordinates(address)
        #     print(address)
        #     print(location)
        #     return (x, y)
    except Exception as e:
        location = geolocator.geocode(address)
        print(location)
        if location:
            return (location.latitude, location.longitude)
        else:
            print('주소가 없네요.', address)
            return ("None", "None")

##############################################################  ############
##################### variable related selenium ##########################
##########################################################################
options = webdriver.ChromeOptions()
options.add_argument("lang=ko_KR")
options.add_argument("headless")
options.add_argument("window-size=1920x1080")
options.add_argument("disable-gpu")

# chromedriver_path = "/home/elinha/Testproject/mediapipe/chromedriver"
# 크롬 드라이버를 사용합니다 (맥은 첫 줄, 윈도우는 두번째 줄 실행)
driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
geolocator = Nominatim(user_agent="geoapiExercises")
matki_all = pd.read_csv("./result/matki_DB_raw.csv")


source_url = "https://map.kakao.com/"
# , "망원", "삼성", "삼성중앙", "선정릉", "신논현", "광흥창", "신촌", "양재", "역삼", "종로3가", "을지로3가", "영등포구청", "문래", "당산"
region = "마포구청"+"역"
# 합정, 망원, 삼성, 삼성중앙, 선정릉, 신논현, 당산, 홍대입구, 역삼역, 광흥창, 신촌
print(f'{region}을 시작합니다.')
# 크롬 드라이버를 사용합니다 (맥은 첫 줄, 윈도우는 두번째 줄 실행)


# 카카오 지도에 접속합니다
driver.get(source_url)
# 검색창에 검색어를 입력합니다
searchbox = driver.find_element(By.XPATH, "//input[@id='search.keyword.query']")
searchbox.send_keys("{0} 맛집".format(region))

# 검색버튼을 눌러서 결과를 가져옵니다
searchbutton = driver.find_element(By.XPATH, "//button[@id='search.keyword.submit']")
driver.execute_script("arguments[0].click();", searchbutton)

# 검색 결과를 가져올 시간을 기다립니다
sleep(2)

# 검색 결과의 페이지 소스를 가져옵니다
html = driver.page_source


driver.find_element(By.XPATH, "/html/body/div[10]/div/div/div/span").click()
sleep(2)
# 더보기 클릭
driver.find_element(By.XPATH, "//*[@id='info.search.place.more']").click()
sleep(2)
# 1~ 5페이지 링크 얻기
page_urls = []
cnt = 0
while driver.find_element(By.XPATH, '//a[@id="info.search.page.no5"]').is_displayed():
    for i in range(1, 6):
        page = driver.find_element(By.ID, "info.search.page.no" + str(i))
        page.click()
        sleep(2)
        urls = driver.find_elements(By.LINK_TEXT, "상세보기")
        for j in range(len(urls)):
            url = urls[j].get_attribute("href")
            print(url)
            page_urls.append(url)
    if (not bool(10 % 5)) & (
        not bool(driver.find_elements(By.XPATH, '//button[@class="next disabled"]'))
    ):
        driver.find_elements(By.XPATH, '//button[@id="info.search.page.next"]')[
            0
        ].click()


columns = [
    "region",
    "name",
    "addresse",
    "cat1",
    "cat2",
    "review_num",
    "blog_review_num",
    "open_time",
    "score_min",
    "likePoint",
    "likePointCnt",
    "rate",
    "reviewerCnt",
    "reviewAt",
    "review",
    "reviews_date",
    "reviewer_id"
]
# 사업장명, 주소, 음식종류1,음식종류2(메뉴),리뷰수,별점,리뷰
df = pd.DataFrame(columns=columns)

for i, page_url in enumerate(page_urls):
    print(f"{i}번째, {page_url}")
    # 상세보기 페이지에 접속합니다
    driver.get(page_url)
    wait = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'kakaoWrap')))
    sleep(3)


    if driver.find_elements(
        By.XPATH, '//div[@class="box_grade_off"]'
    ):  # 후기를 제공하지 않는 맛집 넘기기
        continue
    
    # 사업장명
    name = driver.find_element(By.XPATH, '//h2[@class="tit_location"]').get_attribute('innerText')

    # 사업장 주소
    address = driver.find_element(By.XPATH, '//span[@class="txt_address"]').get_attribute('innerText')

    # 평균 별점
    score_min = driver.find_element(
        By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/div/a[1]/span[1]'
    ).text

    # 리뷰수
    review_num = driver.find_element(By.XPATH, '//span[@class="color_g"]').text[1:-2]
    
    #영업시간
    open_times = driver.find_elements(By.XPATH, '//ul[@class="list_operation"]')
    if len(open_times):
        open_time = open_times[0].get_attribute('innerText').split('\n')[0]
    else:
        open_time = '제공하지 않음'
    # 블로그리뷰수
    blog_review_num = driver.find_element(
        By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/div/a[2]/span'
    ).text

    # 음식 종류
    cat1 = driver.find_element(
        By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/div/span[1]'
    ).text

    # 메뉴
    cat2 = []

    menus = driver.find_elements(By.CLASS_NAME, "info_menu")
    for menu in menus:
        cat2.append(menu.text)

    # 식당 장점
    likePoints = driver.find_elements(By.XPATH, '//*[@class="txt_likepoint"]')
    likePointCnts = driver.find_elements(By.XPATH, '//*[@class="num_likepoint"]')
    likePoint, likePointCnt = "", ""
    for p, c in zip(likePoints, likePointCnts):
        likePoint += p.text + "@"
        likePointCnt += c.text + "@"

    if driver.find_elements(By.XPATH, '//*[@id="mArticle"]/div[7]/div[3]/a/span[1]'):
        # 리뷰 더보기 최대로
        while not bool(
            driver.find_elements(By.XPATH, '//a[@class="link_more link_unfold"]')
        ):
            tmp_clk = driver.find_elements(By.XPATH, '//*[@class="txt_more"]')
            wait = WebDriverWait(driver, 1)
            element = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "link_more"))
            )
            try:
                if tmp_clk[0].text == "후기 더보기":
                    tmp_clk[0].click()
            except Exception as e:
                print("클릭 예외가 발생되었습니다.")
                pass

    try:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        contents_div = soup.find(name="div", attrs={"class": "evaluation_review"})

        # 별점을 가져옵니다.
        rateNcnt = contents_div.find_all(name="span", attrs={"class": "txt_desc"})
        rateCnts = rateNcnt[::2]
        rates = rateNcnt[1::2]

        # 개인이 해당 식당에 남긴 별점
        rateAts = driver.find_elements(
            By.XPATH, '//div[@class="grade_star size_s"]/span/span'
        )

        # 리뷰를 가져옵니다.
        reviews = contents_div.find_all(name="p", attrs={"class": "txt_comment"})

        # 리뷰를 쓴 날짜를 가져옵니다.
        reviews_dates = contents_div.find_all(
            name="span", attrs={"class": "time_write"}
        )

        # 리뷰 아이디 가져오기
        reviews_ids = contents_div.find_all(name="a", attrs={"class": "link_user"})
        print("rateAts", len(rateAts), "reviews", len(reviews))
        # 데이터프레임으로 정리합니다.
        for rate, rateCnt, rateAt, review, reviews_date, reviews_id in zip(
            rates, rateCnts, rateAts, reviews, reviews_dates, reviews_ids
        ):
            rateAt = int(rateAt.get_attribute("style")[7:-2]) / 20
            row = [
                region,
                name,
                address,
                cat1,
                cat2,
                review_num,
                blog_review_num,
                open_time,
                score_min,
                likePoint,
                likePointCnt,
                rate.text,
                rateCnt.text,
                rateAt,
                review.find(name="span").text,
                reviews_date.text,
                reviews_id.text,
            ]
            series = pd.DataFrame([row], columns=columns)
            series['url'] = page_url
            # series['url'] = url
            df = pd.concat([df, series])
    except Exception as e:
        print("예외가 발생되었습니다.", e)
df = df.drop_duplicates(subset=["review", "reviewer_id", "reviews_date"], keep="first")
driver.close()

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


def cat_change(string):
    for k, v in list(cat.items()):
        if string in v:
            string = k
    return string


df["cat1"] = df["cat1"].apply(cat_change)
df['lon'], df['lat'] = 'None', 'None'

# 임시
matki_all = pd.concat([matki_all,df])

tmp_df = matki_all[(matki_all['lon'] == 'None') | (matki_all['lat'] == 'None') ]
tmp_list = set(matki_all['addresse'].to_list())
address_dict = {i:geocode(i,'road') for i in tqdm(tmp_list)}

def samedict(address):
    if address_dict[address]:
        return address_dict[address][0],address_dict[address][1]
    else:
        return 'None', 'None'

matki_all['lon'], matki_all['lat'] = zip(*matki_all['addresse'].progress_apply(samedict))

# matki_all = pd.read_csv("./result/matki_DB_raw.csv")
# matki_all = pd.concat([matki_all,df])
matki_all.drop_duplicates(subset=['review', 'reviewer_id'], keep='last')
matki_all.to_csv(f"./result/matki_DB_raw_tmux_{region}.csv", index=False, encoding='utf-8-sig')  # index label을 따로 저장하지 않기


del matki_all['reviewer_id']
del matki_all['review']


matki_all.to_csv(f"./result/matki_DB_tmux_{region}.csv", index=False, encoding='utf-8-sig')  # index label을 따로 저장하지 않기
