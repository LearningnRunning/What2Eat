# from collections import Counter
import streamlit as st
from streamlit_folium import folium_static
from streamlit_geolocation import streamlit_geolocation
from awesome_package.module import (make_map, generate_user_agent, haversine,
                                    geocode, load_excel_data, category_filters,
                                    popup_html)

from PIL import Image
import ast
def make_clickable_url(df):
    name = df['diner_name']
    url = df['diner_url']
    return f'<a target="_blank" href="{url}">{name}</a>'


BannerImage = Image.open('./img_data/what2eat-logo.png')

st.sidebar.header("오늘 뭐 먹?")
name = st.sidebar.radio("Menu", ["What2Eat", "About us"])

# # Function to print map center coordinates
# def print_map_center(event):
#     print("Map center coordinates:", m.location)
    
df_diner = load_excel_data()
df_diner.rename(columns={'index': 'diner_idx'}, inplace=True)  # Renaming the index column to diner_idx

# 소개창
if name == "About us":
    st.image(BannerImage)
    st.write("# Hello, What2Eat World")

    all_review_total_sum = int(df_diner['all_review_cnt'].dropna().sum())
    real_review_total_sum = int(df_diner['real_good_review_cnt'].dropna().sum())
    
    df_diner_real_review = df_diner[df_diner['real_good_review_cnt'].notna()]
    st.write("보유 음식점 수: {0}개, \n 분석한 리뷰 수: {1}개".format(
            len(df_diner), all_review_total_sum
        ))
    st.write("인증된 음식점 수: {0}개, \n 깐깐한 리뷰 수: {1}개".format(
            len(df_diner_real_review), real_review_total_sum
        ))
    
    link_url = "## [What2Eat 로직설명](https://learningnrunning.github.io/example/tech/review/2024-03-03-from-kakaoRok-to-What2Eat/)"
    st.write(
        link_url
    )
    
# 기능창
elif name == "What2Eat":
    st.image(BannerImage, width=350, use_column_width=True)
    
    st.write("### 아래 버튼을 클릭해주세요, 주변 맛집을 찾아드릴게요")
    location = streamlit_geolocation()
    user_lat, user_lon = location['latitude'], location['longitude']
    user_address = geocode(user_lon, user_lat)
    st.write(user_address)
    # longitude, latitude = 126.991290, 37.573341
    
    people_counts = 5
        
    if user_lat is not None or user_lon is not None:
        # Select radius distance
        radius_distance = "km" # st.selectbox("", ["300m", "500m", "1km", "3km", "10km"])

        # Convert radius distance to meters
        if radius_distance == "300m":
            radius_kilometers = 0.3
        elif radius_distance == "500m":
            radius_kilometers = 0.5
        elif radius_distance == "1km":
            radius_kilometers = 1
        elif radius_distance == "3km":
            radius_kilometers = 3
        elif radius_distance == "10km":
            radius_kilometers = 10
        
        radius_kilometers = 50
        # Calculate distance for each diner and filter rows within 1km radius
        df_diner['distance'] = df_diner.apply(lambda row: haversine(user_lat, user_lon, row['diner_lat'], row['diner_lon']), axis=1)
        df_geo_filtered = df_diner[df_diner['distance'] <= radius_kilometers]


    # seleted_constituency = st.multiselect("", constituency_options)
        if len(df_geo_filtered):
                
            st.write("##  오늘 뭐가 당겨요?(복수가능)")
            
            df_geo_filtered = df_geo_filtered[df_geo_filtered['real_good_review_cnt'].notna()]

            df_geo_filtered_real_review = df_geo_filtered.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

            diner_category_lst = sorted([str(category) for category in set(df_geo_filtered_real_review['diner_category_middle'].dropna().to_list()) if str(category) != '음식점'])

            diner_category = st.multiselect("", diner_category_lst)

            if bool(diner_category):
                df_geo_mid_catecory_filtered, diner_nearby_cnt = category_filters(diner_category, df_geo_filtered_real_review, df_geo_filtered)
                
                if len(df_geo_mid_catecory_filtered):
                
                    st.write("세부 업종에서 안 당기는 건 빼주세요!")
                    # Assuming your data is stored in a DataFrame called 'df'
                    unique_categories = df_geo_mid_catecory_filtered['diner_category_small'].unique().tolist()   
                    
                    # Create a multi-select radio button
                    seleted_category = st.multiselect("세부 카테고리", unique_categories, default=unique_categories)
                    df_geo_small_catecory_filtered = df_geo_mid_catecory_filtered[df_geo_mid_catecory_filtered['diner_category_small'].isin(seleted_category)].sort_values(by='distance', ascending=True)
                    
                    if not len(df_geo_small_catecory_filtered):
                        st.write("헉.. 주변에 찐맛집이 없대요.. \n 다른 메뉴를 골라봐요")
                    elif seleted_category:
                        # st.dataframe(df_geo_small_catecory_filtered)
                        result_map = make_map(df_geo_small_catecory_filtered, user_lon, user_lat)
                        st_data = folium_static(result_map, width=700, height=500)

                        # df_geo_small_catecory_filtered['diner_clickable_url'] = df_geo_small_catecory_filtered.apply(make_clickable_url,  axis=1)
                        # st.dataframe(df_geo_small_catecory_filtered)
                        df_geo_small_catecory_filtered = df_geo_small_catecory_filtered[['distance', 'real_good_review_percent', 'real_good_review_cnt','diner_name', 'diner_url', 'diner_phone', 'diner_category_small', 'diner_menu']]

                        
                        st.data_editor(
                            df_geo_small_catecory_filtered,
                            column_config = {
                                'diner_url' : st.column_config.LinkColumn(
                                    '카카오맵',
                                    validate="^http://place.map.kakao.com/",
                                    display_text='바로가기',
                                    width = 'small'
                                ),
                                'distance' : st.column_config.NumberColumn(
                                    '도달 거리',
                                    default = 'float',
                                    format='%.1f Km'
                                ),
                                'real_good_review_percent' : st.column_config.NumberColumn(
                                    '인증 %',
                                    default = 'float',
                                    format = '%.1f'
                                ),
                                'real_good_review_cnt' : st.column_config.NumberColumn(
                                    '인증 리뷰 수',
                                    default = 'int',
                                    format = '%d 개',
                                    width= 'small'
                                ),
                                'diner_name' : st.column_config.TextColumn(
                                    '상호명'
                                ),
                                'diner_menu' : st.column_config.ListColumn(
                                    '메뉴',
                                    width= 'medium'
                                ),
                                'diner_category_small' : st.column_config.TextColumn(
                                    '업종',
                                ),
                                'diner_phone' : st.column_config.LinkColumn(
                                    '번호'
                                )
                            }
                        )
                        # st.markdown(df_geo_small_catecory_filtered.to_html(render_links=True),unsafe_allow_html=True)
                        # st.dataframe(df_geo_small_catecory_filtered.style.format({'nameurl': make_clickable_both}))
                        
                        # result_map.on_move(print_map_center)
                        # new_location = result_map.location
                        # new_lat, new_lon = new_location[0], new_location[1]

                        # if [user_lat, user_lon] == new_location:
                        #     st_data = folium_static(result_map, width=700, height=500)
                        # else:
                        #     print(new_location)
                        #     st_folium(result_map, width=700, height=500)
