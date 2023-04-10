import requests
from bs4 import BeautifulSoup
import pandas as pd
from auth import *
import os
import re
from time import sleep
import requests

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

options = webdriver.ChromeOptions()
options.add_argument("lang=ko_KR")
options.add_argument("headless")
options.add_argument("window-size=1920x1080")
options.add_argument("disable-gpu")



def KakaoMapAPI(regions):
    # Create an empty DataFrame to store all the restaurant information
    all_df = pd.DataFrame()
    
    # Iterate over each region and search for restaurants using the Kakao Map API
    for region in regions:
        # Set the API endpoint URL
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        
        # Set the headers for the API request
        headers = {"Authorization": f"KakaoAK {REST_API_KEY}"}
        
        # Set the search parameters, including the radius of the search (20km), the category of the search (food), 
        # and the search query (the region name followed by "restaurant" in Korean)
        params = {
            "radius" : "20000",
            "category_group_code" : "FD6",
            "query": f"{region} 맛집"
        }
        
        # Iterate over each page of search results (up to 45 pages) and append the restaurant information to the DataFrame
        for i in range(1,46):
            # Set the page parameter for the search request
            params['page'] = str(i)
            
            # Send the search request and get the response as JSON
            response = requests.get(url, headers=headers, params=params)
            tmp_json = response.json()['documents']
            
            # Convert the JSON to a DataFrame and append it to the main DataFrame
            df = pd.DataFrame(tmp_json)
            all_df = pd.concat([all_df, df])
    
    # Rename the DataFrame columns to be more descriptive
    all_df = all_df.rename(columns={
        'x': 'diner_lat',
        'y' : 'diner_lon',
        'road_address_name': 'diner_address',
        'place_name' : 'diner_name',
        'category_name' : 'diner_category',
        'phone' : 'diner_phone',
        'id' : 'diner_id'
    })
    all_df.drop_duplicates(subset=['place_url'], keep='last',inplace=True)
    # Return the final DataFrame with all the restaurant information
    return all_df

def KakaoMapCreawler(urls_df):
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    diner_cols = [
        'diner_id',
        'diner_name',           # 가게이름 
        'diner_category',       # 가게 카테고리
        'diner_menu',           # 가게 메뉴
        'diner_review_cnt',     # 가게의 평점 개수 
        'diner_review_avg',     # 가게의 평점 평균
        'diner_review_tags',    # 리뷰 태그
        'diner_address',        # 가게 주소    
        'diner_phone',        # 가게 주소    
        'diner_lon',            # 가게 위도
        'diner_lat',            # 가게 경도
        'diner_url',            # 가게 URL
        'diner_open_time'       # 가게 오픈시간
       ]

    review_cols = [
            'diner_id',
            'reviewer_review',
            'reviewer_avg',         # 리뷰어의 평점 평균
            'reviewer_review_cnt',  # 리뷰어의 리뷰 개수
            'reviewer_review_score',# 리뷰어가 남긴 평점
            'reviewer_review_date', # 리뷰를 남긴 날짜
            'reviewer_id'
            ]
    # 사업장명, 주소, 음식종류1,음식종류2(메뉴),리뷰수,별점,리뷰
    dinner_df = pd.read_excel('./diner_only.xlsx', sheet_name='diner', index_col = 0)
    review_df = pd.read_excel('./diner_only.xlsx', sheet_name='review', index_col = 0)

    for i in range(len(urls_df)):
        dinner_id = urls_df.iloc[i,5]
        page_url = urls_df.iloc[i,8]
        cat1 = urls_df.iloc[i,3]
        address = urls_df.iloc[i,9]
        name  = urls_df.iloc[i,7]
        diner_phone = urls_df.iloc[i,6]
        diner_lat = urls_df.iloc[i,10]
        diner_lon = urls_df.iloc[i,11]
        print(f"{dinner_id}: {page_url}")
        # 상세보기 페이지에 접속합니다
        driver.get(page_url)
        wait = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'kakaoWrap')))
        sleep(3)


        if driver.find_elements(
            By.XPATH, '//div[@class="box_grade_off"]'
        ):  # 후기를 제공하지 않는 맛집 넘기기
            continue
        
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

        # # 블로그리뷰수
        # blog_review_num = driver.find_element(
        #     By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/div/a[2]/span'
        # ).text


        # 메뉴
        cat2 = []

        menus = driver.find_elements(By.CLASS_NAME, "info_menu")
        for menu in menus:
            cat2.append(menu.text)

        # 식당 장점
        likePoints = driver.find_elements(By.XPATH, '//*[@class="txt_likepoint"]')
        likePointCnts = driver.find_elements(By.XPATH, '//*[@class="num_likepoint"]')
        likePoint = ""
        for p, c in zip(likePoints, likePointCnts):
            likePoint += p.text + "@" + c.text + "@"

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

            dinner_row = [
                    dinner_id,
                    name,
                    cat1,
                    cat2,
                    review_num,
                    score_min,
                    likePoint,
                    address,
                    diner_phone,
                    diner_lon,
                    diner_lat,
                    page_url,
                    open_time,
                ]
            series = pd.DataFrame([dinner_row], columns=diner_cols)
            dinner_df = pd.concat([dinner_df, series])
            
            rateAts = [int(rateAt.get_attribute("style")[7:-2]) / 20 for rateAt in rateAts]
            # Create a dictionary with the data
            review_data = {
                    'dinner_id': dinner_id,
                    'reviewer_review': reviews,
                    'reviewer_avg': rates,
                    'reviewer_review_cnt': rateCnts,
                    'reviewer_review_score': rateAts,
                    'reviewer_review_date': reviews_dates,
                    'reviewer_id': reviews_ids,
                    }
            review_df_tmp = pd.DataFrame([review_data], columns=review_cols)
            review_df = pd.concat([review_df, review_df_tmp])
        except Exception as e:
            print("예외가 발생되었습니다.", e)
    review_df.drop_duplicates(subset=['reviewer_id','reviewer_review','reviewer_review_cnt','reviewer_review_score','reviewer_review_date'], keep='last',inplace=True)

    # create an Excel writer object
    writer = pd.ExcelWriter('./diner_only.xlsx', engine='xlsxwriter')

    # write each dataframe to a separate sheet in the Excel file
    dinner_df.to_excel(writer, sheet_name='dinner', index=False)
    review_df.to_excel(writer, sheet_name='review', index=False)
    return dinner_df, review_df
