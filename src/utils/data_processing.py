import math
import folium
from folium.plugins import MarkerCluster
from math import radians, sin, cos, sqrt, atan2
import streamlit as st

def generate_introduction(diner_name, diner_url, diner_bad_percent, radius_kilometers, distance, diner_category_small, real_review_cnt, diner_good_percent):
    introduction = f"[{diner_name}]({diner_url})"
    if diner_bad_percent is not None and diner_bad_percent > 10:
        introduction += f"\n불호(비추)리뷰 비율이 {round(diner_bad_percent, 2)}%나 돼!"
        if radius_kilometers >= 0.5:
            introduction += f"\n{distance}M \n\n"
        else:
            introduction += "\n\n"
    else:
        if diner_name:
            introduction += f" ({diner_category_small})\n"
        else:
            introduction += "\n"
                            
        introduction += f"쩝쩝박사 {real_review_cnt}명 인증 \n 쩝쩝 퍼센트: {round(diner_good_percent,2)}%"
                            
        if radius_kilometers >= 0.5:
            introduction += f"\n{distance}M \n\n"
        else:
            introduction += "\n\n"
    
    return introduction

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c

    return distance

@st.cache_data
def category_filters(diner_category, df_diner_real_review, df_diner):
    category_filted_df = df_diner_real_review.query(f"diner_category_middle in @diner_category")
    diner_nearby_cnt = len(df_diner.query(f"diner_category_middle in @diner_category"))
    
    return category_filted_df, diner_nearby_cnt

def make_map(desired_df, x, y):
    # 지도시각화
    m = folium.Map(location=[y, x], zoom_start=15)
    # Get the center coordinates
    # now_center = m.get_center()

    folium.CircleMarker(location=[y, x],
        radius=7, color='blue', fill_color='#147DF5').add_to(m)
    
    marker_cluster = MarkerCluster().add_to(m)

    for diner_row_idx, diner_row in desired_df.iterrows():
        diner_name = diner_row['diner_name']
        diner_bad_percent = diner_row['real_bad_review_percent']
        diner_review_tags = diner_row["diner_review_tags"]
        diner_menu = diner_row["diner_menu"]


    
        ## 정리
        if type(diner_review_tags) is not float:
            diner_tags = diner_review_tags.replace('@', ' ')
            
        color = 'darkblue'
        unlike = ''
        
        if diner_bad_percent > 10:
            color = 'gray'
            unlike = "</br> 다만, 불호가 너무 많은 식당입니다. 불호 퍼센트 : {}".format(round(diner_bad_percent, 2))

        # if diner_menu is not None:
        #     menu_tmp = diner_menu
        #     if menu_tmp.find('['):
        #         menu_list = [" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('[','').replace('[','').split(', ') if len(i)]
        #         menu = "\n".join(menu_list)
        #     elif menu_tmp.find('->'):
        #         menu_list =[" ".join(i.split("\n")[:2]) for i in menu_tmp.replace('가격:', '').split('->')]
        #         menu = "\n".join(menu_list)
        #     elif len(menu_tmp):
        #         menu = "".join(menu_tmp.replace('[','').replace('[','').split(', '))
        #     else:
        #         menu = "메뉴정보가 없는 음식점입니다."
                
        # if len(menu) >= 120:
        #     menu = menu[:120] 
        html = popup_html(diner_row, diner_tags, unlike)
        # iframe = branca.element.IFrame(html=html,width=510,height=280)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)
        
        # 마커 생성
        folium.Marker(
            [diner_row["diner_lat"], diner_row["diner_lon"]],
            popup=popup,
            tooltip=diner_name,
            icon=folium.Icon(color=color, icon="cutlery", prefix='fa')
            ).add_to(marker_cluster)

    return m

def popup_html(diner_row, linke_tags, unlike):
    diner_name = diner_row['diner_name']
    diner_category_small = diner_row['diner_category_small']
    diner_url = diner_row['diner_url']
    diner_open_time = diner_row["diner_open_time"]
    real_review_cnt = int(diner_row['real_good_review_cnt'])
    distance = int(diner_row['distance']*1000)
    diner_good_percent = diner_row['real_good_review_percent']

    
    if type(diner_url) == float:
        link = 'https://map.kakao.com/'
    else:
        link = diner_url

    if type(diner_open_time) == float:
        open_time = '준비중'
    else:
        open_time = diner_open_time        
        
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
                        <h4 width="200px" >{0}</h4>""".format(diner_name) + """
                    </p>
                </div>


                <h5 style="margin-bottom:10"; width="80px"> 찐만족도: {0}% \n 찐만족 리뷰 수: {1}개  {2}</h4>""".format(diner_good_percent, real_review_cnt, unlike) + """

                </head>
                    <table style="height: 126px; width: 150px;">
                <tbody>


                <tr>
                <td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">업종</span></td>
                <td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(diner_category_small) + """
                </tr>
                <tr>
                <td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">요약</span></td>
                <td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(linke_tags) + """
                </tr>
                <tr>
                <td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">영업시간</span></td>
                <td style="width: 100px;background-color: """+ right_col_color +""";">{}</td>""".format(open_time) + """
                </tr>
                <tr>
                <td style="width: 30px;background-color: """+ left_col_color +""";"><span style="color: #ffffff;">거리</span></td>
                <td style="width: 100px;background-color: """+ right_col_color +""";">{} M</td>""".format(distance) + """
                </tr>

                </tbody>
                </table>
                </html>
                """
    return html